import { Link } from "react-router-dom";

/**
 * Anchor renderer for ReactMarkdown. Internal hrefs (starting with `/`) use
 * React Router so clicks don't full-reload; external hrefs open in a new tab
 * with rel="noopener noreferrer". External links also get a small visual cue.
 */
export default function MarkdownLink({
  href,
  children,
  ...rest
}: React.AnchorHTMLAttributes<HTMLAnchorElement>) {
  const target = href ?? "";
  if (target.startsWith("/")) {
    return (
      <Link to={target} {...(rest as object)}>
        {children}
      </Link>
    );
  }
  return (
    <a href={target} target="_blank" rel="noopener noreferrer" {...rest}>
      {children}
    </a>
  );
}
