# Healthcare AI POC — Knowledge Document

---

## 1. Project Summary

A local proof-of-concept for a healthcare AI assistant. A clinician opens a React web app, selects a patient, and types natural language queries like "Clinical Summary" or "Check Medications". The message goes to a Python FastAPI backend, which passes it to an AWS Strands supervisor agent. The supervisor routes the query to one of four specialist sub-agents (clinical, billing, scheduler, RAG). Each sub-agent calls tools that return patient data, then Claude 3.5 Haiku (via Amazon Bedrock) formats the response and sends it back to the UI.

Three patients are supported: P001 Priya Nair (Diabetes), P002 Arjun Mehta (Post-CABG), P003 Ravi Shankar (Hypertension).

Tool architecture:
- EHR data → served via MCP (`mcp_ehr_server.py`)
- Lab/Insurance data → plain `@tool` functions in `tools.py`
- Drug/protocol data → Bedrock Knowledge Base (Pinecone vector store) via `retrieve` tool
- `ehr_lookup` and `drug_lookup` in `tools.py` are commented out (replaced by MCP and KB respectively)

Agent initialization:
- Sub-agents use **lazy initialization** — created on first request via `_init_agents()`, not at import time
- This ensures the AgentCore runtime starts within the 30s initialization window
- Only the supervisor is created fresh per request (to avoid history corruption); sub-agents are singletons

---

## 2. File Structure

```
healthcare-poc/
├── STATUS.md                    ← What's running vs pending
├── KNOWLEDGE.md                 ← This file
│
├── backend/
│   ├── main.py                  ← FastAPI app, REST endpoints
│   ├── agent.py                 ← Strands multi-agent system
│   ├── tools.py                 ← Active tools: lab_results, insurance_check
│   ├── mcp_ehr_server.py        ← MCP server for ehr_lookup (P001, P002, P003)
│   ├── test_mcp.py              ← Manual test script for MCP server
│   ├── requirements.txt         ← Python dependencies
│   └── .env                     ← AWS region, profile, S3 bucket, KB IDs
│
└── frontend/
    ├── index.html               ← HTML entry point
    ├── vite.config.js           ← Vite + React plugin config
    ├── package.json             ← Node dependencies and scripts
    └── src/
        ├── main.jsx             ← React app bootstrap
        ├── App.jsx              ← Main UI component (sidebar + chat panel)
        ├── App.css              ← All styles
        └── api.js               ← Backend API calls (getPatients, sendMessage, uploadDocument)
```

---

## 3. File-by-File Explanation

### backend/.env

```
AWS_REGION=us-east-1                        ← Bedrock region
AWS_PROFILE=default                         ← ~/.aws/credentials profile to use
S3_BUCKET=healthcare-poc-kb-docs            ← S3 bucket for document uploads
BEDROCK_KB_ID=PW6TRBORQW                   ← Bedrock KB ID (active)
BEDROCK_KB_DATASOURCE_ID=ULUY9TNTXP        ← KB data source ID (active)
```

---

### backend/requirements.txt

```
fastapi==0.115.0           ← REST API framework
uvicorn==0.30.6            ← ASGI server that runs FastAPI
strands-agents==1.20.0     ← AWS Strands SDK for building AI agents
strands-agents-tools==0.2.0← Extra tools including retrieve (KB), shell, etc.
boto3==1.35.0              ← AWS Python SDK (Bedrock + S3)
python-dotenv==1.0.1       ← Loads .env into environment variables
mcp>=1.0.0                 ← MCP protocol library (for MCPClient + FastMCP)
python-multipart==0.0.9    ← Required for FastAPI file upload (UploadFile)
```

---

### backend/mcp_ehr_server.py

Runs as a separate process before the FastAPI backend. Serves `ehr_lookup` over stdio MCP transport using `FastMCP`.

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("ehr-server")

@mcp.tool()
def ehr_lookup(patient_id: str) -> dict:
    # Returns full EHR record for P001, P002, P003
    # Unknown patient_id → {"error": "Patient not found"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
    # Communicates via stdin/stdout — agent.py spawns this as a subprocess
```

Patient records:
- P001 — Priya Nair, 42y, Type 2 Diabetes, Metformin 500mg + Amlodipine 5mg, BP 128/82
- P002 — Arjun Mehta, 67y, Post-CABG recovery, Aspirin 75mg + Atorvastatin 40mg, BP 135/88
- P003 — Ravi Shankar, 55y, Hypertension (Stage 2), Telmisartan 40mg + Amlodipine 5mg + Hydrochlorothiazide 12.5mg, BP 162/98

---

### backend/tools.py

Two active `@tool` functions. `ehr_lookup` and `drug_lookup` are commented out — replaced by MCP and Bedrock KB respectively.

```python
from strands import tool

# ehr_lookup — COMMENTED OUT (now served via mcp_ehr_server.py)

@tool
def lab_results(patient_id: str) -> dict:
    # P001: hba1c 7.2%, fasting_glucose 124 mg/dL, creatinine 0.9 mg/dL
    # P002: cholesterol 195, ldl 110, hdl 45
    # P003: sodium, potassium, creatinine, eGFR, cholesterol 210, ldl 135
    # Unknown → {"error": "No labs found"}

# drug_lookup — COMMENTED OUT (now served via Bedrock KB retrieve tool)

@tool
def insurance_check(patient_id: str, procedure_code: str = "99213") -> dict:
    # Returns same hardcoded response for ALL patients:
    # payer: Star Health, eligible: True, pre_auth_required: False,
    # deductible_met: True, copay: $20
```

---

### backend/agent.py

Strands multi-agent setup. Key design decisions:

**Lazy initialization:**
```python
_initialized = False
_clinical_agent = None
# ...

def _init_agents():
    """Called once on first request — not at import time."""
    global _initialized, _clinical_agent, ...
    if _initialized:
        return
    # MCP client + all sub-agents created here
    _initialized = True
```
Sub-agents are singletons created on first call. Only the supervisor is created fresh per request.

**MCP client lifecycle:**
```python
ehr_mcp_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(command="python", args=["mcp_ehr_server.py"]))
)
ehr_mcp_client.__enter__()   # Opens inside _init_agents()
ehr_tools = ehr_mcp_client.list_tools_sync()
# Connection stays open for the lifetime of the FastAPI process
```

**Model:**
```python
def _make_model() -> BedrockModel:
    return BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        # "us." prefix = cross-region inference profile (required)
        # Haiku used — Sonnet is Legacy in this AWS account
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
```

**Sub-agents:**

| Agent | Tools | Handles |
|---|---|---|
| `_clinical_agent` | `ehr_lookup` (MCP) + `lab_results` | EHR records, lab results, clinical summaries |
| `_billing_agent` | `insurance_check` | Insurance eligibility, copay, pre-auth |
| `_scheduler_agent` | _(none)_ | Appointments, follow-ups, reminders (LLM only) |
| `_rag_agent` | `retrieve` (Bedrock KB) | Drug interactions, formulary, clinical protocols |

Each sub-agent is wrapped as a `@tool`-decorated function so the supervisor can call them:
```python
@tool
def clinical_agent(query: str) -> str:
    """Handle clinical queries..."""
    return str(_clinical_agent(query))
```

**RAG agent uses Bedrock KB:**
```python
from strands_tools.retrieve import retrieve

_rag_agent = Agent(
    model=_make_model(),
    tools=[retrieve],
    system_prompt=(
        "...Always call retrieve with knowledgeBaseId='PW6TRBORQW' "
        "and region='us-east-1' before answering drug-related questions."
    ),
)
# retrieve tool accepts: text, knowledgeBaseId, region, numberOfResults, score
# KB ID and region are passed by the agent at call time via system prompt instruction
```

**Supervisor — fresh per request (history corruption fix):**
```python
_SUPERVISOR_PROMPT = "You are a healthcare AI supervisor. Route to correct tool..."

def run_agent(message: str, patient_id: str) -> str:
    _init_agents()  # lazy init sub-agents on first call
    # New Agent instance per request — prevents toolUse/toolResult history mismatch
    # Root cause: singleton accumulates history; Bedrock raises error after several messages
    supervisor = Agent(
        model=_make_model(),
        tools=[clinical_agent, billing_agent, scheduler_agent, rag_agent],
        system_prompt=_SUPERVISOR_PROMPT,
    )
    full_message = f"[Patient ID: {patient_id}] {message}"
    result = supervisor(full_message)
    # Handles both string and AgentResult objects; falls back to "No response generated."
    return str(result)
```

---

### backend/main.py

```python
load_dotenv(override=True)
# MUST run before "from agent import run_agent"
# agent.py imports boto3 at module level — boto3 reads AWS_PROFILE at init time

PATIENTS = [P001, P002, P003]

# Endpoints:
# GET  /health              → {"status": "ok"}
# GET  /patients            → {"patients": [...]}  ← wrapped object, NOT a bare list
# POST /chat                → {"reply": str}
# POST /upload              → uploads to S3 + triggers KB ingestion job
#                             returns: {status, filename, s3_key, job_id, message}
# GET  /upload/status/{id}  → checks Bedrock KB ingestion job status
```

CORS configured for `http://localhost:5173` only.

---

### frontend/src/api.js

```javascript
const BASE = "http://localhost:8000";

export async function getPatients()
// GET /patients → caller accesses .patients on the response

export async function sendMessage(message, patientId)
// POST /chat
// body: { message, patient_id: patientId }  ← snake_case for backend
// returns: { reply: "..." }

export async function uploadDocument(file)
// POST /upload with multipart FormData
// throws Error on non-ok response
// returns: { status, filename, s3_key, job_id, message }
```

---

### frontend/src/App.jsx

**Quick queries (6):**
```javascript
const QUICK_QUERIES = [
  "Clinical Summary", "Lab Results", "Check Medications",
  "Insurance Status", "Next Follow Up", "Reminders"
];
```

**Key behaviors:**
- On mount: fetches patients, auto-selects first
- On patient switch: resets chat with greeting message
- On send: appends user message → loading → calls `sendMessage` → appends agent reply
- On upload: calls `uploadDocument`, shows status in sidebar (Uploading... / ✓ uploaded / Upload failed)
- Auto-scroll: `bottomRef.current?.scrollIntoView()` on every messages/loading change

---

## 4. Data Flow (end to end)

```
User clicks "Check Medications" for P003
        ↓
App.jsx send("Check Medications")
        ↓
api.js POST /chat { message: "Check Medications", patient_id: "P003" }
        ↓
main.py → run_agent("Check Medications", "P003")
        ↓
agent.py: full_message = "[Patient ID: P003] Check Medications"
        ↓
fresh supervisor → Claude routes to rag_agent tool
        ↓
rag_agent → _rag_agent("[Patient ID: P003] Check Medications")
        ↓
_rag_agent calls retrieve(text="P003 medications", knowledgeBaseId="PW6TRBORQW", region="us-east-1")
  → Bedrock KB queries Pinecone vector store
  → returns relevant drug/protocol documents
        ↓
Claude formats response from KB results
        ↓
main.py returns { "reply": "Telmisartan interactions include..." }
        ↓
App.jsx appends agent message bubble
```

---

## 5. KB Upload Flow

```
User selects PDF in sidebar "Knowledge Base" section
        ↓
App.jsx handleUpload → api.js uploadDocument(file)
        ↓
POST /upload (multipart)
        ↓
main.py:
  1. s3.put_object → uploads file to s3://healthcare-poc-kb-docs/
  2. bedrock_agent.start_ingestion_job(KB_ID, DS_ID) → triggers KB sync
  3. returns { job_id: "..." }
        ↓
Bedrock reads from S3, chunks + embeds document, stores vectors in Pinecone
        ↓
Document is now searchable via retrieve tool
```

---

## 6. How to Run

```bash
# Terminal 1 — MCP EHR server (must start first)
cd healthcare-poc/backend
source venv/bin/activate
python mcp_ehr_server.py

# Terminal 2 — FastAPI backend
cd healthcare-poc/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 3 — React frontend
cd healthcare-poc/frontend
npm run dev
# Open http://localhost:5173
```

---

## 7. AWS Configuration

- Credentials: `~/.aws/credentials`, profile `default` (strands-bedrock user)
- Check active user: `aws sts get-caller-identity`
- Required permissions: `AmazonBedrockFullAccess` + `AmazonS3FullAccess`
- Model: `us.anthropic.claude-3-5-haiku-20241022-v1:0` in `us-east-1`
- S3 bucket: `healthcare-poc-kb-docs`
- Bedrock KB: `PW6TRBORQW` with Pinecone vector store
- Pinecone API key stored in AWS Secrets Manager as `pinecone-api-key`
