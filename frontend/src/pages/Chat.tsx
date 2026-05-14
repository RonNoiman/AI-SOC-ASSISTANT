import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { chat, conversations } from "../api/client";
import SeverityBadge from "../components/SeverityBadge";


interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  severity?: string | null;
  createdAt: string;
}

const AGENT_COLORS: Record<string, string> = {
  network: "#00d4ff",
  identity: "#a78bfa",
  policy: "#f59e0b",
  guardrail: "#ef4444",
};

const AGENT_LABELS: Record<string, string> = {
  network: "Network Security",
  identity: "Identity & Authentication",
  policy: "Policy & Compliance",
  guardrail: "Guardrail (blocked)",
};

function agentColor(agent?: string) {
  if (!agent) return "#64748b";
  return AGENT_COLORS[agent] || "#64748b";
}

function agentLabel(agent?: string) {
  if (!agent) return "";
  return AGENT_LABELS[agent] || agent;
}

export default function Chat() {
  const { conversationId: routeId } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [loadingHistory, setLoadingHistory] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Resume an existing conversation when navigated to /chat/:conversationId
  // (from the History page). Plain /chat resets to a clean slate.
  useEffect(() => {
    if (!routeId) {
      setMessages([]);
      setConversationId(undefined);
      return;
    }
    const id = Number(routeId);
    if (Number.isNaN(id)) {
      navigate("/chat", { replace: true });
      return;
    }
    let cancelled = false;
    setLoadingHistory(true);
    (async () => {
      try {
        const msgs = await conversations.messages(id);
        if (cancelled) return;
        setMessages(
          msgs.map((m) => ({
            role: m.role === "user" ? "user" : "assistant",
            content: m.content,
            agent: m.agent_used ?? undefined,
            severity: m.severity,
            createdAt: m.created_at,
          }))
        );
        setConversationId(id);
      } catch {
        // Not found or not owned by this user - fall back to a fresh chat.
        if (!cancelled) navigate("/chat", { replace: true });
      } finally {
        if (!cancelled) setLoadingHistory(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [routeId, navigate]);

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
        {
          role: "assistant",
          content: res.response,
          agent: res.agent,
          severity: res.severity,
          createdAt: new Date().toISOString(),
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err.message}`,
          createdAt: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
    // If we were resuming a conversation, drop the :id from the URL too.
    if (routeId) navigate("/chat");
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
        {loadingHistory && messages.length === 0 && (
          <div className="chat-empty">
            <p>Loading conversation...</p>
          </div>
        )}

        {!loadingHistory && messages.length === 0 && (
          <div className="chat-empty">
            <span className="chat-empty-icon">&#9737;</span>
            <h3>SOC Assistant Ready</h3>
            <p>Ask about network threats, identity issues, or security policies.</p>
            <div className="chat-suggestions">
              {[
                "Multiple failed RDP connections to port 3389 from unknown IPs",
                "50 failed login attempts for user admin from different countries",
                "Are we allowed to disable a user account during an active incident?",
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
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.role === "assistant" && msg.agent && (
              <div className="bubble-meta">
                <div
                  className="agent-badge"
                  style={{ color: agentColor(msg.agent) }}
                >
                  <span
                    className="agent-dot"
                    style={{ background: agentColor(msg.agent) }}
                  />
                  {agentLabel(msg.agent)}
                </div>
                <SeverityBadge severity={msg.severity} />
              </div>
            )}
            <div className="bubble-content">
              {msg.role === "assistant" ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              ) : (
                msg.content
              )}
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
