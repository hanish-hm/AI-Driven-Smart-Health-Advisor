# Smart Health Advisor

Smart Health Advisor is an AI-assisted preventive health web application that combines symptom screening, vital-sign risk assessment, guideline retrieval, outbreak awareness, and nearby care discovery in a single experience.

The project is designed as a lightweight decision-support tool for early guidance, not as a diagnostic system. A user can enter blood pressure, fasting glucose, BMI, location, symptoms, and a health question, and the system responds with structured risk signals, urgency guidance, public-health context, and nearby facility suggestions.

---

## Project Overview

This project brings together five practical healthcare-support functions:

- **Risk assessment** for blood pressure, fasting glucose, and BMI
- **Symptom-based urgency detection** using emergency and doctor-review keyword screening
- **Guideline retrieval** from a curated knowledge base of health guidance
- **Outbreak awareness** using live WHO disease-outbreak feeds
- **Nearby facility lookup** using OpenStreetMap-based location search

The goal is to create a clear, useful, and accessible health-advisory interface that can support awareness and triage-oriented decision-making.

---

## Key Features

- **Structured vital analysis** classifies BP, glucose, and BMI into low, moderate, or high risk categories
- **Urgency detection** flags emergency symptoms and escalates cases that require medical review
- **Guideline-based advice** retrieves the most relevant health guidance for the user's question or symptom context
- **Location-aware outbreak alerts** surface recent WHO outbreak updates relevant to the user's country or region
- **Nearby healthcare discovery** recommends hospitals, clinics, doctors, or pharmacies when escalation is needed
- **Continuously extendable knowledge base** supports curated local guidance plus feed-based additions
- **India-focused content coverage** includes guidance relevant to Indian healthcare and public-health contexts

---

## System Architecture

```text
User -> Frontend (HTML / CSS / JavaScript)
        -> POST /analyze
        -> FastAPI Backend
           -> Risk Engine
           -> Guideline Retrieval Engine
           -> Outbreak Engine
           -> Facility Engine
           -> Background Feed Fetcher
```

### Core Components

- **Frontend**
  Collects user input and renders urgency, risks, advice, outbreak alerts, and facility suggestions.

- **FastAPI Backend**
  Acts as the orchestration layer for validation, analysis, retrieval, and API responses.

- **Risk Engine**
  Applies rule-based clinical thresholds and symptom keyword logic to determine risk and urgency.

- **Guideline Engine**
  Uses local guideline data with lightweight retrieval logic to return relevant health guidance.

- **Outbreak Engine**
  Queries WHO outbreak data and prioritizes alerts relevant to the user's region.

- **Facility Engine**
  Uses OpenStreetMap/Nominatim search to identify nearby healthcare facilities and map links.

- **Background Fetcher**
  Periodically pulls WHO and MoHFW RSS content into the local guideline knowledge base.

---

## How It Works

1. The user submits vitals, symptoms, location, and an optional health question.
2. The backend validates the payload using Pydantic models.
3. The risk engine analyzes blood pressure, glucose, BMI, and symptom severity.
4. The guideline engine retrieves relevant advisory content from the knowledge base.
5. The outbreak engine checks for current WHO alerts related to the user's location.
6. If escalation is needed, the facility engine returns nearby care options.
7. The frontend presents the full result in a single health-advice view.

---

## Urgency Model

| Level | Meaning |
|-------|---------|
| `home_care` | No urgent warning signs detected; monitor symptoms and follow general care advice |
| `see_doctor` | Medical review is recommended based on symptoms, vitals, or both |
| `emergency` | Emergency symptoms were detected and urgent care is advised |

---

## Knowledge Base

The application uses `backend/data/guidelines.json` as its primary local knowledge source.

It includes content related to:

- Hypertension, diabetes, obesity, infectious disease, and general preventive care
- Emergency warning signs and basic first-response guidance
- Maternal health, nutrition, mental health, and public-health education
- India-relevant healthcare guidance and government-linked public-health context

The knowledge base can also be extended through background feed ingestion from public-health sources.

---

## API Surface

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/analyze` | Returns the full health-advice response |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/docs` | OpenAPI / Swagger documentation |
| `GET` | `/` | Serves the main user interface |

### Sample Request

```json
{
  "systolic_bp": 145,
  "diastolic_bp": 95,
  "fasting_glucose": 130,
  "age": 45,
  "bmi": 31.2,
  "country": "India",
  "city": "Mumbai",
  "symptoms": "I have chest pain and feel dizzy",
  "question": "What should I do about high blood pressure?"
}
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, Vanilla JavaScript |
| Backend | Python, FastAPI |
| Validation | Pydantic |
| Guideline Retrieval | sentence-transformers / lightweight lexical fallback |
| Outbreak Data | WHO Disease Outbreak News |
| Geocoding / Facility Search | OpenStreetMap Nominatim |
| Feed Ingestion | feedparser |

---

## Project Strengths

- Combines multiple health-support functions into one workflow
- Uses a clear API-driven architecture with modular backend engines
- Balances static clinical rules with retrieval-based guidance
- Supports live external context through outbreak and facility integrations
- Can be demonstrated easily as a full-stack applied AI project

---

## Disclaimer

This project is intended for informational and educational use only. It is not a substitute for professional medical advice, diagnosis, or treatment. Users should consult a qualified healthcare provider for medical decisions and emergencies.
