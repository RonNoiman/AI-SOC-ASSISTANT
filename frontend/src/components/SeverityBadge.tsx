// Colour-coded triage severity badge shared by the Chat and History views.
// The colour comes from the `.sev-*` CSS classes in index.css, so it follows
// the active light/dark theme.
export default function SeverityBadge({
  severity,
}: {
  severity?: string | null;
}) {
  if (!severity) return null;
  return (
    <span className={`severity-badge sev-${severity.toLowerCase()}`}>
      {severity}
    </span>
  );
}
