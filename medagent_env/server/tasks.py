"""
Embedded task cases for the MedAgent Environment.

Three difficulty levels, each with 5 self-contained patient scenarios.
No external data files required — all data is embedded here.
"""

from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Task 1 – Vital Signs Triage (Easy)
# ---------------------------------------------------------------------------
# Agent queries individual vital fields then submits one of:
#   "stable" | "concerning" | "critical"
#
# Simplified triage rules (RED FLAGS → critical, AMBER → concerning, else stable):
#   Critical  : SpO2 < 90, or SBP < 90, or HR < 40 or HR > 130, or RR < 8 or RR > 24,
#               or consciousness ≠ alert
#   Concerning: SpO2 90–94, or SBP 90–100, or HR 110–130, or RR 21–24, or Temp < 36
#   Stable    : everything within normal bounds

VITAL_TRIAGE_CASES: List[Dict[str, Any]] = [
    {
        "case_id": 0,
        "scenario": (
            "65-year-old male, post-op day 1 after elective knee replacement. "
            "No complaints."
        ),
        "fields": {
            "heart_rate": 88,
            "systolic_bp": 126,
            "diastolic_bp": 78,
            "spo2_percent": 97,
            "respiratory_rate": 16,
            "temperature_celsius": 37.2,
            "consciousness": "alert",
        },
        "answer": "stable",
    },
    {
        "case_id": 1,
        "scenario": (
            "45-year-old female rushed in with sudden-onset chest pain, "
            "diaphoresis and shortness of breath."
        ),
        "fields": {
            "heart_rate": 122,
            "systolic_bp": 86,
            "diastolic_bp": 55,
            "spo2_percent": 89,
            "respiratory_rate": 26,
            "temperature_celsius": 38.1,
            "consciousness": "confused",
        },
        "answer": "critical",
    },
    {
        "case_id": 2,
        "scenario": (
            "72-year-old male with known COPD, presenting for routine follow-up. "
            "Reports mild increased shortness of breath over 2 days."
        ),
        "fields": {
            "heart_rate": 98,
            "systolic_bp": 148,
            "diastolic_bp": 90,
            "spo2_percent": 92,
            "respiratory_rate": 22,
            "temperature_celsius": 37.4,
            "consciousness": "alert",
        },
        "answer": "concerning",
    },
    {
        "case_id": 3,
        "scenario": (
            "28-year-old female, post-partum day 2 after uncomplicated vaginal delivery. "
            "Breastfeeding well, no complaints."
        ),
        "fields": {
            "heart_rate": 74,
            "systolic_bp": 112,
            "diastolic_bp": 70,
            "spo2_percent": 99,
            "respiratory_rate": 14,
            "temperature_celsius": 37.0,
            "consciousness": "alert",
        },
        "answer": "stable",
    },
    {
        "case_id": 4,
        "scenario": (
            "59-year-old male found unresponsive in a park. "
            "Paramedics report possible overdose."
        ),
        "fields": {
            "heart_rate": 44,
            "systolic_bp": 72,
            "diastolic_bp": 38,
            "spo2_percent": 83,
            "respiratory_rate": 6,
            "temperature_celsius": 35.0,
            "consciousness": "unresponsive",
        },
        "answer": "critical",
    },
]


def grade_vital_triage(answer: str, case: Dict[str, Any]) -> Tuple[float, str]:
    """Return (score 0.0-1.0, feedback)."""
    correct = case["answer"]
    if answer.strip().lower() == correct:
        return 1.0, f"Correct! Triage category is '{correct}'."
    # partial credit: concerning vs critical (adjacent categories)
    adjacents = {
        ("concerning", "critical"), ("critical", "concerning"),
        ("stable", "concerning"), ("concerning", "stable"),
    }
    if (answer.strip().lower(), correct) in adjacents:
        return 0.3, f"Partially correct. You chose '{answer}' but the answer is '{correct}'."
    return 0.0, f"Incorrect. You chose '{answer}' but the answer is '{correct}'."


# ---------------------------------------------------------------------------
# Task 2 – NEWS2 Score Calculation (Medium)
# ---------------------------------------------------------------------------
# Agent queries vitals and computes the National Early Warning Score 2 (NEWS2).
# Agent must submit the total integer score as a string, e.g. "7".
#
# NEWS2 component scoring:
#   Respiratory rate (breaths/min): ≤8→3, 9-11→1, 12-20→0, 21-24→2, ≥25→3
#   SpO2 % (Scale 1, no O2 therapy): ≤91→3, 92-93→2, 94-95→1, ≥96→0
#   Supplemental O2:  Yes→2, No→0
#   Systolic BP (mmHg): ≤90→3, 91-100→2, 101-110→1, 111-219→0, ≥220→3
#   HR (bpm): ≤40→3, 41-50→1, 51-90→0, 91-110→1, 111-130→2, ≥131→3
#   Consciousness: ACVPU alert→0, any impairment→3
#   Temperature (°C): ≤35.0→3, 35.1-36.0→1, 36.1-38.0→0, 38.1-39.0→1, ≥39.1→2

NEWS2_CASES: List[Dict[str, Any]] = [
    {
        "case_id": 0,
        "scenario": (
            "65-year-old male, post-op day 1 after elective knee replacement. "
            "On room air."
        ),
        "fields": {
            "heart_rate": 88,
            "systolic_bp": 126,
            "spo2_percent": 97,
            "respiratory_rate": 16,
            "temperature_celsius": 37.2,
            "consciousness": "alert",
            "on_supplemental_oxygen": False,
        },
        # RR16→0, SpO2-97→0, O2-no→0, SBP-126→0, HR-88→0, alert→0, T37.2→0
        "answer": "0",
        "total_news2": 0,
    },
    {
        "case_id": 1,
        "scenario": (
            "45-year-old female with septic shock, on 4L O2 via nasal cannula."
        ),
        "fields": {
            "heart_rate": 122,
            "systolic_bp": 86,
            "spo2_percent": 91,
            "respiratory_rate": 24,
            "temperature_celsius": 38.2,
            "consciousness": "confused",
            "on_supplemental_oxygen": True,
        },
        # RR24→2, SpO2-91→3, O2-yes→2, SBP-86→3, HR-122→2, confused→3, T38.2→1
        "answer": "16",
        "total_news2": 16,
    },
    {
        "case_id": 2,
        "scenario": (
            "72-year-old male with COPD exacerbation, on room air."
        ),
        "fields": {
            "heart_rate": 98,
            "systolic_bp": 148,
            "spo2_percent": 92,
            "respiratory_rate": 22,
            "temperature_celsius": 37.4,
            "consciousness": "alert",
            "on_supplemental_oxygen": False,
        },
        # RR22→2, SpO2-92→2, O2-no→0, SBP-148→0, HR-98→1, alert→0, T37.4→0
        "answer": "5",
        "total_news2": 5,
    },
    {
        "case_id": 3,
        "scenario": (
            "28-year-old female post-partum, on room air."
        ),
        "fields": {
            "heart_rate": 74,
            "systolic_bp": 112,
            "spo2_percent": 99,
            "respiratory_rate": 14,
            "temperature_celsius": 37.0,
            "consciousness": "alert",
            "on_supplemental_oxygen": False,
        },
        # RR14→0, SpO2-99→0, O2-no→0, SBP-112→0, HR-74→0, alert→0, T37.0→0
        "answer": "0",
        "total_news2": 0,
    },
    {
        "case_id": 4,
        "scenario": (
            "59-year-old male post-cardiac arrest, on 15L O2 non-rebreather."
        ),
        "fields": {
            "heart_rate": 44,
            "systolic_bp": 72,
            "spo2_percent": 83,
            "respiratory_rate": 8,
            "temperature_celsius": 35.0,
            "consciousness": "unresponsive",
            "on_supplemental_oxygen": True,
        },
        # RR8→3, SpO2-83→3, O2-yes→2, SBP-72→3, HR-44→1, unresponsive→3, T35.0→3
        "answer": "18",
        "total_news2": 18,
    },
]


def grade_news2(answer: str, case: Dict[str, Any]) -> Tuple[float, str]:
    """Return (score 0.0-1.0, feedback)."""
    correct = case["total_news2"]
    try:
        predicted = int(answer.strip())
    except ValueError:
        return 0.0, f"Answer must be an integer. Got: '{answer}'."
    diff = abs(predicted - correct)
    if diff == 0:
        return 1.0, f"Correct! NEWS2 score is {correct}."
    elif diff == 1:
        return 0.7, f"Close. You scored {predicted}, correct is {correct} (±1)."
    elif diff == 2:
        return 0.4, f"Partial. You scored {predicted}, correct is {correct} (±2)."
    return 0.0, f"Incorrect. You scored {predicted}, correct is {correct}."


# ---------------------------------------------------------------------------
# Task 3 – Renal Dose Adjustment (Hard)
# ---------------------------------------------------------------------------
# The agent must determine appropriate antibiotic dosing adjustment
# based on eGFR and drug-specific rules.
#
# Rules (simplified, educational only):
#   Piperacillin-Tazobactam:  eGFR≥40→normal_dose, eGFR20-39→dose_75, eGFR<20→dose_50
#   Vancomycin:               eGFR≥50→normal_dose, eGFR30-49→dose_75, eGFR10-29→dose_50,
#                             eGFR<10→contraindicated (requires alternative/specialist)
#   Meropenem:                eGFR≥50→normal_dose, eGFR26-49→dose_75, eGFR10-25→dose_50,
#                             eGFR<10→contraindicated
#   Ciprofloxacin:            eGFR≥30→normal_dose, eGFR<30→dose_50
#   Metronidazole:            normal_dose (no renal adjustment needed)
#
# Possible answers: "normal_dose" | "dose_75" | "dose_50" | "contraindicated"

MEDICATION_DOSING_CASES: List[Dict[str, Any]] = [
    {
        "case_id": 0,
        "scenario": (
            "52-year-old male with community-acquired pneumonia. "
            "Prescribed Piperacillin-Tazobactam. Lab results available."
        ),
        "fields": {
            "drug": "Piperacillin-Tazobactam",
            "standard_dose": "4.5g IV q6h",
            "patient_weight_kg": 78,
            "serum_creatinine_umol_L": 88,
            "egfr_ml_min": 62,
            "age_years": 52,
            "dialysis": False,
        },
        # eGFR=62 ≥ 40 → normal_dose
        "answer": "normal_dose",
        "rule_applied": "eGFR >= 40: no adjustment required for Pip-Tazo.",
    },
    {
        "case_id": 1,
        "scenario": (
            "67-year-old female with MRSA bacteraemia. "
            "Vancomycin therapy planned. Labs show reduced kidney function."
        ),
        "fields": {
            "drug": "Vancomycin",
            "standard_dose": "25mg/kg IV loading then 15mg/kg q12h",
            "patient_weight_kg": 62,
            "serum_creatinine_umol_L": 210,
            "egfr_ml_min": 22,
            "age_years": 67,
            "dialysis": False,
        },
        # eGFR=22, range 10-29 → dose_50
        "answer": "dose_50",
        "rule_applied": "Vancomycin: eGFR 10-29 => 50% dose reduction (extend interval).",
    },
    {
        "case_id": 2,
        "scenario": (
            "44-year-old male with intra-abdominal sepsis, on Meropenem. "
            "Near-normal renal function."
        ),
        "fields": {
            "drug": "Meropenem",
            "standard_dose": "1g IV q8h",
            "patient_weight_kg": 85,
            "serum_creatinine_umol_L": 95,
            "egfr_ml_min": 58,
            "age_years": 44,
            "dialysis": False,
        },
        # eGFR=58 ≥ 50 → normal_dose
        "answer": "normal_dose",
        "rule_applied": "Meropenem: eGFR >= 50, no adjustment.",
    },
    {
        "case_id": 3,
        "scenario": (
            "79-year-old female with end-stage renal disease (on haemodialysis) "
            "presenting with Gram-negative UTI. Ciprofloxacin considered."
        ),
        "fields": {
            "drug": "Ciprofloxacin",
            "standard_dose": "400mg IV q12h",
            "patient_weight_kg": 55,
            "serum_creatinine_umol_L": 680,
            "egfr_ml_min": 6,
            "age_years": 79,
            "dialysis": True,
        },
        # eGFR=6 < 30 → dose_50
        "answer": "dose_50",
        "rule_applied": "Ciprofloxacin: eGFR < 30 => 50% dose reduction.",
    },
    {
        "case_id": 4,
        "scenario": (
            "33-year-old male with Clostridium difficile colitis. "
            "Metronidazole prescribed. Labs normal."
        ),
        "fields": {
            "drug": "Metronidazole",
            "standard_dose": "500mg PO/IV q8h",
            "patient_weight_kg": 80,
            "serum_creatinine_umol_L": 75,
            "egfr_ml_min": 90,
            "age_years": 33,
            "dialysis": False,
        },
        # Metronidazole: no renal adjustment → normal_dose
        "answer": "normal_dose",
        "rule_applied": "Metronidazole does not require renal dose adjustment.",
    },
]

VALID_DOSING_ANSWERS = ["normal_dose", "dose_75", "dose_50", "contraindicated"]


def grade_medication_dosing(answer: str, case: Dict[str, Any]) -> Tuple[float, str]:
    """Return (score 0.0-1.0, feedback)."""
    correct = case["answer"]
    norm = answer.strip().lower().replace("-", "_")
    if norm == correct:
        return 1.0, f"Correct! {case['rule_applied']}"
    if norm not in VALID_DOSING_ANSWERS:
        return 0.0, (
            f"Invalid answer '{answer}'. "
            f"Choose from: {', '.join(VALID_DOSING_ANSWERS)}."
        )
    # adjacent partial credit (off-by-one level)
    order = ["normal_dose", "dose_75", "dose_50", "contraindicated"]
    if correct in order and norm in order:
        diff = abs(order.index(norm) - order.index(correct))
        if diff == 1:
            return 0.3, (
                f"Partially correct. You chose '{norm}', correct is '{correct}'. "
                f"Hint: {case['rule_applied']}"
            )
    return 0.0, (
        f"Incorrect. You chose '{norm}', correct is '{correct}'. "
        f"Hint: {case['rule_applied']}"
    )


# ---------------------------------------------------------------------------
# Unified task registry
# ---------------------------------------------------------------------------

TASK_REGISTRY = {
    "vital_triage": {
        "difficulty": "easy",
        "description": (
            "Assess the patient's vital signs and determine the triage category. "
            "Query individual vital fields, then submit one of: "
            "'stable', 'concerning', or 'critical'."
        ),
        "cases": VITAL_TRIAGE_CASES,
        "valid_answers": ["stable", "concerning", "critical"],
        "grader": grade_vital_triage,
        "max_steps": 10,
    },
    "news2_score": {
        "difficulty": "medium",
        "description": (
            "Calculate the National Early Warning Score 2 (NEWS2) for the patient. "
            "Query all relevant vital fields, compute each component score, "
            "then submit the total as an integer string (e.g. '7')."
        ),
        "cases": NEWS2_CASES,
        "valid_answers": None,  # any integer string
        "grader": grade_news2,
        "max_steps": 14,
    },
    "medication_dosing": {
        "difficulty": "hard",
        "description": (
            "Determine the appropriate renal dose adjustment for the prescribed antibiotic. "
            "Query eGFR, drug name, and any other relevant fields, "
            "then submit one of: 'normal_dose', 'dose_75', 'dose_50', 'contraindicated'."
        ),
        "cases": MEDICATION_DOSING_CASES,
        "valid_answers": VALID_DOSING_ANSWERS,
        "grader": grade_medication_dosing,
        "max_steps": 14,
    },
}

# Cycle order for deterministic task rotation across episodes
TASK_CYCLE = ["vital_triage", "news2_score", "medication_dosing"]
