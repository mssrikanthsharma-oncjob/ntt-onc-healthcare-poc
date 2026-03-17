# Healthcare AI POC — Status

## What's Running Now

### Backend (FastAPI :8000)
| Feature | Status |
|---|---|
| `GET /health` | ✅ Running |
| `GET /patients` | ✅ Running — returns P001, P002, P003 |
| `POST /chat` | ✅ Running — fresh supervisor per request (history bug fixed) |
| `POST /upload` | ✅ Running — uploads to S3 + triggers KB sync |
| `GET /upload/status/{job_id}` | ✅ Running — checks KB ingestion job status |
| Clinical Agent (EHR via MCP + Lab tools) | ✅ Running |
| Billing Agent (Insurance tool) | ✅ Running |
| Scheduler Agent (LLM-only) | ✅ Running |
| RAG Agent | ✅ Running — Bedrock KB via `retrieve` tool (Pinecone vector store) |
| EHR lookup | ✅ MCP — served via `mcp_ehr_server.py` (FastMCP/stdio) |
| Lab results tool | ✅ Running — P001, P002, P003 data in `tools.py` |
| Drug lookup | ✅ Bedrock KB — `retrieve` tool queries KB ID `PW6TRBORQW` |
| Insurance check tool | ✅ Running — hardcoded mock data |
| Amazon Bedrock (Claude 3.5 Haiku) | ✅ Running — live LLM inference |

### Frontend (React Vite :5173)
| Feature | Status |
|---|---|
| Patient sidebar with status dots | ✅ Running |
| Click to switch patients (P001, P002, P003) | ✅ Running |
| Chat panel with message bubbles | ✅ Running |
| Loading animation (bouncing dots) | ✅ Running |
| Quick query buttons (6) | ✅ Running — Clinical Summary, Lab Results, Check Medications, Insurance Status, Next Follow Up, Reminders |
| Bedrock · Claude badge | ✅ Running |
| Knowledge Base upload section | ✅ Running — uploads to S3 + triggers KB sync |

---

## Known Issues Fixed

| Issue | Fix |
|---|---|
| Agent not calling tools | Sub-agents wrapped as top-level `@tool` functions with unique names |
| Claude Sonnet Legacy error | Switched to `claude-3-5-haiku-20241022-v1:0` |
| Conversation history corruption (500 error after several messages) | Fresh `Agent` instance created per request in `run_agent()` |
| `ehr_lookup` tool name collision | Moved to MCP server (`mcp_ehr_server.py`); `tools.py` version commented out |
| `AmazonKnowledgeBasesTool` import error | Replaced with `retrieve` from `strands_tools` (correct tool for strands-agents v1.20) |

---

## Pending

| Feature | Notes |
|---|---|
| Deployment | Dockerfile + AgentCore handler — not yet implemented |

---

## Skipped (Optional Tasks)

| Feature | Reason |
|---|---|
| Unit tests for tools | Optional — skipped for faster MVP |
| Property-based tests (Hypothesis) | Optional — skipped for faster MVP |
| Unit tests for API endpoints | Optional — skipped for faster MVP |

---

## Data Locations

| Data | Location |
|---|---|
| EHR records (P001, P002, P003) | `backend/mcp_ehr_server.py` — served via MCP |
| Lab results (P001, P002, P003) | `backend/tools.py` — `lab_results` tool |
| Drug/protocol info | Bedrock KB (Pinecone) — queried via `retrieve` tool |
| Insurance data | `backend/tools.py` — `insurance_check` tool (hardcoded) |
| Uploaded documents | S3 bucket `healthcare-poc-kb-docs` → synced to Bedrock KB |

---

## Run Order
```bash
# Terminal 1 — MCP EHR server (must start first)
cd healthcare-poc/backend && python mcp_ehr_server.py

# Terminal 2 — FastAPI backend
cd healthcare-poc/backend && uvicorn main:app --reload --port 8000

# Terminal 3 — React frontend
cd healthcare-poc/frontend && npm run dev
```
