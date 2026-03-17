"""
Gradio frontend for Healthcare AI POC.
Runs alongside the existing React/FastAPI setup — does NOT replace it.

To run:
    cd healthcare-poc/backend
    source venv/bin/activate
    python gradio_app.py
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

import gradio as gr

_run_agent = None

def _get_run_agent():
    global _run_agent
    if _run_agent is None:
        from agent import run_agent
        _run_agent = run_agent
    return _run_agent


PATIENTS = {
    "P001 — Priya Nair (Type 2 Diabetes)": "P001",
    "P002 — Arjun Mehta (Post-CABG)": "P002",
    "P003 — Ravi Shankar (Hypertension)": "P003",
}

QUICK_QUERIES = [
    "Clinical Summary",
    "Lab Results",
    "Check Medications",
    "Insurance Status",
    "Next Follow Up",
    "Reminders",
]


def respond(message, history, patient_state):
    patient_id = PATIENTS.get(patient_state)
    if not patient_id:
        return "Please select a patient first."
    run_agent = _get_run_agent()
    return run_agent(message, patient_id)


def upload_doc(file, patient_state):
    if file is None:
        return "No file selected."
    import requests
    try:
        with open(file, "rb") as f:
            res = requests.post(
                "http://localhost:8000/upload",
                files={"file": (os.path.basename(file), f)},
            )
        if res.ok:
            data = res.json()
            return f"✓ Uploaded: {data.get('filename')} (job: {data.get('job_id', 'n/a')})"
        return f"Upload failed: {res.text}"
    except Exception as e:
        return f"Error: {e}"


with gr.Blocks(title="Healthcare AI POC") as demo:
    gr.Markdown("# 🏥 Healthcare AI Assistant")
    gr.Markdown("Powered by AWS Strands · Amazon Bedrock · Claude 3.5 Haiku")

    # State holds selected patient — not shown in examples table
    patient_state = gr.State(value=list(PATIENTS.keys())[0])

    patient_dropdown = gr.Dropdown(
        choices=list(PATIENTS.keys()),
        value=list(PATIENTS.keys())[0],
        label="Select Patient",
    )
    # Sync dropdown → state
    patient_dropdown.change(fn=lambda x: x, inputs=patient_dropdown, outputs=patient_state)

    chat = gr.ChatInterface(
        fn=respond,
        additional_inputs=[patient_state],
        examples=[[q, list(PATIENTS.keys())[0]] for q in QUICK_QUERIES],
        example_labels=QUICK_QUERIES,
    )

    gr.Markdown("---")
    with gr.Accordion("📄 Knowledge Base Upload", open=False):
        gr.Markdown("Upload a PDF or document to the Bedrock Knowledge Base.")
        file_input = gr.File(label="Select file", file_types=[".pdf", ".txt", ".docx"])
        upload_btn = gr.Button("Upload to KB", variant="primary")
        upload_status = gr.Textbox(label="Status", interactive=False)
        upload_btn.click(fn=upload_doc, inputs=[file_input, patient_state], outputs=upload_status)


if __name__ == "__main__":
    demo.launch(
        server_port=7862,
        share=True,
        theme=gr.themes.Soft(),
    )
