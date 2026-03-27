"""
Rule-based risk classifier for hypertension, diabetes, and obesity.
Rules follow WHO/JNC-8 thresholds. Swap `_ml_predict` to plug in an ML model.
"""
from typing import List, Tuple
from backend.models.vitals import VitalsInput
from backend.models.response import RiskResult

# --- Urgency keyword flags (symptom text scanning) ---
EMERGENCY_KEYWORDS = [
    # Cardiovascular
    "chest pain", "chest pressure", "chest tightness", "heart attack", "cardiac arrest",
    "pain in left arm", "jaw pain", "radiating pain",
    # Respiratory
    "can't breathe", "cannot breathe", "difficulty breathing", "unable to breathe",
    "stopped breathing", "no breathing", "respiratory failure", "bluish lips", "blue lips",
    "bluish face", "choking",
    # Neurological
    "stroke", "face drooping", "arm weakness", "speech difficulty", "sudden confusion",
    "loss of consciousness", "unconscious", "unresponsive", "seizure", "convulsion",
    "convulsions", "fits", "paralysis", "sudden paralysis", "numbness", "sudden numbness",
    "sudden severe headache", "thunderclap headache", "worst headache",
    # Eyes
    "sudden vision loss", "sudden blindness", "blurred vision", "loss of vision",
    "curtain over vision", "flashes of light",
    # Bleeding
    "vomiting blood", "coughing blood", "blood in vomit", "bleeding from mouth",
    "severe bleeding", "uncontrolled bleeding", "heavy bleeding", "blood in stool",
    "black stool", "tarry stool",
    # Meningitis / Brain
    "stiff neck", "neck stiffness", "sensitivity to light", "photophobia",
    "rash that doesn't fade", "non-blanching rash",
    # Severe infections / Sepsis
    "sepsis", "blood poisoning", "high fever with rash", "fever with stiff neck",
    "fever with seizure", "fever with confusion",
    # Allergic / Anaphylaxis
    "anaphylaxis", "severe allergic reaction", "throat swelling", "tongue swelling",
    "face swelling", "swollen throat",
    # Abdominal emergencies
    "appendicitis", "severe abdominal pain", "sudden abdominal pain", "rigid abdomen",
    "ruptured",
    # Obstetric emergencies
    "heavy vaginal bleeding", "bleeding during pregnancy", "eclampsia", "seizure in pregnancy",
    # Poisoning / Overdose
    "poisoning", "overdose", "swallowed poison", "ingested chemicals",
    # Trauma
    "head injury", "skull fracture", "spinal injury", "broken neck",
    # Nipah / Ebola / Hemorrhagic fevers
    "encephalitis", "brain inflammation", "hemorrhagic fever", "bleeding from eyes",
    "bleeding from nose and mouth",
    # Diabetic emergencies
    "diabetic coma", "hypoglycemic shock", "unconscious diabetic",
    # Cardiac
    "palpitations with fainting", "heart racing with chest pain",
    # Child emergencies
    "baby not breathing", "infant seizure", "child convulsions", "baby turning blue",
    "child unconscious",
    # Snakebite
    "snakebite", "snake bite", "snake venom", "bitten by snake",
    # Burns
    "severe burn", "chemical burn", "electrical burn", "burn on face",
    # Drowning / Suffocation
    "drowning", "suffocation", "strangling",
    # Suicide
    "suicidal", "want to die", "attempting suicide", "self harm", "self-harm"
]

DOCTOR_KEYWORDS = [
    # Fever related
    "persistent fever", "fever for 3 days", "fever for more than 3 days", "high fever",
    "fever with chills", "night sweats", "fever and rash", "fever and vomiting",
    # Respiratory
    "shortness of breath", "breathlessness", "wheezing", "persistent cough",
    "cough with blood", "cough for 2 weeks", "coughing for weeks", "chest congestion",
    # Digestive
    "persistent vomiting", "vomiting for days", "blood in urine", "dark urine",
    "yellow urine", "frequent diarrhea", "diarrhea for days", "bloody diarrhea",
    "abdominal pain", "stomach pain", "bloating", "jaundice", "yellow skin",
    "yellow eyes", "pale stool",
    # Neurological
    "dizziness", "severe dizziness", "fainting", "blackout", "confusion",
    "memory loss", "disorientation", "persistent headache", "headache for days",
    "migraine", "tremors", "shaking hands",
    # Cardiovascular
    "palpitations", "irregular heartbeat", "rapid heartbeat", "heart racing",
    "swollen legs", "swollen ankles", "swollen feet", "leg swelling",
    # Urinary
    "frequent urination", "painful urination", "burning urination", "unable to urinate",
    "no urination", "blood in urine",
    # Skin
    "spreading rash", "rash all over body", "blisters", "skin peeling",
    "jaundice", "yellowing of skin", "yellowing of eyes", "swollen lymph nodes",
    "lumps", "unexplained bruising",
    # Musculoskeletal
    "joint pain", "severe joint swelling", "inability to walk", "back pain with numbness",
    "muscle weakness", "leg weakness",
    # Eyes / Ears
    "eye discharge", "red eyes", "ear discharge", "hearing loss", "ear pain",
    # Weight / Appetite
    "unexplained weight loss", "rapid weight loss", "loss of appetite", "not eating",
    # Fatigue
    "extreme fatigue", "fatigue", "weakness", "unable to stand", "unable to walk",
    # Reproductive / Maternal
    "missed period", "irregular periods", "heavy periods", "pelvic pain",
    "vaginal discharge", "swelling during pregnancy", "reduced fetal movement",
    # Mental health
    "severe depression", "panic attack", "severe anxiety", "hallucinations",
    "hearing voices", "paranoia",
    # Infections
    "swollen glands", "persistent sore throat", "difficulty swallowing",
    "mouth sores", "oral thrush",
    # Diabetes related
    "excessive thirst", "excessive hunger", "frequent urination", "slow healing wound",
    "diabetic foot", "foot ulcer",
    # Thyroid
    "neck swelling", "goiter", "hair loss", "cold intolerance", "heat intolerance",
    # Sickle cell
    "sickle cell pain", "pain crisis", "vaso-occlusive",
    # Nipah / viral
    "altered consciousness", "drowsiness", "encephalitis symptoms",
    # General
    "swelling", "persistent pain", "symptoms not improving", "getting worse"
]


def classify_bp(systolic: int, diastolic: int) -> Tuple[str, str]:
    if systolic >= 180 or diastolic >= 120:
        return "high", f"BP {systolic}/{diastolic} mmHg — hypertensive crisis"
    if systolic >= 140 or diastolic >= 90:
        return "moderate", f"BP {systolic}/{diastolic} mmHg — Stage 2 hypertension"
    if systolic >= 130 or diastolic >= 80:
        return "moderate", f"BP {systolic}/{diastolic} mmHg — Stage 1 hypertension"
    if systolic >= 120:
        return "low", f"BP {systolic}/{diastolic} mmHg — elevated (pre-hypertension)"
    return "low", f"BP {systolic}/{diastolic} mmHg — normal"


def classify_glucose(glucose: float, age: int) -> Tuple[str, str]:
    if glucose >= 200:
        return "high", f"Glucose {glucose} mg/dL — likely diabetic range"
    if glucose >= 126:
        return "moderate", f"Glucose {glucose} mg/dL — fasting diabetes threshold"
    if glucose >= 100:
        return "low", f"Glucose {glucose} mg/dL — pre-diabetic range"
    return "low", f"Glucose {glucose} mg/dL — normal"


def classify_bmi(bmi: float | None) -> Tuple[str, str] | None:
    if bmi is None:
        return None
    if bmi >= 35:
        return "high", f"BMI {bmi:.1f} — severe obesity, high cardiometabolic risk"
    if bmi >= 30:
        return "moderate", f"BMI {bmi:.1f} — obese"
    if bmi >= 25:
        return "low", f"BMI {bmi:.1f} — overweight"
    if bmi >= 18.5:
        return "low", f"BMI {bmi:.1f} — normal"
    if bmi >= 16:
        return "moderate", f"BMI {bmi:.1f} — underweight, risk of malnutrition and anemia"
    return "high", f"BMI {bmi:.1f} — severely underweight, high risk of malnutrition"


def scan_symptoms(symptoms: str) -> Tuple[str, str, List[str]]:
    """Returns (urgency, reason, flagged_keywords)."""
    text = symptoms.lower()
    flags = [kw for kw in EMERGENCY_KEYWORDS if kw in text]
    if flags:
        return "emergency", f"Emergency symptom(s) detected: {', '.join(flags)}", flags
    flags = [kw for kw in DOCTOR_KEYWORDS if kw in text]
    if flags:
        return "see_doctor", f"Symptom(s) requiring medical review: {', '.join(flags)}", flags
    return "home_care", "No urgent symptoms detected — monitor and follow home care advice.", []


def _ml_predict(vitals: VitalsInput) -> List[RiskResult] | None:
    """
    Hook for an ML model. Return a list of RiskResult or None to fall back to rules.
    Replace this stub with: load model, run inference, return results.
    """
    return None


def assess_risk(vitals: VitalsInput) -> Tuple[List[RiskResult], str, str, List[str]]:
    ml_results = _ml_predict(vitals)

    if ml_results is not None:
        risks = ml_results
    else:
        risks = []
        bp_level, bp_msg = classify_bp(vitals.systolic_bp, vitals.diastolic_bp)
        risks.append(RiskResult(condition="Hypertension", risk_level=bp_level, explanation=bp_msg))

        gl_level, gl_msg = classify_glucose(vitals.fasting_glucose, vitals.age)
        risks.append(RiskResult(condition="Diabetes", risk_level=gl_level, explanation=gl_msg))

        bmi_result = classify_bmi(vitals.bmi)
        if bmi_result:
            risks.append(RiskResult(condition="Obesity", risk_level=bmi_result[0], explanation=bmi_result[1]))

    urgency, reason, flags = scan_symptoms(vitals.symptoms)

    # Escalate urgency based on vital risk levels
    high_risk_count = sum(1 for r in risks if r.risk_level == "high")
    if urgency == "home_care" and high_risk_count >= 1:
        urgency, reason = "see_doctor", "High-risk vitals detected — medical evaluation recommended."

    return risks, urgency, reason, flags
