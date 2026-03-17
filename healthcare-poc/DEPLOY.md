# Healthcare AI POC — Deployment Guide (AgentCore Starter Toolkit)

## Architecture

```
Browser → Vercel (React frontend)
              ↓ HTTPS InvokeAgentRuntime
    AWS Bedrock AgentCore Runtime
              ↓ subprocess stdio
         mcp_ehr_server.py (same runtime)
              ↓ boto3
    Amazon Bedrock (Claude 3.5 Haiku) + Bedrock KB (Pinecone)
              ↓
    S3 (uploaded documents)
```

---

## What's Already Done (code is ready)

| Item | File | Status |
|---|---|---|
| AgentCore handler | `backend/agentcore_handler.py` | ✅ Done |
| `/invocations` + `/ping` endpoints | `backend/main.py` | ✅ Done (for Docker path) |
| Dockerfile | `backend/Dockerfile` | ✅ Done (for Docker path) |
| Updated requirements.txt | `backend/requirements.txt` | ✅ Done — boto3>=1.42 |
| Frontend env var | `frontend/src/api.js` | ✅ Done — uses `VITE_API_URL` |

---

## Prerequisites

```bash
# Upgrade pip and install AgentCore toolkit
pip install --upgrade pip
pip install bedrock-agentcore bedrock-agentcore-starter-toolkit

# Verify
agentcore --version
```

Also update your local boto3:
```bash
pip install "boto3>=1.42" "botocore>=1.35"
```

---

## Step 1: Install updated dependencies

```bash
cd healthcare-poc/backend
pip install -r requirements.txt
```

---

## Step 2: Test locally first

```bash
# Terminal 1 — MCP server (required before handler starts)
cd healthcare-poc/backend
python mcp_ehr_server.py

# Terminal 2 — Launch handler locally on port 8080
cd healthcare-poc/backend
agentcore launch -e agentcore_handler.py

# Terminal 3 — Test it
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"message": "Clinical Summary", "patient_id": "P001"}'
```

Expected response: `{"reply": "..."}`

---

## Step 3: Configure for deployment

```bash
cd healthcare-poc/backend

# Configure — uses direct_code_deploy (no Docker needed), deploys to us-east-1
agentcore configure -e agentcore_handler.py -r us-east-1 --disable-memory
```

This creates a `.bedrock_agentcore.yaml` file in the backend directory.
Use default values when prompted.

---

## Step 4: Deploy to AgentCore Runtime

```bash
cd healthcare-poc/backend
agentcore deploy
```

The toolkit will:
- Package your code
- Upload to S3
- Create the IAM execution role automatically
- Deploy to AgentCore Runtime via CodeBuild (no Docker needed locally)

Note the **Agent ARN** and **endpoint** from the output.

---

## Step 5: Check deployment status

```bash
agentcore status
```

Wait until status shows as active before invoking.

---

## Step 6: Test the deployed agent

```bash
# Using the agentcore CLI
agentcore invoke --payload '{"message": "Clinical Summary", "patient_id": "P001"}'

# Or using boto3 directly (replace ARN with your agent ARN from Step 4)
python - <<'EOF'
import boto3, json

client = boto3.client("bedrock-agentcore", region_name="us-east-1")
response = client.invoke_agent_runtime(
    agentRuntimeArn="<your-agent-arn>",
    payload=json.dumps({"message": "Clinical Summary", "patient_id": "P001"}).encode()
)
print(json.loads(response["response"].read()))
EOF
```

---

## Step 7: Deploy frontend to Vercel

```bash
npm install -g vercel
cd healthcare-poc/frontend
vercel

# Set the AgentCore endpoint as the backend URL
vercel env add VITE_API_URL production
# Enter the AgentCore endpoint from Step 4

vercel --prod
```

---

## Step 8: Update CORS for Vercel domain

Once you have the Vercel URL, update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-app.vercel.app",   # add your Vercel URL here
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy: `agentcore deploy`

---

## Updating after code changes

```bash
cd healthcare-poc/backend
agentcore deploy   # re-packages and redeploys automatically
```

---

## Notes

- Default deploy mode uses **direct_code_deploy** — no Docker required locally
- AWS CodeBuild handles the container build in the cloud (ARM64/Graviton)
- Do NOT set `AWS_PROFILE` in production — AgentCore uses the IAM execution role
- `mcp_ehr_server.py` spawns as a subprocess via stdio inside the runtime
- All existing local endpoints (`/chat`, `/patients`, `/upload`) still work for local dev
- AgentCore provides CloudWatch logging automatically — check `/aws/bedrock-agentcore/runtimes/`
- The old `deploy_agentcore.py` (manual boto3 approach) is kept for reference but the toolkit is the recommended path

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Unknown service: bedrock-agentcore-control` | `pip install "boto3>=1.42"` |
| `Docker not found` | Safe to ignore — default mode doesn't need Docker |
| `Model access denied` | Enable Claude 3.5 Haiku in Bedrock console for us-east-1 |
| `Port 8080 in use` | `lsof -ti:8080 \| xargs kill -9` |
| Memory provisioning in progress | Wait 2-5 min, run `agentcore status` |
