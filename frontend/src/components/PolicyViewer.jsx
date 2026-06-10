import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { ChevronDown, ChevronRight, FileText } from 'lucide-react'
import { fetchPolicy } from '../api/client'

export default function PolicyViewer() {
  const [expanded, setExpanded] = useState(false)
  const [text, setText] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [loading, setLoading] = useState(false)

  const toggle = async () => {
    const next = !expanded
    setExpanded(next)
    if (next && !loaded && !loading) {
      setLoading(true)
      try {
        const data = await fetchPolicy()
        setText(data.text || '')
        setLoaded(true)
      } catch (_) {
        setText('Failed to load policy.')
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <div className="flex flex-col h-full border-l border-nova-border bg-nova-panel">
      <button
        onClick={toggle}
        className="flex items-center justify-between px-3 py-2.5 border-b border-nova-border shrink-0 hover:bg-nova-card transition-colors"
      >
        <span className="flex items-center gap-2 text-sm font-semibold">
          <FileText size={15} className="text-nova-amber" />
          Refund Policy — Source of Truth
        </span>
        {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>

      {expanded && (
        <div className="flex-1 overflow-y-auto px-3 py-3" style={{ maxHeight: 400 }}>
          {loading && (
            <div className="text-xs text-nova-muted">Loading policy…</div>
          )}
          {!loading && (
            <div className="policy-md text-xs leading-relaxed">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-sm font-bold text-nova-text mb-2">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xs font-bold text-nova-amber mt-3 mb-1">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-xs font-bold text-nova-amber mt-3 mb-1">{children}</h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-nova-muted mb-2">{children}</p>
                  ),
                  strong: ({ children }) => (
                    <strong className="text-nova-amber font-semibold">{children}</strong>
                  ),
                  li: ({ children }) => (
                    <li className="text-nova-muted ml-4 list-disc">{children}</li>
                  ),
                }}
              >
                {text}
              </ReactMarkdown>
            </div>
          )}
          {loaded && (
            <div className="text-[10px] text-nova-muted mt-4 pt-2 border-t border-nova-border">
              Last updated: policy v2 · deterministic guard enforced
            </div>
          )}
        </div>
      )}
    </div>
  )
}
