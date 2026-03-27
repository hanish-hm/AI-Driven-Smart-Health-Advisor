from pydantic import BaseModel
from typing import List, Optional


class RiskResult(BaseModel):
    condition: str
    risk_level: str          # "low" | "moderate" | "high"
    explanation: str


class OutbreakAlert(BaseModel):
    title: str
    summary: str
    link: str
    date: str
    source: str
    location_match: bool
    match_type: str  # "exact" | "region" | "global_fallback" | "no_alerts"


class NearbyFacility(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    maps_url: str
    open_now: Optional[bool] = None
    rating: Optional[float] = None


class HealthAdviceResponse(BaseModel):
    urgency: str             # "home_care" | "see_doctor" | "emergency"
    urgency_reason: str
    risks: List[RiskResult]
    guideline_answer: str
    symptom_flags: List[str]
    outbreak_alerts: List[OutbreakAlert]
    nearby_facilities: List[NearbyFacility] = []
