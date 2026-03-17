// In production (Vercel), set VITE_API_URL to the AgentCore endpoint
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getPatients() {
  const res = await fetch(`${BASE}/patients`);
  return res.json();
}

export async function sendMessage(message, patientId) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, patient_id: patientId }),
  });
  return res.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}
