"""
MCP server for EHR lookups.
Run this as a separate process before starting the FastAPI backend:
    python mcp_ehr_server.py
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ehr-server")


@mcp.tool()
def ehr_lookup(patient_id: str) -> dict:
    """Look up patient EHR record by patient ID."""
    records = {
        "P001": {
            "name": "Priya Nair",
            "age": 42,
            "condition": "Type 2 Diabetes",
            "medications": ["Metformin 500mg", "Amlodipine 5mg"],
            "last_visit": "2025-11-14",
            "vitals": {"bp": "128/82", "spo2": "97%", "hr": "74 bpm"},
        },
        "P002": {
            "name": "Arjun Mehta",
            "age": 67,
            "condition": "Post-CABG recovery",
            "medications": ["Aspirin 75mg", "Atorvastatin 40mg"],
            "last_visit": "2025-12-01",
            "vitals": {"bp": "135/88", "spo2": "95%", "hr": "68 bpm"},
        },
        "P003": {
            "name": "Ravi Shankar",
            "age": 55,
            "condition": "Hypertension (Stage 2)",
            "medications": ["Telmisartan 40mg", "Amlodipine 5mg", "Hydrochlorothiazide 12.5mg"],
            "last_visit": "2026-01-10",
            "vitals": {"bp": "162/98", "spo2": "96%", "hr": "82 bpm"},
        },
    }
    return records.get(patient_id, {"error": "Patient not found"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
