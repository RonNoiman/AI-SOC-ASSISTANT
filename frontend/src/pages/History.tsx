import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  conversations,
  type ConversationSummary,
  type ConversationFilters,
  type Message,
} from "../api/client";
import SeverityBadge from "../components/SeverityBadge";

const AGENT_LABELS: Record<string, string> = {
  network: "Network",
  identity: "Identity",
  policy: "Policy",
  guardrail: "Guardrail",
};

function agentLabel(agent: string) {
  return AGENT_LABELS[agent] || agent;
}

export default function History() {
  const navigate = useNavigate();
  const [convos, setConvos] = useState<ConversationSummary[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [msgLoading, setMsgLoading] = useState(false);

  // Search + filter controls.
  const [query, setQuery] = useState("");
  const [agent, setAgent] = useState("");
  const [severity, setSeverity] = useState("");
  const [sort, setSort] = useState<"newest" | "oldest">("newest");

  const loadConvos = useCallback(async (filters: ConversationFilters) => {
    setLoading(true);
    try {
      const items = await conversations.list(filters);
      setConvos(items);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounced reload: refetch 300 ms after the user stops changing any control.
  useEffect(() => {
    const handle = setTimeout(() => {
      void loadConvos({ q: query, agent, severity, sort });
    }, 300);
    return () => clearTimeout(handle);
  }, [query, agent, severity, sort, loadConvos]);

  const openConversation = async (id: number) => {
    setSelected(id);
    setMsgLoading(true);
    try {
      const msgs = await conversations.messages(id);
      setMessages(msgs);
    } finally {
      setMsgLoading(false);
    }
  };

  const deleteConversation = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;
    await conversations.delete(id);
    setConvos((prev) => prev.filter((c) => c.id !== id));
    if (selected === id) {
      setSelected(null);
      setMessages([]);
    }
  };

  const hasFilters = Boolean(query || agent || severity);
  const selectedConvo = convos.find((c) => c.id === selected) || null;

  return (
    <div className="history-page">
      <div className="history-sidebar">
        <h2>Conversations</h2>

        <div className="history-controls">
          <input
            type="search"
            className="history-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search title or message..."
          />
          <div className="history-filters">
            <select
              value={agent}
              onChange={(e) => setAgent(e.target.value)}
              title="Filter by assistant"
            >
              <option value="">All agents</option>
              <option value="network">Network</option>
              <option value="identity">Identity</option>
              <option value="policy">Policy</option>
              <option value="guardrail">Guardrail</option>
            </select>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              title="Filter by risk"
            >
              <option value="">All risk</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
              <option value="Informational">Info</option>
            </select>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as "newest" | "oldest")}
              title="Sort by time"
            >
              <option value="newest">Newest</option>
              <option value="oldest">Oldest</option>
            </select>
          </div>
        </div>

        {loading ? (
          <p className="panel-note">Loading conversations...</p>
        ) : convos.length === 0 ? (
          <div className="panel-note">
            <strong>{hasFilters ? "No matches." : "No conversations yet."}</strong>
            <span>
              {hasFilters
                ? "Try different search terms or filters."
                : "Start a chat to build searchable history for the analyst."}
            </span>
          </div>
        ) : (
          <div className="convo-list">
            {convos.map((c) => (
              <div
                key={c.id}
                className={`convo-item ${selected === c.id ? "active" : ""}`}
                onClick={() => openConversation(c.id)}
              >
                <div className="convo-title">{c.title}</div>
                {(c.agents.length > 0 || c.top_severity) && (
                  <div className="convo-badges">
                    {c.agents.map((a) => (
                      <span key={a} className="convo-agent-chip">
                        {agentLabel(a)}
                      </span>
                    ))}
                    <SeverityBadge severity={c.top_severity} />
                  </div>
                )}
                <div className="convo-meta">
                  <span>{c.message_count} messages</span>
                  <span>{new Date(c.updated_at).toLocaleDateString()}</span>
                </div>
                <button
                  className="convo-delete"
                  onClick={(e) => deleteConversation(c.id, e)}
                  title="Delete"
                >
                  &#10005;
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="history-detail">
        {!selected ? (
          <div className="history-empty">
            <div className="panel-note panel-note-centered">
              <strong>Select a conversation</strong>
              <span>
                Review previous analyst questions, agent answers, and
                timestamps - then resume the chat to keep investigating.
              </span>
            </div>
          </div>
        ) : (
          <>
            <div className="history-detail-header">
              <h3>{selectedConvo?.title ?? "Conversation"}</h3>
              <button
                className="btn-primary"
                onClick={() => navigate(`/chat/${selected}`)}
              >
                Resume chat &rarr;
              </button>
            </div>
            {msgLoading ? (
              <p className="panel-note">Loading messages...</p>
            ) : (
              <div className="message-list">
                {messages.map((m) => (
                  <div key={m.id} className={`history-msg ${m.role}`}>
                    <div className="msg-header">
                      <span className="msg-role">
                        {m.role === "user" ? "You" : "Assistant"}
                      </span>
                      {m.agent_used && (
                        <span className="msg-agent">
                          {m.agent_used.replace("_", " ")}
                        </span>
                      )}
                      <SeverityBadge severity={m.severity} />
                      <span className="msg-time">
                        {new Date(m.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="msg-content">
                      {m.role === "assistant" ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {m.content}
                        </ReactMarkdown>
                      ) : (
                        m.content
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
