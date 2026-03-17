# Implementation Plan: Healthcare AI POC

## Overview

Incremental implementation of the Healthcare AI POC. Start with the backend tools and API, wire up the Strands multi-agent system, then build the React frontend. Each step produces runnable, integrated code.

## Tasks

- [x] 1. Set up project structure and backend dependencies
  - Create `healthcare-poc/backend/` and `healthcare-poc/frontend/` directory layout
  - Create `backend/requirements.txt` with pinned versions: fastapi, uvicorn, strands-agents, strands-agents-tools, boto3, python-dotenv, mcp, python-multipart
  - Create `backend/.env` with `AWS_REGION`, `AWS_PROFILE`, `S3_BUCKET`, `BEDROCK_KB_ID`, `BEDROCK_KB_DATASOURCE_ID`
  - Scaffold the React Vite frontend project under `frontend/`
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 2. Implement mock MCP tools (`backend/tools.py`)
  - [x] 2.1 Implement `ehr_lookup` tool with hardcoded records for P001 (Priya Nair) and P002 (Arjun Mehta)
    - Note: `ehr_lookup` also exists in `mcp_ehr_server.py` as an MCP-served version; `tools.py` version kept for reference
    - _Requirements: 2.1, 2.2_
  - [x] 2.2 Implement `lab_results` tool with hardcoded lab data for P001, P002 and error fallback
    - _Requirements: 2.3, 2.4_
  - [x] 2.3 Add telmisartan, hydrochlorothiazide, and aspirin/atorvastatin entries to `drug_lookup` in `tools.py`
    - Added telmisartan, hydrochlorothiazide, aspirin, atorvastatin with interactions and formulary tiers
    - Also added P003 lab results (sodium, potassium, creatinine, eGFR, cholesterol, LDL) to `lab_results`
    - _Requirements: 2.5, 2.7_
  - [x] 2.4 Implement `insurance_check` tool with hardcoded eligibility response and optional `procedure_code` defaulting to "99213"
    - _Requirements: 2.6_
  - [ ]* 2.5 Write unit tests for all four tools
    - Test known patient lookups return expected data shapes
    - Test unknown patient/drug fallback behavior
    - _Requirements: 2.1–2.7_
  - [ ]* 2.6 Write property test for `ehr_lookup` unknown patient error (Property 2)
    - **Property 2: EHR unknown patient error**
    - **Validates: Requirements 2.2**
  - [ ]* 2.7 Write property test for `lab_results` unknown patient error (Property 3)
    - **Property 3: Lab unknown patient error**
    - **Validates: Requirements 2.4**
  - [ ]* 2.8 Write property test for `drug_lookup` always returns required fields (Property 4)
    - **Property 4: Drug lookup always returns required fields**
    - **Validates: Requirements 2.5, 2.7**
  - [ ]* 2.9 Write property test for `insurance_check` always returns required fields (Property 5)
    - **Property 5: Insurance check always returns required fields**
    - **Validates: Requirements 2.6**

- [x] 3. Implement MCP server for EHR tool (`backend/mcp_ehr_server.py`)
  - `ehr_lookup` served via `FastMCP` over stdio transport
  - Includes P001 (Priya Nair), P002 (Arjun Mehta), P003 (Ravi Shankar) records
  - Tested and verified working via `test_mcp.py`

- [x] 4. Implement Strands multi-agent system (`backend/agent.py`)
  - [x] 4.1 Configure `BedrockModel` with `us.anthropic.claude-3-5-haiku-20241022-v1:0`
    - Note: Sonnet is Legacy in this AWS account; Haiku used instead
    - _Requirements: 3.1, 7.2_
  - [x] 4.2 Create `clinical_agent` with MCP `ehr_lookup` (via `MCPClient`) + `lab_results` plain tool
    - MCP client opened once at startup, connection kept alive for process lifetime
    - _Requirements: 3.2_
  - [x] 4.3 Create `billing_agent` with `insurance_check` tool
    - _Requirements: 3.3_
  - [x] 4.4 Create `scheduler_agent` with no tools (LLM-only scheduling recommendations)
    - _Requirements: 3.4_
  - [x] 4.5 Create `rag_agent` with `drug_lookup` tool
    - KB integration commented in, ready to enable when Bedrock KB is configured
    - _Requirements: 3.5_
  - [x] 4.6 Create `supervisor_agent` wrapping four sub-agents as `@tool` decorated functions
    - Sub-agents wrapped as top-level `@tool` functions; `run_agent` prepends `[Patient ID: {patient_id}]` to message
    - _Requirements: 3.6, 3.7_
  - [x] 4.7 Fix conversation history corruption in `run_agent`
    - Root cause: singleton supervisor accumulates toolUse/toolResult pairs across requests; Bedrock raises mismatch error after several messages
    - Fix: create a fresh `Agent` instance per call in `run_agent()`; sub-agents remain singletons
    - Singleton `_supervisor` commented out for reference

- [x] 5. Implement FastAPI application (`backend/main.py`)
  - [x] 5.1 FastAPI app with CORS for `http://localhost:5173`
    - `load_dotenv(override=True)` called before agent import
    - _Requirements: 1.4_
  - [x] 5.2 GET `/health` returning `{"status": "ok"}`
    - _Requirements: 1.3_
  - [x] 5.3 GET `/patients` returning P001, P002, P003
    - Note: returns 3 patients (P003 added beyond original spec); response wrapped as `{"patients": [...]}` not a bare list
    - _Requirements: 1.2_
  - [x] 5.4 POST `/chat` calling `run_agent` and returning `{"reply": response}`
    - _Requirements: 1.1, 1.5_
  - [x] 5.5 POST `/upload` — uploads file to S
3 bucket; KB sync commented out pending Bedrock KB setup
  - [x] 5.6 GET `/upload/status/{job_id}` — checks KB ingestion job status (for future use)
  - [ ]* 5.7 Write unit tests for `/health` and `/patients` endpoints
    - _Requirements: 1.2, 1.3_

- [x] 6. Add third patient P003 — Ravi Shankar (Hypertension)
  - EHR: Stage 2 Hypertension, BP 162/98, on Telmisartan + Amlodipine + Hydrochlorothiazide (in `mcp_ehr_server.py`)
  - Labs: sodium, potassium, creatinine, eGFR, cholesterol, LDL (in `mcp_ehr_server.py`)
  - Added to `main.py` PATIENTS list
  - Note: P003 drug entries (telmisartan, hydrochlorothiazide) still missing from `tools.py` `drug_lookup` — see task 2.3

- [x] 7. Implement frontend API module (`frontend/src/api.js`)
  - `getPatients()` — GET `/patients`
  - `sendMessage(message, patientId)` — POST `/chat` with `Content-Type: application/json`
  - `uploadDocument(file)` — POST `/upload` with multipart form data
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 8. Implement frontend React application (`frontend/src/App.jsx` and `frontend/src/App.css`)
  - [x] 8.1 Two-panel layout: Patient_Sidebar + Chat_Panel
    - _Requirements: 4.1, 4.2_
  - [x] 8.2 Patient_Sidebar with status dots, click-to-select, quick query buttons
    - 6 quick queries: Clinical summary, Show lab results, Check medications, Insurance status, Next follow up, Reminders
    - _Requirements: 4.3, 4.4, 4.5_
  - [x] 8.3 Chat_Panel with header (patient name + Bedrock · Claude badge), message bubbles, loading animation, input bar
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  - [x] 8.4 Knowledge Base upload section at bottom of sidebar
    - File picker + upload button → calls `POST /upload`; shows uploading/success/error status
  - [x] 8.5 `App.css` with all styles including KB upload section

- [x] 9. Bedrock Knowledge Base integration
  - S3 bucket `healthcare-poc-kb-docs` created
  - Bedrock KB created in AWS Console with Pinecone as vector store; KB ID and datasource ID set in `.env`
  - `agent.py`: `drug_lookup` commented out; `retrieve` from `strands_tools` used instead; KB ID + region passed via system prompt
  - `main.py`: KB sync (`start_ingestion_job`) enabled in `/upload` endpoint
  - `tools.py`: `ehr_lookup` and `drug_lookup` both commented out (MCP and KB handle them respectively)
  - Pending: deploy (Task 10)

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- MCP server (`mcp_ehr_server.py`) must be running before starting the FastAPI backend
- Model changed from Claude 3.5 Sonnet to Claude 3.5 Haiku (Sonnet is Legacy in this AWS account)
- `load_dotenv(override=True)` must run before agent import so `AWS_PROFILE` is set before boto3 initializes
- AWS credentials: `strands-bedrock` user (default profile) with `AdministratorAccess` + `AmazonBedrockFullAccess`
- S3 permissions need to be attached to `strands-bedrock` user before upload works
- `/patients` response shape is `{"patients": [...]}` (not a bare list) — frontend must access `.patients`

## Run Order
```bash
# Terminal 1 — MCP EHR server
cd healthcare-poc/backend && python mcp_ehr_server.py

# Terminal 2 — FastAPI backend
cd healthcare-poc/backend && uvicorn main:app --reload --port 8000

# Terminal 3 — React frontend
cd healthcare-poc/frontend && npm run dev
```
