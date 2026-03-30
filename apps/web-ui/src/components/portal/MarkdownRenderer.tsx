import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const styles = `
.md-body { color: #c9d1d9; line-height: 1.8; font-size: 0.95rem; word-break: break-word; }
.md-body h1 { font-size: 1.5rem; margin: 28px 0 12px; padding-bottom: 8px; border-bottom: 1px solid #30363d; }
.md-body h2 { font-size: 1.25rem; margin: 24px 0 10px; padding-bottom: 6px; border-bottom: 1px solid #30363d; }
.md-body h3 { font-size: 1.1rem; margin: 20px 0 8px; }
.md-body h4 { font-size: 1rem; margin: 16px 0 6px; }
.md-body p { margin: 8px 0; }
.md-body strong { color: #e6edf3; }
.md-body a { color: #58a6ff; text-decoration: none; }
.md-body a:hover { text-decoration: underline; }
.md-body ul, .md-body ol { margin: 8px 0; padding-left: 24px; }
.md-body li { margin: 4px 0; }
.md-body blockquote { border-left: 3px solid #3fb950; padding: 8px 16px; margin: 12px 0; background: #0d1117; border-radius: 0 6px 6px 0; color: #8b949e; }
.md-body hr { border: none; border-top: 1px solid #30363d; margin: 20px 0; }
.md-body code { background: #161b22; padding: 2px 6px; border-radius: 4px; font-size: 0.88em; font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; color: #e6edf3; }
.md-body pre { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px; overflow-x: auto; margin: 12px 0; }
.md-body pre code { background: none; padding: 0; font-size: 0.85rem; line-height: 1.6; color: #c9d1d9; }
.md-body table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.9rem; }
.md-body thead { background: #161b22; }
.md-body th { padding: 10px 14px; text-align: left; border: 1px solid #30363d; font-weight: 600; color: #e6edf3; white-space: nowrap; }
.md-body td { padding: 8px 14px; border: 1px solid #30363d; vertical-align: top; }
.md-body tr:nth-child(even) { background: #161b2288; }
.md-body img { max-width: 100%; border-radius: 6px; margin: 8px 0; }
.md-body .contains-task-list { list-style: none; padding-left: 0; }
.md-body input[type="checkbox"] { margin-right: 8px; }
`

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <>
      <style>{styles}</style>
      <div className="md-body">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    </>
  )
}
