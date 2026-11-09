import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Renders an assistant reply written in GitHub-flavored Markdown (bold, lists,
 * headings, tables, fenced code) as formatted HTML.
 *
 * Raw HTML in the source is intentionally NOT rendered: no `rehype-raw` is
 * wired in, so react-markdown's default behaviour of ignoring embedded HTML
 * stands. The chat reply is untrusted LLM output, and rendering raw HTML would
 * open a stored-XSS path. GFM alone covers every construct the agent emits.
 *
 * @param children The Markdown source string to render.
 */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
