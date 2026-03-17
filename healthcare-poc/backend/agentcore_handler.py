"""
AgentCore Runtime entry point for the Healthcare AI POC.

Uses lazy initialization — agents are created on first invocation,
not at import time. This ensures the runtime starts within AgentCore's
30-second initialization window.
"""
import os
from dotenv import load_dotenv

# Load .env for local runs; AgentCore injects env vars directly in production
load_dotenv(override=True)

# Lazy singleton — initialized on first call
_run_agent = None


def _get_run_agent():
    """Import and initialize agent only on first call."""
    global _run_agent
    if _run_agent is None:
        from agent import run_agent
        _run_agent = run_agent
    return _run_agent


def handler(payload: dict, context=None) -> dict:
    """
    AgentCore Runtime handler.

    Expected input:
        {"message": "Clinical Summary", "patient_id": "P001"}

    Returns:
        {"reply": "..."}
    """
    message = payload.get("message", "")
    patient_id = payload.get("patient_id", "P001")

    if not message:
        return {"error": "message is required"}

    run_agent = _get_run_agent()
    reply = run_agent(message, patient_id)
    return {"reply": reply}
