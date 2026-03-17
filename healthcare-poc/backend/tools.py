from strands import tool


# ehr_lookup commented out — now served via MCP server (mcp_ehr_server.py)
# Uncomment if you want to revert to plain tool (remove MCPClient from agent.py too).
#
# @tool
# def ehr_lookup(patient_id: str) -> dict:
#     """Look up patient EHR record by patient ID."""
#     records = {
#         "P001": {
#             "name": "Priya Nair",
#             "age": 42,
#             "condition": "Type 2 Diabetes",
#             "medications": ["Metformin 500mg", "Amlodipine 5mg"],
#             "last_visit": "2025-11-14",
#             "vitals": {"bp": "128/82", "spo2": "97%", "hr": "74 bpm"},
#         },
#         "P002": {
#             "name": "Arjun Mehta",
#             "age": 67,
#             "condition": "Post-CABG recovery",
#             "medications": ["Aspirin 75mg", "Atorvastatin 40mg"],
#             "last_visit": "2025-12-01",
#             "vitals": {"bp": "135/88", "spo2": "95%", "hr": "68 bpm"},
#         },
#     }
#     return records.get(patient_id, {"error": "Patient not found"})


@tool
def lab_results(patient_id: str) -> dict:
    """Fetch latest lab results for a patient."""
    labs = {
        "P001": {
            "hba1c": "7.2%",
            "fasting_glucose": "124 mg/dL",
            "creatinine": "0.9 mg/dL",
            "status": "resulted",
        },
        "P002": {
            "cholesterol": "195 mg/dL",
            "ldl": "110 mg/dL",
            "hdl": "45 mg/dL",
            "status": "resulted",
        },
        "P003": {
            "sodium": "138 mEq/L",
            "potassium": "3.9 mEq/L",
            "creatinine": "1.1 mg/dL",
            "egfr": "72 mL/min/1.73m²",
            "cholesterol": "210 mg/dL",
            "ldl": "135 mg/dL",
            "status": "resulted",
        },
    }
    return labs.get(patient_id, {"error": "No labs found"})


# drug_lookup commented out — replaced by Bedrock Knowledge Base (retrieve tool in agent.py)
# Uncomment and re-add to _rag_agent tools if you want to revert to hardcoded data.
#
# @tool
# def drug_lookup(drug_name: str) -> dict:
#     """Check drug interactions and formulary status."""
#     drugs = {
#         "metformin": {"interactions": [], "formulary_tier": 1, "generic_available": True, "covered": True},
#         "amlodipine": {"interactions": [], "formulary_tier": 1, "generic_available": True, "covered": True},
#         "telmisartan": {"interactions": ["potassium-sparing diuretics", "lithium", "NSAIDs"], "formulary_tier": 2, "generic_available": True, "covered": True},
#         "hydrochlorothiazide": {"interactions": ["lithium", "digoxin", "NSAIDs"], "formulary_tier": 1, "generic_available": True, "covered": True},
#         "aspirin": {"interactions": ["warfarin", "NSAIDs", "clopidogrel"], "formulary_tier": 1, "generic_available": True, "covered": True},
#         "atorvastatin": {"interactions": ["cyclosporine", "clarithromycin", "gemfibrozil"], "formulary_tier": 1, "generic_available": True, "covered": True},
#     }
#     return drugs.get(
#         drug_name.lower(),
#         {"interactions": [], "formulary_tier": 2, "generic_available": False, "covered": True},
#     )


@tool
def insurance_check(patient_id: str, procedure_code: str = "99213") -> dict:
    """Check insurance eligibility and pre-auth requirements."""
    return {
        "patient_id": patient_id,
        "payer": "Star Health",
        "eligible": True,
        "pre_auth_required": False,
        "deductible_met": True,
        "copay": "$20",
        "procedure_code": procedure_code,
    }
