# 🩺 AI-Driven Smart Health Advisor

A personalized preventive health guidance system that analyzes your vitals and symptoms to deliver evidence-based advice, real-time outbreak alerts, and nearby hospital recommendations — all powered by WHO & NCDC protocols.

---

## ✨ Features

- **Vitals Risk Assessment** — Classifies Blood Pressure, Fasting Glucose, and BMI against WHO/JNC-8 thresholds into Low / Moderate / High risk levels
- **Symptom Analysis** — Scans free-text symptoms for emergency and doctor-consultation keywords, escalating urgency automatically
- **RAG-Powered Guideline Advice** — Uses sentence-transformer embeddings to retrieve the most relevant WHO/NCDC guideline for your specific query
- **Live WHO Outbreak Alerts** — Fetches real-time Disease Outbreak News from WHO, matched to your country or region
- **Nearby Health Facilities** — Finds hospitals, clinics, and doctors near your city using OpenStreetMap, with direct Google Maps links
- **Auto-Updating Guidelines** — A background fetcher periodically pulls new entries from WHO and MoHFW RSS feeds and appends them to the local knowledge base
- **India-Specific Guidance** — Includes MoHFW, ICMR, NTEP, NVBDCP, and Ayushman Bharat scheme information for Indian users

---

## 🏗️ Architecture

```
User → Frontend (HTML / CSS / JS)
           ↓  POST /analyze
       FastAPI Backend
           ├── Risk Engine       →  Rule-based BP / Glucose / BMI classifier (ML hook included)
           ├── RAG Engine        →  Sentence-transformer retrieval over WHO/NCDC guidelines
           ├── Outbreak Engine   →  Live WHO Disease Outbreak News (1-hour cache)
           ├── Facility Engine   →  Nominatim geocoding + OpenStreetMap hospital search
           └── Fetcher           →  Periodic WHO/MoHFW RSS ingestion (24-hour interval)
```

---

## 🧠 How It Works

1. User submits vitals (BP, glucose, BMI, age) and describes symptoms
2. **Risk Engine** classifies each vital against clinical thresholds
3. **Symptom scanner** checks for emergency or doctor-level keywords and escalates urgency
4. **RAG Engine** embeds the user's question and retrieves the closest matching guideline chunk
5. **Outbreak Engine** fetches the latest WHO alerts filtered to the user's location
6. If urgency is `see_doctor` or `emergency`, **Facility Engine** finds nearby hospitals and returns Google Maps links
7. All results are returned in a single API response and rendered in the UI

---

## 📊 Urgency Levels

| Level | Meaning |
|-------|---------|
| ✅ `home_care` | No urgent symptoms — monitor and follow home care advice |
| ⚠️ `see_doctor` | Symptoms or vitals require medical evaluation |
| 🚨 `emergency` | Critical symptoms detected — seek immediate care |

---

## 🗂️ Knowledge Base

Guidelines are stored in `backend/data/guidelines.json` and cover:

- WHO protocols for hypertension, diabetes, obesity, TB, malaria, dengue, COVID-19, and 40+ conditions
- NCDC/ICMR/MoHFW India-specific guidance including Ayushman Bharat, NTEP, and NVBDCP
- Maternal health, mental health, emergency first aid, nutrition, and immunization guidelines
- Auto-updated entries from WHO and MoHFW RSS feeds on every server run

---

## 🔌 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Submit vitals + symptoms, receive full health advice |
| `GET`  | `/health`  | Server health check |
| `GET`  | `/docs`    | Auto-generated Swagger UI |

### Sample Request

```json
POST /analyze
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

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, Vanilla JS |
| Backend | Python, FastAPI |
| NLP / RAG | `sentence-transformers` (all-MiniLM-L6-v2) |
| Geocoding | Nominatim (OpenStreetMap) |
| Outbreak Data | WHO Disease Outbreak News API |
| Guidelines Sync | `feedparser` (WHO + MoHFW RSS) |

---

## ⚠️ Disclaimer

This tool is for **informational and educational purposes only**. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical decisions.
