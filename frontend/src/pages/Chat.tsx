import { useState, useRef, useEffect } from "react";
import { chat } from "../api/client";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  createdAt: string;
}

const AGENT_COLORS: Record<string, string> = {
  network_agent: "#00d4ff",
  identity_agent: "#a78bfa",
  policy_agent: "#f59e0b",
  general: "#10b981",
};

function agentColor(agent?: string) {
  if (!agent) return "#64748b";
  return AGENT_COLORS[agent] || "#64748b";
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const now = new Date().toISOString();
    setMessages((prev) => [...prev, { role: "user", content: text, createdAt: now }]);
    setInput("");
    setSending(true);

    try {
      const res = await chat.send(text, conversationId);
      setConversationId(res.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.response, agent: res.agent, createdAt: new Date().toISOString() },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message}`, createdAt: new Date().toISOString() },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <h2>Security Chat</h2>
        <button className="btn-secondary" onClick={handleNewChat}>
          + New Chat
        </button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <span className="chat-empty-icon">&#9737;</span>
            <h3>SOC Assistant Ready</h3>
            <p>Ask about network threats, identity issues, or security policies.</p>
            <div className="chat-suggestions">
              {[
                "How should I investigate repeated failed login attempts?",
                "What signs indicate suspicious outbound traffic?",
                "What is a secure firewall policy for port 443?",
              ].map((s) => (
                <button
                  key={s}
                  className="suggestion-chip"
                  onClick={() => setInput(s)}
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="chat-empty-note">
              <h4>What This Assistant Does</h4>
              <p>
                It provides cybersecurity guidance by routing your question to a specialized
                agent. It does not read live SIEM, firewall, or Active Directory data in this version.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.role === "assistant" && msg.agent && (
              <div
                className="agent-badge"
                style={{ color: agentColor(msg.agent) }}
              >
                <span
                  className="agent-dot"
                  style={{ background: agentColor(msg.agent) }}
                />
                {msg.agent.replace("_", " ")}
              </div>
            )}
            <div className="bubble-content">{msg.content}</div>
            <div className="bubble-meta">
              {msg.role === "user" ? "You" : "Assistant"} • {new Date(msg.createdAt).toLocaleTimeString()}
            </div>
          </div>
        ))}

        {sending && (
          <div className="chat-bubble assistant">
            <div className="typing-indicator">
              <span /><span /><span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Describe a security concern..."
          disabled={sending}
        />
        <button
          className="btn-send"
          onClick={handleSend}
          disabled={sending || !input.trim()}
        >
          &#9654;
        </button>
      </div>
    </div>
  );
}
