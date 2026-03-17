import os
from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
#from tools import lab_results, drug_lookup, insurance_check
from tools import lab_results, insurance_check

# ehr_lookup removed — now served via MCP server (mcp_ehr_server.py)


def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


# --- Lazy initialization ---
# All sub-agents are created on first call to run_agent(), not at import time.
# This ensures AgentCore runtime starts within the 30s initialization window.

_initialized = False
_clinical_agent = None
_billing_agent = None
_scheduler_agent = None
_rag_agent = None


def _init_agents():
    """Initialize MCP client and all sub-agents. Called once on first request."""
    global _initialized, _clinical_agent, _billing_agent, _scheduler_agent, _rag_agent

    if _initialized:
        return

    from strands_tools.retrieve import retrieve

    # EHR tool via MCP server (spawned as subprocess)
    ehr_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command="python", args=["mcp_ehr_server.py"])
        )
    )
    ehr_mcp_client.__enter__()
    ehr_tools = ehr_mcp_client.list_tools_sync()

    _clinical_agent = Agent(
        model=_make_model(),
        tools=[*ehr_tools, lab_results],
        system_prompt=(
            "You are a clinical AI assistant. When asked for a clinical summary, "
            "call ehr_lookup AND lab_results for the patient, then output ALL data in this exact format:\n\n"
            "Patient: [name], [age]y\n"
            "Condition: [condition]\n"
            "Last Visit: [date]\n"
            "Vitals: BP [bp], SpO2 [spo2], HR [hr]\n"
            "Medications: [list each medication]\n"
            "Lab Results: [list each lab value with units]\n\n"
            "Show every field and value exactly as returned by the tools. Do not omit anything."
        ),
    )

    _billing_agent = Agent(
        model=_make_model(),
        tools=[insurance_check],
        system_prompt=(
            "You are a healthcare billing assistant. Use the insurance_check tool to verify "
            "patient insurance details. Present ALL fields in this format:\n\n"
            "Patient ID: [id]\n"
            "Payer: [payer]\n"
            "Eligible: [yes/no]\n"
            "Pre-Auth Required: [yes/no]\n"
            "Deductible Met: [yes/no]\n"
            "Copay: [amount]\n"
            "Procedure Code: [code]\n\n"
            "Show every field exactly as returned. Do not omit anything."
        ),
    )

    _scheduler_agent = Agent(
        model=_make_model(),
        tools=[],
        system_prompt=(
            "You are a healthcare scheduling assistant. Based on the patient context provided, "
            "give specific actionable recommendations in this format:\n\n"
            "Next Follow-Up: [recommended date/timeframe and reason]\n"
            "Reminders:\n"
            "- [reminder 1]\n"
            "- [reminder 2]\n"
            "- [reminder 3]\n\n"
            "Be specific — include timeframes, medication reminders, and monitoring tasks "
            "based on the patient's condition."
        ),
    )

    # NOTE: drug_lookup (hardcoded) version commented out — using Bedrock KB via retrieve
    # _rag_agent = Agent(
    #     model=_make_model(),
    #     tools=[drug_lookup],
    #     system_prompt=("You are a clinical pharmacology assistant..."),
    # )

    _rag_agent = Agent(
        model=_make_model(),
        tools=[retrieve],
        system_prompt=(
            "You are a clinical pharmacology assistant. Use the retrieve tool to search the "
            "knowledge base for drug information. "
            f"Always call retrieve with knowledgeBaseId='{os.getenv('BEDROCK_KB_ID')}' "
            f"and region='{os.getenv('AWS_REGION', 'us-east-1')}'. "
            "Present results in this format:\n\n"
            "Drug: [name]\n"
            "Formulary Tier: [tier]\n"
            "Generic Available: [yes/no]\n"
            "Covered: [yes/no]\n"
            "Interactions: [list interactions or 'None']\n\n"
            "If multiple drugs are involved, list each one separately. Show all retrieved data."
        ),
    )

    _initialized = True


# --- Wrap sub-agents as @tool functions for the supervisor ---

@tool
def clinical_agent(query: str) -> str:
    """Handle clinical queries: patient EHR records, lab results, clinical summaries, diagnoses. Pass the full query including patient_id."""
    return str(_clinical_agent(query))


@tool
def billing_agent(query: str) -> str:
    """Handle billing queries: insurance eligibility, pre-authorization, claims, copay. Pass the full query including patient_id."""
    return str(_billing_agent(query))


@tool
def scheduler_agent(query: str) -> str:
    """Handle scheduling queries: appointments, follow-ups, reminders. Pass the full query including patient_id."""
    return str(_scheduler_agent(query))


@tool
def rag_agent(query: str) -> str:
    """Handle drug and protocol queries: drug interactions, formulary lookups, clinical guidelines. Pass the drug name or query."""
    return str(_rag_agent(query))


# --- Supervisor ---

# Singleton supervisor commented out — causes history corruption across requests.
# After several messages, toolResult/toolUse counts mismatch and Bedrock raises:
# "The number of toolResult blocks exceeds the number of toolUse blocks"
# Fix: create a fresh Agent per request in run_agent() below.
#
# _supervisor = Agent(
#     model=_make_model(),
#     tools=[clinical_agent, billing_agent, scheduler_agent, rag_agent],
#     system_prompt=(...),
# )
#
# def run_agent(message: str, patient_id: str) -> str:
#     full_message = f"[Patient ID: {patient_id}] {message}"
#     result = _supervisor(full_message)
#     return str(result)


_SUPERVISOR_PROMPT = (
    "You are a healthcare AI supervisor. Route each query to the correct specialist tool.\n\n"
    "Routing rules:\n"
    "- clinical_agent: EHR records, lab results, clinical summaries, vitals, medications\n"
    "- billing_agent: insurance, claims, pre-authorization, copay\n"
    "- scheduler_agent: appointments, follow-ups, reminders\n"
    "- rag_agent: drug interactions, formulary, clinical protocols\n\n"
    "Call the appropriate tool and present its full response to the user."
)


def run_agent(message: str, patient_id: str) -> str:
    """Create a fresh supervisor per request to avoid conversation history corruption.

    Sub-agents are lazily initialized on first call via _init_agents().
    Only the supervisor is created fresh each request to avoid history buildup.
    """
    _init_agents()

    supervisor = Agent(
        model=_make_model(),
        tools=[clinical_agent, billing_agent, scheduler_agent, rag_agent],
        system_prompt=_SUPERVISOR_PROMPT,
    )
    full_message = f"[Patient ID: {patient_id}] {message}"
    result = supervisor(full_message)

    # Extract text from result — handle both string and AgentResult objects
    text = str(result)
    if not text or text.strip() in ("", "None"):
        # Fallback: try to get the last message content directly
        try:
            text = result.message["content"][0]["text"]
        except Exception:
            text = "No response generated."
    return text
