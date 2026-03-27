from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.models.vitals import VitalsInput
from backend.models.response import HealthAdviceResponse
from backend.engines.risk_engine import assess_risk
from backend.engines.rag_engine import load_rag_engine, query_guidelines
from backend.engines.outbreak_engine import get_relevant_alerts
from backend.engines.facility_engine import get_nearby_facilities
from backend.fetcher import start_background_fetcher

app = FastAPI(title="Smart Health Advisor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
async def startup():
    load_rag_engine()
    start_background_fetcher()


@app.get("/")
def serve_ui():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.post("/analyze", response_model=HealthAdviceResponse)
def analyze(vitals: VitalsInput):
    risks, urgency, urgency_reason, symptom_flags = assess_risk(vitals)

    # Build query: use explicit question or fall back to symptoms
    query = vitals.question or vitals.symptoms
    guideline_answer = query_guidelines(query, vitals.country)
    outbreak_alerts = get_relevant_alerts(vitals.country, vitals.city)

    nearby_facilities = []
    if urgency in ("see_doctor", "emergency"):
        nearby_facilities = get_nearby_facilities(vitals.city, vitals.country)

    return HealthAdviceResponse(
        urgency=urgency,
        urgency_reason=urgency_reason,
        risks=risks,
        guideline_answer=guideline_answer,
        symptom_flags=symptom_flags,
        outbreak_alerts=outbreak_alerts,
        nearby_facilities=nearby_facilities,
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
