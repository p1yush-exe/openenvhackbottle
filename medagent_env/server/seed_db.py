"""
Seed the MedAgent SQLite database with clinical case data.

Creates server/data/medagent.db and populates three tables:
  - vital_triage_cases
  - news2_cases
  - medication_dosing_cases

10 cases per task (30 total). Run this script once before starting the server,
or let the Dockerfile execute it at build time.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "medagent.db"

# ---------------------------------------------------------------------------
# Case data
# ---------------------------------------------------------------------------

VITAL_TRIAGE_CASES = [
    # 0 - Stable post-op
    {
        "case_id": 0, "difficulty": "easy",
        "scenario": "65-year-old male, post-op day 1 after elective knee replacement. No complaints.",
        "fields": {"heart_rate": 88, "systolic_bp": 126, "diastolic_bp": 78,
                   "spo2_percent": 97, "respiratory_rate": 16, "temperature_celsius": 37.2,
                   "consciousness": "alert"},
        "answer": "stable",
    },
    # 1 - Critical septic shock
    {
        "case_id": 1, "difficulty": "easy",
        "scenario": "45-year-old female rushed in with sudden-onset chest pain, diaphoresis and shortness of breath.",
        "fields": {"heart_rate": 122, "systolic_bp": 86, "diastolic_bp": 55,
                   "spo2_percent": 89, "respiratory_rate": 26, "temperature_celsius": 38.1,
                   "consciousness": "confused"},
        "answer": "critical",
    },
    # 2 - Concerning COPD
    {
        "case_id": 2, "difficulty": "easy",
        "scenario": "72-year-old male with COPD, mild increased shortness of breath over 2 days.",
        "fields": {"heart_rate": 98, "systolic_bp": 148, "diastolic_bp": 90,
                   "spo2_percent": 92, "respiratory_rate": 22, "temperature_celsius": 37.4,
                   "consciousness": "alert"},
        "answer": "concerning",
    },
    # 3 - Stable post-partum
    {
        "case_id": 3, "difficulty": "easy",
        "scenario": "28-year-old female, post-partum day 2 after uncomplicated vaginal delivery. Breastfeeding well.",
        "fields": {"heart_rate": 74, "systolic_bp": 112, "diastolic_bp": 70,
                   "spo2_percent": 99, "respiratory_rate": 14, "temperature_celsius": 37.0,
                   "consciousness": "alert"},
        "answer": "stable",
    },
    # 4 - Critical overdose
    {
        "case_id": 4, "difficulty": "easy",
        "scenario": "59-year-old male found unresponsive in a park. Paramedics report possible overdose.",
        "fields": {"heart_rate": 44, "systolic_bp": 72, "diastolic_bp": 38,
                   "spo2_percent": 83, "respiratory_rate": 6, "temperature_celsius": 35.0,
                   "consciousness": "unresponsive"},
        "answer": "critical",
    },
    # 5 - Stable young athlete
    {
        "case_id": 5, "difficulty": "easy",
        "scenario": "22-year-old male marathon runner, post-race routine check. Feels well.",
        "fields": {"heart_rate": 52, "systolic_bp": 108, "diastolic_bp": 62,
                   "spo2_percent": 99, "respiratory_rate": 13, "temperature_celsius": 37.6,
                   "consciousness": "alert"},
        "answer": "stable",
    },
    # 6 - Concerning pyrexia
    {
        "case_id": 6, "difficulty": "easy",
        "scenario": "38-year-old female with 3-day history of fever and productive cough.",
        "fields": {"heart_rate": 112, "systolic_bp": 102, "diastolic_bp": 68,
                   "spo2_percent": 94, "respiratory_rate": 23, "temperature_celsius": 38.9,
                   "consciousness": "alert"},
        "answer": "concerning",
    },
    # 7 - Critical meningitis
    {
        "case_id": 7, "difficulty": "easy",
        "scenario": "19-year-old male presenting with severe headache, neck stiffness and photophobia.",
        "fields": {"heart_rate": 134, "systolic_bp": 82, "diastolic_bp": 50,
                   "spo2_percent": 96, "respiratory_rate": 28, "temperature_celsius": 40.1,
                   "consciousness": "confused"},
        "answer": "critical",
    },
    # 8 - Stable mild hypertension
    {
        "case_id": 8, "difficulty": "easy",
        "scenario": "55-year-old female with known hypertension, attending routine medication review.",
        "fields": {"heart_rate": 78, "systolic_bp": 142, "diastolic_bp": 88,
                   "spo2_percent": 98, "respiratory_rate": 15, "temperature_celsius": 36.8,
                   "consciousness": "alert"},
        "answer": "stable",
    },
    # 9 - Concerning hypoglycaemia
    {
        "case_id": 9, "difficulty": "easy",
        "scenario": "67-year-old diabetic male, found diaphoretic and confused at home by carer.",
        "fields": {"heart_rate": 108, "systolic_bp": 96, "diastolic_bp": 60,
                   "spo2_percent": 95, "respiratory_rate": 20, "temperature_celsius": 36.4,
                   "consciousness": "confused"},
        "answer": "concerning",
    },
]

NEWS2_CASES = [
    # 0 - NEWS2 = 0 (stable post-op)
    {
        "case_id": 0, "difficulty": "medium",
        "scenario": "65-year-old male, post-op day 1 after elective knee replacement. On room air.",
        "fields": {"heart_rate": 88, "systolic_bp": 126, "spo2_percent": 97,
                   "respiratory_rate": 16, "temperature_celsius": 37.2,
                   "consciousness": "alert", "on_supplemental_oxygen": False},
        "answer": "0",
        "total_news2": 0,
    },
    # 1 - NEWS2 = 16 (septic shock on O2)
    # RR24→2, SpO2-91→3, O2-yes→2, SBP-86→3, HR-122→2, confused→3, T38.2→1
    {
        "case_id": 1, "difficulty": "medium",
        "scenario": "45-year-old female with septic shock, on 4L O2 via nasal cannula.",
        "fields": {"heart_rate": 122, "systolic_bp": 86, "spo2_percent": 91,
                   "respiratory_rate": 24, "temperature_celsius": 38.2,
                   "consciousness": "confused", "on_supplemental_oxygen": True},
        "answer": "16",
        "total_news2": 16,
    },
    # 2 - NEWS2 = 5 (COPD exacerbation)
    # RR22→2, SpO2-92→2, O2-no→0, SBP-148→0, HR-98→1, alert→0, T37.4→0
    {
        "case_id": 2, "difficulty": "medium",
        "scenario": "72-year-old male with COPD exacerbation, on room air.",
        "fields": {"heart_rate": 98, "systolic_bp": 148, "spo2_percent": 92,
                   "respiratory_rate": 22, "temperature_celsius": 37.4,
                   "consciousness": "alert", "on_supplemental_oxygen": False},
        "answer": "5",
        "total_news2": 5,
    },
    # 3 - NEWS2 = 0 (post-partum)
    {
        "case_id": 3, "difficulty": "medium",
        "scenario": "28-year-old female post-partum, on room air.",
        "fields": {"heart_rate": 74, "systolic_bp": 112, "spo2_percent": 99,
                   "respiratory_rate": 14, "temperature_celsius": 37.0,
                   "consciousness": "alert", "on_supplemental_oxygen": False},
        "answer": "0",
        "total_news2": 0,
    },
    # 4 - NEWS2 = 18 (cardiac arrest)
    # RR8→3, SpO2-83→3, O2-yes→2, SBP-72→3, HR-44→1, unresponsive→3, T35.0→3
    {
        "case_id": 4, "difficulty": "medium",
        "scenario": "59-year-old male post-cardiac arrest, on 15L O2 non-rebreather.",
        "fields": {"heart_rate": 44, "systolic_bp": 72, "spo2_percent": 83,
                   "respiratory_rate": 8, "temperature_celsius": 35.0,
                   "consciousness": "unresponsive", "on_supplemental_oxygen": True},
        "answer": "18",
        "total_news2": 18,
    },
    # 5 - NEWS2 = 3 (mild pneumonia)
    # RR21→2, SpO2-96→0, O2-no→0, SBP-118→0, HR-94→1, alert→0, T37.8→0
    {
        "case_id": 5, "difficulty": "medium",
        "scenario": "50-year-old female with mild community-acquired pneumonia, on room air.",
        "fields": {"heart_rate": 94, "systolic_bp": 118, "spo2_percent": 96,
                   "respiratory_rate": 21, "temperature_celsius": 37.8,
                   "consciousness": "alert", "on_supplemental_oxygen": False},
        "answer": "3",
        "total_news2": 3,
    },
    # 6 - NEWS2 = 7 (UTI with confusion)
    # RR20→0, SpO2-94→1, O2-no→0, SBP-104→1, HR-108→1, confused→3, T38.5→1
    {
        "case_id": 6, "difficulty": "medium",
        "scenario": "82-year-old female with UTI, presenting confused to ED.",
        "fields": {"heart_rate": 108, "systolic_bp": 104, "spo2_percent": 94,
                   "respiratory_rate": 20, "temperature_celsius": 38.5,
                   "consciousness": "confused", "on_supplemental_oxygen": False},
        "answer": "7",
        "total_news2": 7,
    },
    # 7 - NEWS2 = 2 (stable bradycardia)
    # RR16→0, SpO2-98→0, O2-no→0, SBP-118→0, HR-46→1, alert→0, T35.8→1
    {
        "case_id": 7, "difficulty": "medium",
        "scenario": "70-year-old male on beta-blockers, routine check showing bradycardia.",
        "fields": {"heart_rate": 46, "systolic_bp": 118, "spo2_percent": 98,
                   "respiratory_rate": 16, "temperature_celsius": 35.8,
                   "consciousness": "alert", "on_supplemental_oxygen": False},
        "answer": "2",
        "total_news2": 2,
    },
    # 8 - NEWS2 = 11 (PE on O2)
    # RR25→3, SpO2-93→2, O2-yes→2, SBP-96→2, HR-118→2, alert→0, T37.0→0
    {
        "case_id": 8, "difficulty": "medium",
        "scenario": "56-year-old male with suspected pulmonary embolism, on 4L O2.",
        "fields": {"heart_rate": 118, "systolic_bp": 96, "spo2_percent": 93,
                   "respiratory_rate": 25, "temperature_celsius": 37.0,
                   "consciousness": "alert", "on_supplemental_oxygen": True},
        "answer": "11",
        "total_news2": 11,
    },
    # 9 - NEWS2 = 4 (DKA mild)
    # RR23→2, SpO2-97→0, O2-no→0, SBP-106→1, HR-106→1, alert→0, T36.2→0
    {
        "case_id": 9, "difficulty": "medium",
        "scenario": "24-year-old male with mild diabetic ketoacidosis, on room air.",
        "fields": {"heart_rate": 106, "systolic_bp": 106, "spo2_percent": 97,
                   "respiratory_rate": 23, "temperature_celsius": 36.2,
                   "consciousness": "alert", "on_supplemental_oxygen": False},
        "answer": "4",
        "total_news2": 4,
    },
]

MEDICATION_DOSING_CASES = [
    # 0 - Pip-Tazo, eGFR=62, normal_dose
    {
        "case_id": 0, "difficulty": "hard",
        "scenario": "52-year-old male with community-acquired pneumonia. Prescribed Piperacillin-Tazobactam.",
        "fields": {"drug": "Piperacillin-Tazobactam", "standard_dose": "4.5g IV q6h",
                   "patient_weight_kg": 78, "serum_creatinine_umol_L": 88,
                   "egfr_ml_min": 62, "age_years": 52, "dialysis": False},
        "answer": "normal_dose",
        "rule_applied": "eGFR >= 40: no adjustment required for Pip-Tazo.",
    },
    # 1 - Vancomycin, eGFR=22, dose_50
    {
        "case_id": 1, "difficulty": "hard",
        "scenario": "67-year-old female with MRSA bacteraemia. Vancomycin therapy planned. Labs show reduced kidney function.",
        "fields": {"drug": "Vancomycin", "standard_dose": "25mg/kg IV loading then 15mg/kg q12h",
                   "patient_weight_kg": 62, "serum_creatinine_umol_L": 210,
                   "egfr_ml_min": 22, "age_years": 67, "dialysis": False},
        "answer": "dose_50",
        "rule_applied": "Vancomycin: eGFR 10-29 => 50% dose reduction (extend interval).",
    },
    # 2 - Meropenem, eGFR=58, normal_dose
    {
        "case_id": 2, "difficulty": "hard",
        "scenario": "44-year-old male with intra-abdominal sepsis, on Meropenem. Near-normal renal function.",
        "fields": {"drug": "Meropenem", "standard_dose": "1g IV q8h",
                   "patient_weight_kg": 85, "serum_creatinine_umol_L": 95,
                   "egfr_ml_min": 58, "age_years": 44, "dialysis": False},
        "answer": "normal_dose",
        "rule_applied": "Meropenem: eGFR >= 50, no adjustment.",
    },
    # 3 - Ciprofloxacin, eGFR=6, dose_50
    {
        "case_id": 3, "difficulty": "hard",
        "scenario": "79-year-old female with ESRD on haemodialysis presenting with Gram-negative UTI. Ciprofloxacin considered.",
        "fields": {"drug": "Ciprofloxacin", "standard_dose": "400mg IV q12h",
                   "patient_weight_kg": 55, "serum_creatinine_umol_L": 680,
                   "egfr_ml_min": 6, "age_years": 79, "dialysis": True},
        "answer": "dose_50",
        "rule_applied": "Ciprofloxacin: eGFR < 30 => 50% dose reduction.",
    },
    # 4 - Metronidazole, eGFR=90, normal_dose
    {
        "case_id": 4, "difficulty": "hard",
        "scenario": "33-year-old male with C. difficile colitis. Metronidazole prescribed. Labs normal.",
        "fields": {"drug": "Metronidazole", "standard_dose": "500mg PO/IV q8h",
                   "patient_weight_kg": 80, "serum_creatinine_umol_L": 75,
                   "egfr_ml_min": 90, "age_years": 33, "dialysis": False},
        "answer": "normal_dose",
        "rule_applied": "Metronidazole does not require renal dose adjustment.",
    },
    # 5 - Pip-Tazo, eGFR=28, dose_75
    {
        "case_id": 5, "difficulty": "hard",
        "scenario": "61-year-old female with hospital-acquired pneumonia. Piperacillin-Tazobactam ordered. Moderate CKD.",
        "fields": {"drug": "Piperacillin-Tazobactam", "standard_dose": "4.5g IV q6h",
                   "patient_weight_kg": 70, "serum_creatinine_umol_L": 168,
                   "egfr_ml_min": 28, "age_years": 61, "dialysis": False},
        "answer": "dose_75",
        "rule_applied": "Pip-Tazo: eGFR 20-39 => 75% dose (reduce to 3.375g q6h).",
    },
    # 6 - Vancomycin, eGFR=72, normal_dose
    {
        "case_id": 6, "difficulty": "hard",
        "scenario": "48-year-old male with methicillin-resistant wound infection. Vancomycin planned. Normal renal function.",
        "fields": {"drug": "Vancomycin", "standard_dose": "25mg/kg IV loading then 15mg/kg q12h",
                   "patient_weight_kg": 90, "serum_creatinine_umol_L": 78,
                   "egfr_ml_min": 72, "age_years": 48, "dialysis": False},
        "answer": "normal_dose",
        "rule_applied": "Vancomycin: eGFR >= 50, no adjustment required.",
    },
    # 7 - Meropenem, eGFR=15, dose_50
    {
        "case_id": 7, "difficulty": "hard",
        "scenario": "73-year-old male with Klebsiella bacteraemia. Meropenem considered. Severe CKD.",
        "fields": {"drug": "Meropenem", "standard_dose": "1g IV q8h",
                   "patient_weight_kg": 68, "serum_creatinine_umol_L": 385,
                   "egfr_ml_min": 15, "age_years": 73, "dialysis": False},
        "answer": "dose_50",
        "rule_applied": "Meropenem: eGFR 10-25 => 50% dose (500mg q8h or 1g q12h).",
    },
    # 8 - Vancomycin, eGFR=6, contraindicated
    {
        "case_id": 8, "difficulty": "hard",
        "scenario": "85-year-old female with ESRD (not on dialysis) with MRSA endocarditis. Vancomycin considered.",
        "fields": {"drug": "Vancomycin", "standard_dose": "25mg/kg IV loading then 15mg/kg q12h",
                   "patient_weight_kg": 50, "serum_creatinine_umol_L": 720,
                   "egfr_ml_min": 6, "age_years": 85, "dialysis": False},
        "answer": "contraindicated",
        "rule_applied": "Vancomycin: eGFR < 10 (non-dialysis) => contraindicated, requires specialist review.",
    },
    # 9 - Ciprofloxacin, eGFR=45, normal_dose
    {
        "case_id": 9, "difficulty": "hard",
        "scenario": "58-year-old male with prostatitis. Ciprofloxacin ordered. Mild CKD.",
        "fields": {"drug": "Ciprofloxacin", "standard_dose": "400mg IV q12h",
                   "patient_weight_kg": 82, "serum_creatinine_umol_L": 130,
                   "egfr_ml_min": 45, "age_years": 58, "dialysis": False},
        "answer": "normal_dose",
        "rule_applied": "Ciprofloxacin: eGFR >= 30, no adjustment required.",
    },
]


def seed(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # ---- vital_triage_cases ----
    cur.execute("DROP TABLE IF EXISTS vital_triage_cases")
    cur.execute("""
        CREATE TABLE vital_triage_cases (
            case_id   INTEGER PRIMARY KEY,
            difficulty TEXT NOT NULL,
            scenario  TEXT NOT NULL,
            fields    TEXT NOT NULL,  -- JSON blob
            answer    TEXT NOT NULL
        )
    """)
    for c in VITAL_TRIAGE_CASES:
        cur.execute(
            "INSERT INTO vital_triage_cases VALUES (?,?,?,?,?)",
            (c["case_id"], c["difficulty"], c["scenario"],
             json.dumps(c["fields"]), c["answer"]),
        )

    # ---- news2_cases ----
    cur.execute("DROP TABLE IF EXISTS news2_cases")
    cur.execute("""
        CREATE TABLE news2_cases (
            case_id    INTEGER PRIMARY KEY,
            difficulty TEXT NOT NULL,
            scenario   TEXT NOT NULL,
            fields     TEXT NOT NULL,
            answer     TEXT NOT NULL,
            total_news2 INTEGER NOT NULL
        )
    """)
    for c in NEWS2_CASES:
        cur.execute(
            "INSERT INTO news2_cases VALUES (?,?,?,?,?,?)",
            (c["case_id"], c["difficulty"], c["scenario"],
             json.dumps(c["fields"]), c["answer"], c["total_news2"]),
        )

    # ---- medication_dosing_cases ----
    cur.execute("DROP TABLE IF EXISTS medication_dosing_cases")
    cur.execute("""
        CREATE TABLE medication_dosing_cases (
            case_id      INTEGER PRIMARY KEY,
            difficulty   TEXT NOT NULL,
            scenario     TEXT NOT NULL,
            fields       TEXT NOT NULL,
            answer       TEXT NOT NULL,
            rule_applied TEXT NOT NULL
        )
    """)
    for c in MEDICATION_DOSING_CASES:
        cur.execute(
            "INSERT INTO medication_dosing_cases VALUES (?,?,?,?,?,?)",
            (c["case_id"], c["difficulty"], c["scenario"],
             json.dumps(c["fields"]), c["answer"], c["rule_applied"]),
        )

    conn.commit()
    conn.close()
    print(f"[seed_db] Seeded {db_path} with "
          f"{len(VITAL_TRIAGE_CASES)} vital_triage, "
          f"{len(NEWS2_CASES)} news2, "
          f"{len(MEDICATION_DOSING_CASES)} medication_dosing cases.")


if __name__ == "__main__":
    seed()
