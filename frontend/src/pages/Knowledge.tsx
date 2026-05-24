import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  reference,
  mitreUrl,
  type SeverityLevel,
  type Threat,
  type StrideCategory,
  type RiskMatrixRow,
  type MitreTechnique,
} from "../api/client";

type Tab = "severity" | "threats" | "stride" | "risk-matrix" | "mitre";

const TABS: { id: Tab; label: string }[] = [
  { id: "severity", label: "Severity Dictionary" },
  { id: "threats", label: "Threat Dictionary" },
  { id: "mitre", label: "MITRE ATT&CK" },
  { id: "stride", label: "STRIDE Analysis" },
  { id: "risk-matrix", label: "Risk Matrix" },
];

export default function Knowledge() {
  const [params, setParams] = useSearchParams();
  const tabParam = (params.get("tab") as Tab) || "severity";
  const focusId = params.get("id") || params.get("level") || params.get("category");

  const [severity, setSeverity] = useState<SeverityLevel[]>([]);
  const [threats, setThreats] = useState<Threat[]>([]);
  const [stride, setStride] = useState<StrideCategory[]>([]);
  const [risk, setRisk] = useState<RiskMatrixRow[]>([]);
  const [mitre, setMitre] = useState<MitreTechnique[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, t, st, r, m] = await Promise.all([
          reference.severity(),
          reference.threats(),
          reference.stride(),
          reference.riskMatrix(),
          reference.mitre(),
        ]);
        setSeverity(s);
        setThreats(t);
        setStride(st);
        setRisk(r);
        setMitre(m);
      } catch (err: any) {
        setError(err.message || "Failed to load reference data.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const setTab = (id: Tab) => {
    const next = new URLSearchParams(params);
    next.set("tab", id);
    next.delete("id");
    next.delete("level");
    next.delete("category");
    setParams(next, { replace: true });
  };

  if (loading) {
    return (
      <div className="knowledge-page">
        <p className="panel-note">Loading reference data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="knowledge-page">
        <p className="panel-note">{error}</p>
      </div>
    );
  }

  return (
    <div className="knowledge-page">
      <header className="knowledge-header">
        <h2>Knowledge Base</h2>
        <p>
          Why an alert is rated the way it is, which threat catalog entry it
          matches, and how this project's STRIDE analysis maps to real components.
        </p>
      </header>

      <div className="knowledge-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`knowledge-tab ${tabParam === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="knowledge-tab-body">
        {tabParam === "severity" && (
          <SeverityTab levels={severity} focusId={focusId} />
        )}
        {tabParam === "threats" && (
          <ThreatsTab threats={threats} focusId={focusId} />
        )}
        {tabParam === "mitre" && (
          <MitreTab techniques={mitre} focusId={focusId} />
        )}
        {tabParam === "stride" && (
          <StrideTab categories={stride} focusId={focusId} />
        )}
        {tabParam === "risk-matrix" && <RiskMatrixTab rows={risk} />}
      </div>
    </div>
  );
}

// ── Severity Dictionary ──────────────────────────────────────────────────────

function SeverityTab({
  levels,
  focusId,
}: {
  levels: SeverityLevel[];
  focusId: string | null;
}) {
  // Deep-link target opens by default; otherwise the first entry opens.
  const initial = useMemo(() => {
    if (focusId) {
      const match = levels.find(
        (l) => l.level.toLowerCase() === focusId.toLowerCase()
      );
      if (match) return match.level;
    }
    return levels[0]?.level ?? null;
  }, [levels, focusId]);

  const [open, setOpen] = useState<string | null>(initial);

  useEffect(() => setOpen(initial), [initial]);

  return (
    <div className="knowledge-list">
      <p className="knowledge-blurb">
        Severity reflects business impact x likelihood from the analyst's point
        of view. Click any level to see what triggers it, why it is dangerous,
        and why it is not the level above or below.
      </p>
      {levels.map((l) => {
        const isOpen = open === l.level;
        return (
          <article
            key={l.level}
            className={`knowledge-card sev-card sev-card-${l.level.toLowerCase()} ${
              isOpen ? "open" : ""
            }`}
          >
            <button
              className="knowledge-card-toggle"
              onClick={() => setOpen(isOpen ? null : l.level)}
              aria-expanded={isOpen}
            >
              <span className="sev-card-marker" style={{ background: l.color }} />
              <span className="knowledge-card-title">{l.level}</span>
              <span className="knowledge-card-sub">{l.what_it_means}</span>
              <span className="knowledge-card-caret">{isOpen ? "▾" : "▸"}</span>
            </button>

            {isOpen && (
              <div className="knowledge-card-body">
                <DetailBlock label="Typical indicators" items={l.typical_indicators} />
                <DetailBlock label="Typical scenarios" items={l.typical_scenarios} />
                <DetailLine label="Why it is dangerous" text={l.why_dangerous} />
                <DetailLine label="Why not higher" text={l.why_not_higher} />
                <DetailLine label="Why not lower" text={l.why_not_lower} />
                <DetailLine label="Response SLA" text={l.response_sla} />
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

// ── Threat Dictionary ────────────────────────────────────────────────────────

function ThreatsTab({
  threats,
  focusId,
}: {
  threats: Threat[];
  focusId: string | null;
}) {
  const initial = useMemo(() => {
    if (focusId) {
      const match = threats.find((t) => t.id.toLowerCase() === focusId.toLowerCase());
      if (match) return match.id;
    }
    return threats[0]?.id ?? null;
  }, [threats, focusId]);

  const [open, setOpen] = useState<string | null>(initial);

  useEffect(() => setOpen(initial), [initial]);

  return (
    <div className="knowledge-list">
      <p className="knowledge-blurb">
        T-ids follow the standard threat-model traceability notation. Every
        agent reply links to the T-id it matched so the analyst can trace the
        decision back to a known threat.
      </p>
      {threats.map((t) => {
        const isOpen = open === t.id;
        return (
          <article
            key={t.id}
            className={`knowledge-card threat-card ${isOpen ? "open" : ""}`}
          >
            <button
              className="knowledge-card-toggle"
              onClick={() => setOpen(isOpen ? null : t.id)}
              aria-expanded={isOpen}
            >
              <span className="threat-id">{t.id}</span>
              <span className="knowledge-card-title">{t.name}</span>
              <span className="threat-stride">{t.stride_category}</span>
              <span className="knowledge-card-caret">{isOpen ? "▾" : "▸"}</span>
            </button>

            {isOpen && (
              <div className="knowledge-card-body">
                <DetailLine label="Description" text={t.description} />
                <DetailLine
                  label="Attack example"
                  text={t.attack_example}
                  mono
                />
                <DetailBlock
                  label="Detection indicators"
                  items={t.detection_indicators}
                />
                <DetailLine label="Mitigation" text={t.mitigation} />
                <DetailLine
                  label="Primary agent"
                  text={t.primary_agent}
                  pill
                />
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

// ── MITRE ATT&CK ─────────────────────────────────────────────────────────────

function MitreTab({
  techniques,
  focusId,
}: {
  techniques: MitreTechnique[];
  focusId: string | null;
}) {
  const requested = focusId ? focusId.trim().toUpperCase() : null;

  // Resolve the deep-link target. We open the matching parent or sub if it
  // exists in the curated set; otherwise we show a fallback card linking to
  // attack.mitre.org so the analyst is never stuck without a source.
  const focusMatch = useMemo(() => {
    if (!requested) return null;
    if (techniques.some((t) => t.id === requested)) return requested;
    if (requested.includes(".")) {
      const parent = requested.split(".")[0];
      if (techniques.some((t) => t.id === parent)) return parent;
    }
    return null;
  }, [requested, techniques]);

  const [open, setOpen] = useState<string | null>(
    focusMatch ?? techniques[0]?.id ?? null
  );

  useEffect(() => {
    if (focusMatch) setOpen(focusMatch);
  }, [focusMatch]);

  const showFallback = requested && !focusMatch;

  return (
    <div className="knowledge-list">
      <p className="knowledge-blurb">
        Curated subset of MITRE ATT&CK techniques the agents commonly cite -
        T1078, T1110, T1190, T1003, T1486, T1021 and others. Sub-techniques
        (e.g. T1021.001 RDP) link to the parent here and to the full sub-page
        on attack.mitre.org. Anything not in this dictionary is one click away
        on the authoritative MITRE site.
      </p>

      {showFallback && (
        <article className="knowledge-card mitre-fallback">
          <div className="knowledge-card-body">
            <DetailLine
              label="Requested technique"
              text={requested!}
              mono
            />
            <DetailLine
              label="Note"
              text={
                "This technique is not curated in the local dictionary. " +
                "Open it on attack.mitre.org for the authoritative reference."
              }
            />
            <div className="kb-row">
              <span className="kb-label">attack.mitre.org</span>
              <a
                className="kb-text kb-text-link"
                href={mitreUrl(requested!)}
                target="_blank"
                rel="noopener noreferrer"
              >
                {mitreUrl(requested!)}
              </a>
            </div>
          </div>
        </article>
      )}

      {techniques.map((t) => {
        const isOpen = open === t.id;
        return (
          <article
            key={t.id}
            className={`knowledge-card mitre-card ${isOpen ? "open" : ""}`}
          >
            <button
              className="knowledge-card-toggle"
              onClick={() => setOpen(isOpen ? null : t.id)}
              aria-expanded={isOpen}
            >
              <span className="threat-id mitre-id">{t.id}</span>
              <span className="knowledge-card-title">{t.name}</span>
              <span className="threat-stride mitre-tactic">{t.tactic}</span>
              <span className="knowledge-card-caret">{isOpen ? "▾" : "▸"}</span>
            </button>

            {isOpen && (
              <div className="knowledge-card-body">
                <DetailLine label="Description" text={t.description} />
                <DetailBlock
                  label="Detection indicators"
                  items={t.detection_indicators}
                />
                <DetailBlock label="Mitigations" items={t.mitigations} />
                <div className="kb-row">
                  <span className="kb-label">attack.mitre.org</span>
                  <a
                    className="kb-text kb-text-link"
                    href={t.mitre_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {t.mitre_url}
                  </a>
                </div>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

// ── STRIDE Analysis ──────────────────────────────────────────────────────────

function StrideTab({
  categories,
  focusId,
}: {
  categories: StrideCategory[];
  focusId: string | null;
}) {
  const initial = useMemo(() => {
    if (focusId) {
      const match = categories.find(
        (c) => c.category.toLowerCase() === focusId.toLowerCase()
      );
      if (match) return match.category;
    }
    return categories[0]?.category ?? null;
  }, [categories, focusId]);

  const [open, setOpen] = useState<string | null>(initial);

  useEffect(() => setOpen(initial), [initial]);

  return (
    <div className="knowledge-list">
      <p className="knowledge-blurb">
        Each STRIDE category is tied to real components of this project, with
        the current mitigation in code and an honest note about residual risk
        (flagged Future Improvement where relevant).
      </p>
      {categories.map((c) => {
        const isOpen = open === c.category;
        return (
          <article
            key={c.category}
            className={`knowledge-card stride-card ${isOpen ? "open" : ""}`}
          >
            <button
              className="knowledge-card-toggle"
              onClick={() => setOpen(isOpen ? null : c.category)}
              aria-expanded={isOpen}
            >
              <span className="knowledge-card-title">{c.category}</span>
              <span className="knowledge-card-sub">{c.definition}</span>
              <span className="knowledge-card-caret">{isOpen ? "▾" : "▸"}</span>
            </button>

            {isOpen && (
              <div className="knowledge-card-body">
                {c.scenarios.map((s, i) => (
                  <div key={i} className="stride-scenario">
                    <DetailLine label="Attack" text={s.attack} />
                    <DetailLine
                      label="Affected component"
                      text={s.affected_component}
                      mono
                    />
                    <DetailLine label="Risk" text={s.risk} />
                    <DetailLine label="Mitigation" text={s.mitigation} />
                    <DetailLine
                      label="Residual risk"
                      text={s.residual_risk}
                      highlight={s.residual_risk
                        .toLowerCase()
                        .includes("future improvement")}
                    />
                  </div>
                ))}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

// ── Risk Matrix ──────────────────────────────────────────────────────────────

function RiskMatrixTab({ rows }: { rows: RiskMatrixRow[] }) {
  return (
    <div className="knowledge-list">
      <p className="knowledge-blurb">
        Risk Matrix: likelihood x impact = severity for each cataloged threat,
        with the mitigation in this codebase and the remaining residual risk.
      </p>
      <div className="risk-matrix-wrap">
        <table className="risk-matrix">
          <thead>
            <tr>
              <th>ID</th>
              <th>Threat</th>
              <th>STRIDE</th>
              <th>Likelihood</th>
              <th>Impact</th>
              <th>Severity</th>
              <th>Affected Component</th>
              <th>Mitigation</th>
              <th>Residual Risk</th>
              <th>Why this severity</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.threat_id}>
                <td>
                  <strong>{r.threat_id}</strong>
                </td>
                <td>{r.threat}</td>
                <td>{r.stride}</td>
                <td>
                  <span className={`rm-pill rm-${r.likelihood.toLowerCase()}`}>
                    {r.likelihood}
                  </span>
                </td>
                <td>
                  <span className={`rm-pill rm-${r.impact.toLowerCase()}`}>
                    {r.impact}
                  </span>
                </td>
                <td>
                  <span
                    className={`severity-badge sev-${r.severity.toLowerCase()}`}
                  >
                    {r.severity}
                  </span>
                </td>
                <td className="risk-matrix-mono">{r.affected_component}</td>
                <td>{r.mitigation}</td>
                <td>{r.residual_risk}</td>
                <td>{r.why_this_severity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Shared bits ──────────────────────────────────────────────────────────────

function DetailBlock({
  label,
  items,
}: {
  label: string;
  items: string[];
}) {
  if (!items || items.length === 0) return null;
  return (
    <div className="kb-row kb-row-block">
      <span className="kb-label">{label}</span>
      <ul className="kb-list">
        {items.map((it, i) => (
          <li key={i}>{it}</li>
        ))}
      </ul>
    </div>
  );
}

function DetailLine({
  label,
  text,
  mono,
  pill,
  highlight,
}: {
  label: string;
  text: string;
  mono?: boolean;
  pill?: boolean;
  highlight?: boolean;
}) {
  if (!text) return null;
  const cls = [
    "kb-text",
    mono ? "kb-text-mono" : "",
    pill ? "kb-text-pill" : "",
    highlight ? "kb-text-future" : "",
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <div className="kb-row kb-row-block">
      <span className="kb-label">{label}</span>
      <span className={cls}>{text}</span>
    </div>
  );
}
