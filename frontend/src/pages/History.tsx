import { useState, useEffect } from "react";
import { conversations, type ConversationSummary, type Message } from "../api/client";

export default function History() {
  const [convos, setConvos] = useState<ConversationSummary[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [msgLoading, setMsgLoading] = useState(false);

  useEffect(() => {
    conversations.list().then(setConvos).finally(() => setLoading(false));
  }, []);

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

  return (
    <div className="history-page">
      <div className="history-sidebar">
        <h2>Conversations</h2>
        {loading ? (
          <p className="panel-note">Loading conversations...</p>
        ) : convos.length === 0 ? (
          <div className="panel-note">
            <strong>No conversations yet.</strong>
            <span>Start a chat to build searchable history for the analyst.</span>
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
                <div className="convo-meta">
                  <span>{c.message_count} messages</span>
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
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
              <span>Review previous analyst questions, agent answers, and timestamps.</span>
            </div>
          </div>
        ) : msgLoading ? (
          <p className="panel-note">Loading messages...</p>
        ) : (
          <div className="message-list">
            {messages.map((m) => (
              <div key={m.id} className={`history-msg ${m.role}`}>
                <div className="msg-header">
                  <span className="msg-role">{m.role === "user" ? "You" : "Assistant"}</span>
                  {m.agent_used && (
                    <span className="msg-agent">{m.agent_used.replace("_", " ")}</span>
                  )}
                  <span className="msg-time">
                    {new Date(m.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="msg-content">{m.content}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
