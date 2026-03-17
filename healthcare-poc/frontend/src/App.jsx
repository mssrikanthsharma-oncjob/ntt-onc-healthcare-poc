import { useState, useEffect, useRef } from "react";
import { getPatients, sendMessage, uploadDocument } from "./api";
import "./App.css";

const QUICK_QUERIES = ["Clinical Summary", "Lab Results", "Check Medications", "Insurance Status", "Next Follow Up", "Reminders"];

export default function App() {
  const [patients, setPatients] = useState([]);
  const [activePatient, setActivePatient] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    getPatients().then((data) => {
      setPatients(data.patients);
      setActivePatient(data.patients[0]);
    });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (activePatient) {
      setMessages([
        {
          role: "agent",
          text: `Hello! I'm ready to help with ${activePatient.name}'s care. Ask me for a clinical summary, lab results, medication check, or insurance status.`,
        },
      ]);
    }
  }, [activePatient?.id]);

  async function send(text) {
    const msg = (text ?? input).trim();
    if (!msg || loading || !activePatient) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const data = await sendMessage(msg, activePatient.id);
      setMessages((m) => [...m, { role: "agent", text: data.reply }]);
    } catch {
      setMessages((m) => [...m, { role: "agent", text: "Error contacting agent. Is the backend running?" }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploadStatus("Uploading...");
    try {
      const data = await uploadDocument(file);
      setUploadStatus(`✓ ${data.filename} uploaded`);
    } catch {
      setUploadStatus("Upload failed");
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h2 className="sidebar-title">Patients</h2>
        {patients.map((p) => (
          <div
            key={p.id}
            className={`patient-card ${activePatient?.id === p.id ? "active" : ""}`}
            onClick={() => setActivePatient(p)}
          >
            <span className={`dot dot-${p.status}`} />
            <div>
              <div className="patient-name">{p.name}</div>
              <div className="patient-meta">{p.age}y · {p.condition}</div>
            </div>
          </div>
        ))}

        <div className="quick-queries">
          <h3>Quick queries</h3>
          {QUICK_QUERIES.map((q) => (
            <button key={q} className="quick-btn" onClick={() => send(q)}>
              {q}
            </button>
          ))}
        </div>

        <div className="kb-upload">
          <h3>Knowledge Base</h3>
          <label className="upload-label">
            <input type="file" accept=".pdf,.txt,.docx" onChange={handleUpload} hidden />
            Upload Document
          </label>
          {uploadStatus && <div className="upload-status">{uploadStatus}</div>}
        </div>
      </aside>

      <main className="chat-panel">
        <header className="chat-header">
          <div>
            <span className="header-name">{activePatient?.name}</span>
            <span className="header-id"> · {activePatient?.id}</span>
          </div>
          <span className="bedrock-badge">Bedrock · Claude</span>
        </header>

        <div className="messages">
          {messages.map((m, i) => (
            <div key={i} className={`msg msg-${m.role}`}>
              <div className="bubble">{m.text}</div>
              {m.role === "agent" && <div className="msg-meta">Strands Agent · AWS Bedrock</div>}
            </div>
          ))}
          {loading && (
            <div className="msg msg-agent">
              <div className="bubble thinking">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="input-row">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask about patient care, medications, labs…"
            disabled={loading}
          />
          <button onClick={() => send()} disabled={loading}>Send</button>
        </div>
      </main>
    </div>
  );
}
