import { Link } from "react-router-dom";

// Colour-coded triage severity badge shared by Chat, History, and the Risk
// Matrix view. Renders as a Link into the Knowledge Base so an analyst can
// always click a severity to see what it means (and why not the level above
// or below). The colour comes from the `.sev-*` CSS classes in index.css so
// it follows the active light/dark theme.
export default function SeverityBadge({
  severity,
  linkToKnowledge = true,
}: {
  severity?: string | null;
  linkToKnowledge?: boolean;
}) {
  if (!severity) return null;
  const className = `severity-badge sev-${severity.toLowerCase()}`;
  if (!linkToKnowledge) {
    return <span className={className}>{severity}</span>;
  }
  return (
    <Link
      to={`/knowledge?tab=severity&level=${encodeURIComponent(severity)}`}
      className={className}
      title="Open severity definition in Knowledge Base"
    >
      {severity}
    </Link>
  );
}
