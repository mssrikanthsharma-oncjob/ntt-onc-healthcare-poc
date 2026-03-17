import os
from dotenv import load_dotenv

# Must load .env BEFORE importing agent, so AWS_PROFILE is set before boto3 initializes
load_dotenv(override=True)

import boto3
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="Healthcare AI POC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PATIENTS = [
    {"id": "P001", "name": "Priya Nair", "age": 42, "condition": "Type 2 Diabetes", "status": "monitoring"},
    {"id": "P002", "name": "Arjun Mehta", "age": 67, "condition": "Post-CABG", "status": "critical"},
    {"id": "P003", "name": "Ravi Shankar", "age": 55, "condition": "Hypertension", "status": "stable"},
]


class ChatRequest(BaseModel):
    message: str
    patient_id: str = "P001"


# AgentCore Docker path models — kept for reference if Docker deployment is needed later
# class InvocationRequest(BaseModel):
#     input: dict


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/patients")
def list_patients():
    return {"patients": PATIENTS}


@app.post("/chat")
def chat(req: ChatRequest):
    reply = run_agent(req.message, req.patient_id)
    return {"reply": reply}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document to S3. KB sync is disabled until KB is configured."""
    bucket = os.getenv("S3_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not bucket:
        raise HTTPException(status_code=500, detail="S3_BUCKET not configured in .env")

    try:
        # Upload file to S3
        s3 = boto3.client("s3", region_name=region)
        contents = await file.read()
        s3.put_object(Bucket=bucket, Key=file.filename, Body=contents)

        # KB sync disabled — uncomment when Bedrock KB is configured
        kb_id = os.getenv("BEDROCK_KB_ID")
        ds_id = os.getenv("BEDROCK_KB_DATASOURCE_ID")
        bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        job = bedrock_agent.start_ingestion_job(
             knowledgeBaseId=kb_id,
             dataSourceId=ds_id,
        )
        job_id = job["ingestionJob"]["ingestionJobId"]

        return {
            "status": "uploaded",
            "filename": file.filename,
            "s3_key": file.filename,
            "job_id":job_id,
            "message": f"{file.filename} uploaded to S3 successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AgentCore Docker path endpoints — kept commented for reference
# The starter toolkit uses agentcore_handler.py directly, not these endpoints.
#
# @app.get("/ping")
# def ping():
#     """AgentCore health check endpoint."""
#     return {"status": "healthy"}
#
# @app.post("/invocations")
# def invocations(req: InvocationRequest):
#     """AgentCore entry point."""
#     message = req.input.get("message", "")
#     patient_id = req.input.get("patient_id", "P001")
#     if not message:
#         raise HTTPException(status_code=400, detail="message is required in input")
#     reply = run_agent(message, patient_id)
#     return {"output": {"reply": reply}}


@app.get("/upload/status/{job_id}")
def upload_status(job_id: str):
    """Check the status of a KB ingestion job."""
    kb_id = os.getenv("BEDROCK_KB_ID")
    ds_id = os.getenv("BEDROCK_KB_DATASOURCE_ID")
    region = os.getenv("AWS_REGION", "us-east-1")
    try:
        bedrock_agent = boto3.client("bedrock-agent", region_name=region)
        job = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            ingestionJobId=job_id,
        )
        return {"status": job["ingestionJob"]["status"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
