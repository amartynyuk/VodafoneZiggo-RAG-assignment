import { useState, type FormEvent } from "react";
import "./App.css";

/** Response shape from POST /ask (matches ai-assistant API contract). */
interface AskResponse {
  answer: string;
  source: string;
  confidence: number;
  blocked: boolean;
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; text: string; source?: string }[]
  >([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data: AskResponse = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          source: data.blocked ? "blocked" : data.source,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Could not reach the assistant API. Is docker compose running?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Ziggo Assistant</h1>
        <p className="subtitle">RAG demo — Phase 0 scaffold</p>
      </header>

      <main className="chat">
        {messages.length === 0 && (
          <p className="placeholder">
            Ask about Ziggo internet, TV, or Ziggo GO…
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`bubble bubble--${msg.role}`}>
            <p>{msg.text}</p>
            {msg.source && (
              <span className="badge">source: {msg.source}</span>
            )}
          </div>
        ))}
        {loading && <div className="bubble bubble--assistant">Thinking…</div>}
      </main>

      <form className="input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question…"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
