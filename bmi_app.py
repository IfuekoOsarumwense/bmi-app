from __future__ import annotations

import os
from math import isfinite

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field, field_validator

app = FastAPI(
    title="BMI Calculator API",
    description="Calculate BMI and categorize the result based on standard health ranges.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class BMIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weight_kg: float = Field(..., gt=0, le=500, description="Weight in kilograms.")
    height_cm: float = Field(..., gt=0, le=300, description="Height in centimeters.")

    @field_validator("weight_kg", "height_cm")
    @classmethod
    def validate_measurements(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("Measurement must be a finite number.")
        return value


class BMIResponse(BaseModel):
    bmi: float
    category: str
    weight_kg: float
    height_cm: float


def get_bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obesity"


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "bmi-calculator",
    }


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.post("/api/v1/bmi", response_model=BMIResponse, status_code=status.HTTP_200_OK)
async def calculate_bmi_endpoint(payload: BMIRequest) -> BMIResponse:
    bmi = calculate_bmi(payload.weight_kg, payload.height_cm)
    return BMIResponse(
        bmi=bmi,
        category=get_bmi_category(bmi),
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("bmi_app:app", host="0.0.0.0", port=port, reload=False)
