import { useState } from "react";
import { Link } from "react-router-dom";
import type { Transparency } from "../api/client";

// Short human-readable name per T-id, used in the chip. Full descriptions live
// in the Knowledge Base; here we just want the analyst to see what they got.
const THREAT_LABELS: Record<string, string> = {
  T1: "Prompt Injection / Jailbreak",
  T2: "Credential Stuffing / Brute Force",
  T3: "Reconnaissance / Port Scanning",
  T4: "Privilege Escalation Attempt",
  T5: "Insider Threat / Anomalous Access",
  T6: "Data Exfiltration",
  T7: "Policy Violation / Compliance Gap",
  T8: "Malware / Suspicious Process",
};

interface Props {
  transparency: Transparency;
  // Optional: show open by default for the very latest assistant reply.
  defaultOpen?: boolean;
}

export default function TransparencyPanel({ transparency, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  const pct = Math.round((transparency.confidence_score ?? 0) * 100);
  const threatLabel = transparency.threat_id
    ? `${transparency.threat_id} — ${THREAT_LABELS[transparency.threat_id] ?? "Threat"}`
    : null;

  return (
    <div className={`transparency-panel ${open ? "open" : ""}`}>
      <button
        type="button"
        className="transparency-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="transparency-toggle-label">
          {open ? "▾" : "▸"} AI Decision Reasoning
        </span>
        <span className="transparency-toggle-meta">
          Confidence {pct}%
          {transparency.threat_id ? ` · ${transparency.threat_id}` : ""}
          {transparency.stride_category ? ` · ${transparency.stride_category}` : ""}
        </span>
      </button>

      {open && (
        <div className="transparency-body">
          <div className="transparency-row">
            <span className="transparency-label">Confidence</span>
            <div className="transparency-confidence">
              <div className="transparency-confidence-track">
                <div
                  className="transparency-confidence-fill"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="transparency-confidence-value">{pct}%</span>
            </div>
          </div>

          {threatLabel && transparency.threat_id && (
            <div className="transparency-row">
              <span className="transparency-label">Threat</span>
              <Link
                to={`/knowledge?tab=threats&id=${encodeURIComponent(transparency.threat_id)}`}
                className="transparency-chip transparency-chip-threat"
                title="Open in Knowledge Base"
              >
                {threatLabel}
              </Link>
            </div>
          )}

          {transparency.stride_category && (
            <div className="transparency-row">
              <span className="transparency-label">STRIDE</span>
              <Link
                to={`/knowledge?tab=stride&category=${encodeURIComponent(transparency.stride_category)}`}
                className="transparency-chip transparency-chip-stride"
                title="Open in Knowledge Base"
              >
                {transparency.stride_category}
              </Link>
            </div>
          )}

          {transparency.matched_indicators.length > 0 && (
            <div className="transparency-row transparency-row-block">
              <span className="transparency-label">Matched indicators</span>
              <ul className="transparency-indicators">
                {transparency.matched_indicators.map((ind, i) => (
                  <li key={i}>{ind}</li>
                ))}
              </ul>
            </div>
          )}

          {transparency.reasoning && (
            <div className="transparency-row transparency-row-block">
              <span className="transparency-label">Why this triage</span>
              <p className="transparency-text">{transparency.reasoning}</p>
            </div>
          )}

          {transparency.recommended_action && (
            <div className="transparency-row transparency-row-block">
              <span className="transparency-label">Next step</span>
              <p className="transparency-text">{transparency.recommended_action}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
