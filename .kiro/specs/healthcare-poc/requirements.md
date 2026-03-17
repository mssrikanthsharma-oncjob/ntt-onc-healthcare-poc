# Requirements Document

## Introduction

A Healthcare AI Proof-of-Concept (POC) application demonstrating a multi-agent AI system for healthcare workflows. The system consists of a Python FastAPI backend powered by AWS Strands agents connected to Amazon Bedrock (Claude 3.5 Sonnet), and a React (Vite) frontend. The POC showcases a supervisor agent routing queries to four specialized sub-agents (clinical, billing, scheduler, RAG) that use mock MCP tools to simulate real healthcare data integrations.

## Glossary

- **System**: The complete Healthcare AI POC application (backend + frontend)
- **Backend**: The Python FastAPI application serving REST endpoints
- **Frontend**: The React (Vite) single-page application
- **Supervisor_Agent**: The top-level Strands agent that routes user queries to appropriate sub-agents
- **Clinical_Agent**: A Strands sub-agent handling clinical queries using EHR and lab tools
- **Billing_Agent**: A Strands sub-agent handling billing and insurance queries
- **Scheduler_Agent**: A Strands sub-agent handling appointment and reminder queries
- **RAG_Agent**: A Strands sub-agent handling drug and protocol knowledge base queries
- **EHR_Tool**: A mock Strands tool returning hardcoded patient electronic health records
- **Lab_Tool**: A mock Strands tool returning hardcoded patient lab results
- **Drug_Tool**: A mock Strands tool returning hardcoded drug interaction and formulary data
- **Insurance_Tool**: A mock Strands tool returning hardcoded insurance eligibility data
- **Patient**: A mock patient record identified by a patient ID (P001 or P002)
- **Chat_Panel**: The right-side UI component where users send messages and view agent responses
- **Patient_Sidebar**: The left-side UI component listing available patients

## Requirements

### Requirement 1: Backend API Endpoints

**User Story:** As a frontend developer, I want a FastAPI backend with well-defined REST endpoints, so that the frontend can communicate with the AI agent system.

#### Acceptance Criteria

1. THE Backend SHALL expose a POST `/chat` endpoint that accepts a JSON body with `message` (string) and `patient_id` (string) fields and returns a JSON response with a `reply` (string) field.
2. THE Backend SHALL expose a GET `/patients` endpoint that returns a JSON list of the two mock patients (P001 and P002) with their names and IDs.
3. THE Backend SHALL expose a GET `/health` endpoint that returns a JSON response with status `ok`.
4. THE Backend SHALL enable CORS for `http://localhost:5173` to allow the React frontend to make cross-origin requests.
5. WHEN the `/chat` endpoint receives a request, THE Backend SHALL invoke the Supervisor_Agent with the provided message and patient_id and return the agent's response as the `reply` field.

### Requirement 2: Mock MCP Tools

**User Story:** As a developer, I want four mock Strands tools with hardcoded data, so that the agents can simulate real healthcare data lookups without requiring live integrations.

#### Acceptance Criteria

1. THE EHR_Tool SHALL accept a `patient_id` string parameter and return a dictionary containing name, age, condition, medications, last_visit, and vitals for patients P001 and P002.
2. IF an unknown patient_id is provided to the EHR_Tool, THEN THE EHR_Tool SHALL return a dictionary with an `error` key set to "Patient not found".
3. THE Lab_Tool SHALL accept a `patient_id` string parameter and return a dictionary of lab result key-value pairs for patients P001 and P002.
4. IF an unknown patient_id is provided to the Lab_Tool, THEN THE Lab_Tool SHALL return a dictionary with an `error` key set to "No labs found".
5. THE Drug_Tool SHALL accept a `drug_name` string parameter and return a dictionary containing interactions, formulary_tier, generic_available, and covered fields.
6. THE Insurance_Tool SHALL accept a `patient_id` string and an optional `procedure_code` string (defaulting to "99213") and return a dictionary containing patient_id, payer, eligible, pre_auth_required, deductible_met, copay, and procedure_code fields.
7. WHEN the Drug_Tool receives a drug_name not in its hardcoded list, THE Drug_Tool SHALL return a default dictionary with empty interactions, formulary_tier 2, generic_available False, and covered True.

### Requirement 3: Multi-Agent Architecture

**User Story:** As a product stakeholder, I want a Strands multi-agent system with a supervisor routing to specialized sub-agents, so that different types of healthcare queries are handled by the most appropriate agent.

#### Acceptance Criteria

1. THE System SHALL use Amazon Bedrock with model ID `us.anthropic.claude-3-5-sonnet-20241022-v2:0` as the LLM for all agents.
2. THE Clinical_Agent SHALL be configured with the EHR_Tool and Lab_Tool and a system prompt focused on clinical data retrieval and summarization.
3. THE Billing_Agent SHALL be configured with the Insurance_Tool and a system prompt focused on billing, claims, and insurance eligibility.
4. THE Scheduler_Agent SHALL be configured with a system prompt focused on appointment scheduling and reminders (no external tools required for POC).
5. THE RAG_Agent SHALL be configured with the Drug_Tool and a system prompt focused on drug interactions and clinical protocol lookups.
6. THE Supervisor_Agent SHALL be configured with the four sub-agents as tools and a system prompt that routes queries to the appropriate sub-agent based on query type.
7. WHEN the Supervisor_Agent receives a query with a patient_id, THE Supervisor_Agent SHALL include the patient_id in its context when delegating to sub-agents.

### Requirement 4: Frontend Patient Sidebar

**User Story:** As a clinician, I want a patient sidebar listing available patients, so that I can select a patient and have all subsequent queries scoped to that patient's data.

#### Acceptance Criteria

1. THE Patient_Sidebar SHALL display a list of patients fetched from the GET `/patients` backend endpoint on application load.
2. WHEN a patient is selected in the Patient_Sidebar, THE Frontend SHALL set that patient as the active patient for all subsequent chat messages.
3. THE Patient_Sidebar SHALL display a colored status indicator dot next to each patient name.
4. THE Patient_Sidebar SHALL visually distinguish the currently selected patient from unselected patients.
5. THE Frontend SHALL display quick query buttons ("Clinical summary", "Show lab results", "Check medications", "Insurance status") that, WHEN clicked, SHALL send the corresponding query text as a chat message for the selected patient.

### Requirement 5: Frontend Chat Panel

**User Story:** As a clinician, I want a chat interface to send natural language queries and receive AI agent responses, so that I can quickly access patient information through conversation.

#### Acceptance Criteria

1. THE Chat_Panel SHALL display a header showing the currently selected patient's name and a "Bedrock · Claude" badge.
2. THE Chat_Panel SHALL render user messages in purple-styled message bubbles and agent responses in light gray-styled message bubbles.
3. WHEN a user submits a message by pressing Enter or clicking a send button, THE Frontend SHALL call the POST `/chat` endpoint with the message text and the selected patient's ID.
4. WHILE a chat response is pending, THE Chat_Panel SHALL display a loading animation consisting of three bouncing dots.
5. WHEN a response is received from the backend, THE Chat_Panel SHALL append the agent's reply as a new message bubble and remove the loading animation.
6. WHEN a new message is added to the chat, THE Chat_Panel SHALL scroll to show the latest message.

### Requirement 6: Frontend API Integration

**User Story:** As a frontend developer, I want a dedicated API module, so that all backend communication is centralized and easy to maintain.

#### Acceptance Criteria

1. THE Frontend SHALL contain an `api.js` module that exports a `getPatients` function calling GET `http://localhost:8000/patients`.
2. THE Frontend SHALL contain an `api.js` module that exports a `sendMessage` function calling POST `http://localhost:8000/chat` with `message` and `patient_id` in the request body as JSON.
3. WHEN the `sendMessage` function is called, THE Frontend SHALL set the `Content-Type` header to `application/json`.

### Requirement 7: Project Configuration and Setup

**User Story:** As a developer, I want a well-structured project with clear dependency management, so that the POC can be set up and run quickly.

#### Acceptance Criteria

1. THE Backend SHALL declare its Python dependencies in a `requirements.txt` file including fastapi, uvicorn, strands-agents, strands-agents-tools, boto3, and python-dotenv at the specified versions.
2. THE Backend SHALL read the `AWS_REGION` configuration from a `.env` file using python-dotenv.
3. THE Frontend SHALL be scaffolded as a React Vite project with `App.jsx`, `api.js`, and `App.css` as the primary source files.
4. THE System SHALL use AWS credentials from `~/.aws/credentials` automatically via the boto3 default credential chain, with no hardcoded credentials in source code.
