from typing import Annotated, Literal, List

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import random

app = FastAPI(
    title="Caloric Expenditure Tool",
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


class PredictiveDataInput(BaseModel):
    """
    Form-based input schema for calculating Basal Metabolic Rate (BMR) and Daily Caloric Needs.
    """

    unit_system: Literal["metric", "imperial"] = Field(
        default="metric",
        title="Unit System",
        examples=["metric"],
        description="Select your measurement system.",
    )
    age: int = Field(
        title="Age",
        ge=1,
        le=150,
        examples=[30],
        description="Enter your age in years. Must be a value between 1 and 150.",
    )
    weight: float = Field(
        title="Weight",
        ge=1.0,
        examples=[70.0],
        description="Enter your weight in kilograms (metric) or pounds (imperial). Must be a positive value.",
    )
    height: float = Field(
        title="Height",
        ge=1.0,
        examples=[175.0],
        description="Enter your height in centimeters (metric) or inches (imperial). Must be a positive value.",
    )
    biological_sex: Literal["male", "female"] = Field(
        title="Biological Sex",
        examples=["male"],
        description="Select your biological sex.",
    )
    activity_level: Literal[
        "sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"
    ] = Field(
        title="Activity Level",
        examples=["moderately_active"],
        description=(
            "Select your activity level.\n\n"
            "- **Sedentary**: Little to no exercise\n"
            "- **Lightly Active**: Light exercise (1-3 days per week)\n"
            "- **Moderately Active**: Moderate exercise (3–5 days per week)\n"
            "- **Very Active**: Heavy exercise (6–7 days per week)\n"
            "- **Extra Active**: Very heavy exercise (twice per day, extra heavy workouts)"
        ),
    )


class PredictiveData(BaseModel):
    """
    Form-based output schema for BMR and Daily Caloric Needs.
    """

    bmr: float = Field(
        title="Basal Metabolic Rate (BMR) in kcal/day",
        examples=[1984.0],
        description="Your calculated Basal Metabolic Rate (BMR) in kilocalories per day.",
    )
    daily_caloric_needs: float = Field(
        title="Daily Caloric Needs in kcal/day",
        examples=[2380.0],
        description="Your calculated Daily Caloric Needs based on your activity level, in kilocalories per day.",
    )
    recommendations: str = Field(
        title="Recommendations",
        examples=["Your daily caloric needs are within the average range. Maintain a balanced diet."],
        description="Personalized recommendations based on your daily caloric needs.",
    )


@app.post("/predict", response_model=PredictiveData, summary="Calculate BMR and Daily Caloric Needs")
def predict_calories(
        data: Annotated[PredictiveDataInput, Form()],
):
    """
    Calculate Basal Metabolic Rate (BMR) and Daily Caloric Needs based on user input.
    """
    # Unit conversion factors
    conversion_factors = {
        "metric": {"weight": 1.0, "height": 1.0},
        "imperial": {"weight": 0.453592, "height": 2.54},
    }

    unit = data.unit_system.lower()
    if unit not in conversion_factors:
        raise HTTPException(
            status_code=400,
            detail="Invalid unit system. Must be 'metric' or 'imperial'.",
        )

    factors = conversion_factors[unit]
    weight_in_kg = data.weight * factors["weight"]
    height_in_cm = data.height * factors["height"]

    # Original Harris-Benedict Equation for BMR
    if data.biological_sex == "male":
        bmr = (
            66.473
            + (13.7516 * weight_in_kg)
            + (5.0033 * height_in_cm)
            - (6.7550 * data.age)
        )
    else:
        bmr = (
            655.0955
            + (9.5634 * weight_in_kg)
            + (1.8496 * height_in_cm)
            - (4.6756 * data.age)
        )

    activity_multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9,
    }

    multiplier = activity_multipliers.get(data.activity_level, 1.2)
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


class TimeSeriesPredictiveDataInput(BaseModel):
    """
    Form-based input schema for predicting weight over time.
    """

    unit_system: Literal["metric", "imperial"] = Field(
        default="metric",
        title="Unit System",
        examples=["metric"],
        description="Select your measurement system.",
    )
    initial_weight: float = Field(
        title="Initial Weight",
        ge=1.0,
        examples=[70.0],
        description="Enter your initial weight in kilograms (metric) or pounds (imperial). Must be a positive value.",
    )
    weight_change_per_week: float = Field(
        title="Weight Change per Week",
        examples=[0.5],
        description="Projected weight change per week in kilograms (metric) or pounds (imperial).",
    )


class TimeSeriesDataPoint(BaseModel):
    """
    Data point representing weight at a specific week.
    """
    week: int = Field(
        title="Week",
        examples=[1],
        description="Week number.",
    )
    weight: float = Field(
        title="Weight",
        examples=[69.5],
        description="Predicted weight in kilograms or pounds at the given week.",
    )


class TimeSeriesPredictiveData(BaseModel):
    """
    Form-based output schema for predicted weight over time.
    """

    predicted_weight: List[TimeSeriesDataPoint] = Field(
        title="Predicted Weight Over Time",
        description="List of predicted weights over the 12-week period.",
    )
    recommendations: str = Field(
        title="Recommendations",
        examples=["Your projected weight loss is healthy. Maintain your current plan."],
        description="Personalized recommendations based on your projected weight change.",
    )


@app.post(
    "/predict-time-series",
    response_model=TimeSeriesPredictiveData,
    summary="Predict Weight Over Time",
    openapi_extra={"x-chart-type": "line_chart"}
)
def predict_time_series(
        data: Annotated[TimeSeriesPredictiveDataInput, Form()],
):
    """
    Predict weight progression over a 12-week period based on user inputs.
    """
    # Unit conversion factors
    conversion_factors = {
        "metric": {"weight": 1.0},
        "imperial": {"weight": 0.453592},
    }

    unit = data.unit_system.lower()
    if unit not in conversion_factors:
        raise HTTPException(
            status_code=400,
            detail="Invalid unit system. Must be 'metric' or 'imperial'.",
        )

    factor = conversion_factors[unit]["weight"]
    initial_weight_kg = data.initial_weight * factor
    weight_change_per_week_kg = data.weight_change_per_week * factor

    # Start with initial weight as the first data point (week=0)
    predicted_weight = [TimeSeriesDataPoint(week=0, weight=data.initial_weight)]
    current_weight = initial_weight_kg

    for week in range(1, 13):
        variation = random.uniform(-0.1, 0.1)
        current_weight -= weight_change_per_week_kg
        current_weight = round(current_weight + variation, 2)
        # Convert back to original unit system for output
        current_weight_output = current_weight / factor
        predicted_weight.append(TimeSeriesDataPoint(week=week, weight=round(current_weight_output, 2)))

    total_weight_change = data.weight_change_per_week * 12
    if total_weight_change > 10:
        recommendations = "Your projected weight loss is significant. Consider consulting a healthcare professional."
    elif 5 <= total_weight_change <= 10:
        recommendations = "Your projected weight loss is healthy. Maintain your current plan."
    else:
        recommendations = "Your projected weight loss is minimal. You might want to adjust your caloric intake or activity level."

    return TimeSeriesPredictiveData(
        predicted_weight=predicted_weight,
        recommendations=recommendations
    )
