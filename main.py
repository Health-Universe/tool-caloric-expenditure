from fastapi import FastAPI, Form
from pydantic import BaseModel
from enum import Enum
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import random


class BiologicalSexEnum(str, Enum):
    male = "male"
    female = "female"


class ActivityLevelEnum(str, Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"
    extra_active = "extra_active"


class PredictiveData(BaseModel):
    bmr: float
    daily_caloric_needs: float
    recommendations: str


class TimeSeriesDataPoint(BaseModel):
    week: int
    weight: float


class TimeSeriesPredictiveData(BaseModel):
    initial_weight: float
    predicted_weight: List[TimeSeriesDataPoint]
    recommendations: str


app = FastAPI(
    title="Caloric Expenditure API",
    description="API for calculating Basal Metabolic Rate (BMR) and Daily Caloric Needs based on user inputs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/predict", response_model=PredictiveData, summary="Calculate BMR and Daily Caloric Needs")
async def predict_calories(
        age: int = Form(..., gt=0, description="Age of the user in years"),
        biological_sex: BiologicalSexEnum = Form(..., description="Biological sex of the user"),
        weight: float = Form(..., gt=0, description="Weight of the user in kilograms"),
        height: float = Form(..., gt=0, description="Height of the user in centimeters"),
        activity_level: ActivityLevelEnum = Form(..., description="User's activity level")
):
    """
    Calculate Basal Metabolic Rate (BMR) and Daily Caloric Needs based on user input.
    """
    # Mifflin-St Jeor Equation for BMR
    if biological_sex == BiologicalSexEnum.male:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_multipliers = {
        ActivityLevelEnum.sedentary: 1.2,
        ActivityLevelEnum.lightly_active: 1.375,
        ActivityLevelEnum.moderately_active: 1.55,
        ActivityLevelEnum.very_active: 1.725,
        ActivityLevelEnum.extra_active: 1.9,
    }

    multiplier = activity_multipliers.get(activity_level, 1.2)
    daily_caloric_needs = bmr * multiplier

    if daily_caloric_needs < 1500:
        recommendations = "Your daily caloric needs are relatively low. Ensure you're getting enough nutrients."
    elif 1500 <= daily_caloric_needs <= 2500:
        recommendations = "Your daily caloric needs are within the average range. Maintain a balanced diet."
    else:
        recommendations = "Your daily caloric needs are high. Consider consulting a nutritionist for personalized advice."

    return PredictiveData(
        bmr=round(bmr, 2),
        daily_caloric_needs=round(daily_caloric_needs, 2),
        recommendations=recommendations
    )


@app.post("/predict-time-series", response_model=TimeSeriesPredictiveData, summary="Predict Weight Over Time")
async def predict_time_series(
        initial_weight: float = Form(..., gt=0, description="Initial weight of the user in kilograms"),
        weight_change_per_week: float = Form(..., description="Projected weight change per week in kilograms")
):
    """
    Predict weight progression over a 12-week period based on user inputs.
    """
    predicted_weight = []
    current_weight = initial_weight

    for week in range(1, 13):
        variation = random.uniform(-0.1, 0.1)
        current_weight -= weight_change_per_week
        current_weight = round(current_weight + variation, 2)
        predicted_weight.append(TimeSeriesDataPoint(week=week, weight=current_weight))

    total_weight_change = weight_change_per_week * 12
    if total_weight_change > 10:
        recommendations = "Your projected weight loss is significant. Consider consulting a healthcare professional."
    elif 5 <= total_weight_change <= 10:
        recommendations = "Your projected weight loss is healthy. Maintain your current plan."
    else:
        recommendations = "Your projected weight loss is minimal. You might want to adjust your caloric intake or activity level."

    return TimeSeriesPredictiveData(
        initial_weight=initial_weight,
        predicted_weight=predicted_weight,
        recommendations=recommendations
    )
