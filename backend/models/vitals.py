from pydantic import BaseModel, Field
from typing import Optional


class VitalsInput(BaseModel):
    systolic_bp: int = Field(..., ge=60, le=250, description="Systolic blood pressure (mmHg)")
    diastolic_bp: int = Field(..., ge=40, le=150, description="Diastolic blood pressure (mmHg)")
    fasting_glucose: float = Field(..., ge=30, le=600, description="Fasting blood glucose (mg/dL)")
    age: int = Field(..., ge=1, le=120)
    bmi: Optional[float] = Field(None, ge=10.0, le=70.0)
    symptoms: str = Field(..., min_length=3, description="Free-text symptom description")
    question: Optional[str] = Field(None, description="Optional health question for guideline lookup")
    country: Optional[str] = Field(None, description="User's country")
    city: Optional[str] = Field(None, description="User's city or region")
