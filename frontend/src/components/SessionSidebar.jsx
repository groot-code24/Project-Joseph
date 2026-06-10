import React, { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Plus, X } from 'lucide-react'
import { fetchSessions, deleteSession } from '../api/client'

const DECISION_BADGE = {
  approved: { label: 'Approved', cls: 'bg-nova-green/20 text-nova-green' },
  denied: { label: 'Denied', cls: 'bg-nova-red/20 text-nova-red' },
  escalated_human: { label: 'Escalated', cls: 'bg-nova-amber/20 text-nova-amber' },
}

export default function SessionSidebar({ activeSessionId, onSessionSelect, onNewSession, reloadKey }) {
  const [sessions, setSessions] = useState([])

  const load = () => fetchSessions().then(setSessions).catch(() => {})

  useEffect(() => {
    load()
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [reloadKey])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    try { await deleteSession(id) } catch (_) {}
    load()
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-nova-border shrink-0">
        <span className="text-sm font-semibold">Sessions</span>
        <button
          onClick={onNewSession}
          className="flex items-center gap-1 text-xs bg-nova-blue text-white px-2 py-1 rounded-md hover:bg-blue-500 transition-colors"
        >
          <Plus size={13} /> New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sessions.length === 0 && !activeSessionId ? (
          <div className="text-xs text-nova-muted text-center mt-6 px-2">
            No sessions yet. Click New Chat to start.
          </div>
        ) : (
          <div className="flex flex-col gap-1.5">
            {activeSessionId && !sessions.some(s => s.session_id === activeSessionId) && (
              <SessionItem
                session={{ session_id: activeSessionId, customer_id: null, final_decision: null, message_count: 0, last_active: new Date().toISOString() }}
                active
                onSelect={() => onSessionSelect(activeSessionId)}
                onDelete={() => {}}
                isNew
              />
            )}
            {sessions.map(s => (
              <SessionItem
                key={s.session_id}
                session={s}
                active={s.session_id === activeSessionId}
                onSelect={() => onSessionSelect(s.session_id)}
                onDelete={(e) => handleDelete(e, s.session_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function SessionItem({ session, active, onSelect, onDelete, isNew }) {
  const badge = session.final_decision ? DECISION_BADGE[session.final_decision] : { label: 'Active', cls: 'bg-nova-blue/20 text-nova-blue' }
  let when = ''
  try { when = formatDistanceToNow(new Date(session.last_active), { addSuffix: true }) } catch (_) {}

  return (
    <div
      onClick={onSelect}
      className={`group cursor-pointer rounded-lg px-2.5 py-2 border transition-colors ${active ? 'bg-nova-card border-l-2 border-l-nova-blue border-nova-border' : 'bg-nova-panel border-nova-border hover:bg-nova-card/60'}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-nova-text">{session.session_id.slice(0, 8)}…</span>
        {!isNew && (
          <button onClick={onDelete} className="opacity-0 group-hover:opacity-100 text-nova-muted hover:text-nova-red transition-opacity">
            <X size={13} />
          </button>
        )}
      </div>
      <div className="text-[11px] text-nova-muted mt-0.5">{session.customer_id || 'Unknown Customer'}</div>
      <div className="flex items-center justify-between mt-1.5">
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${badge.cls}`}>{badge.label}</span>
        <span className="text-[10px] text-nova-muted">{session.message_count || 0} msgs</span>
      </div>
      {when && <div className="text-[10px] text-nova-muted mt-0.5">{when}</div>}
    </div>
  )
}
