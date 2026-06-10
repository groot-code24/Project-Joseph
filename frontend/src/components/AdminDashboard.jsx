import React, { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronRight, ShieldAlert } from 'lucide-react'
import { fetchTrace, createTraceStream, fetchMetrics } from '../api/client'

const TYPE_STYLE = {
  llm_call: 'bg-nova-purple/25 text-nova-purple',
  tool_call: 'bg-nova-blue/25 text-nova-blue',
  tool_result: 'bg-slate-600/40 text-slate-300',
  guard_check: 'bg-slate-600/40 text-slate-200',
  retry: 'bg-nova-amber/25 text-nova-amber',
  injection_detected: 'bg-nova-red/25 text-nova-red',
}

const DEFAULT_EXPANDED = new Set(['guard_check', 'injection_detected'])

function guardColor(step) {
  const d = step.tool_output?.decision
  if (d === 'approve') return 'bg-nova-green/25 text-nova-green'
  if (d === 'deny') return 'bg-nova-red/25 text-nova-red'
  if (d === 'escalate') return 'bg-nova-amber/25 text-nova-amber'
  return TYPE_STYLE.guard_check
}

function StatChip({ value, label, color }) {
  return (
    <div className="flex-1 rounded-lg bg-nova-card border border-nova-border px-2 py-1.5 text-center">
      <div className={`text-lg font-semibold ${color}`}>{value}</div>
      <div className="text-[10px] text-nova-muted leading-tight">{label}</div>
    </div>
  )
}

function TraceCard({ step }) {
  const [open, setOpen] = useState(DEFAULT_EXPANDED.has(step.step_type))
  const badgeCls = step.step_type === 'guard_check' ? guardColor(step) : (TYPE_STYLE[step.step_type] || 'bg-slate-600/40 text-slate-300')
  const time = step.timestamp ? new Date(step.timestamp).toLocaleTimeString('en-GB') : ''
  const body = { ...(step.tool_input ? { input: step.tool_input } : {}), ...(step.tool_output ? { output: step.tool_output } : {}) }
  const hasBody = Object.keys(body).length > 0 || step.notes

  return (
    <div className="rounded-lg border border-nova-border bg-nova-panel mb-1.5 overflow-hidden">
      <button onClick={() => setOpen(o => !o)} className="w-full flex items-center gap-2 px-2.5 py-1.5 text-left hover:bg-nova-card/50">
        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide flex items-center gap-1 ${badgeCls}`}>
          {step.step_type === 'injection_detected' && <ShieldAlert size={11} />}
          {step.step_type.replace('_', ' ')}
        </span>
        {step.tool_name && <span className="text-xs font-mono text-nova-text">{step.tool_name}</span>}
        {step.latency_ms ? <span className="text-[10px] text-nova-muted bg-nova-card px-1.5 py-0.5 rounded-full">{Math.round(step.latency_ms)}ms</span> : null}
        {step.step_type === 'llm_call' && (
          <span className="text-[10px] text-nova-muted font-mono">↑{step.llm_input_tokens ?? 0} / ↓{step.llm_output_tokens ?? 0}</span>
        )}
        <span className="ml-auto text-[10px] text-nova-muted font-mono">{time}</span>
        {hasBody && (open ? <ChevronDown size={14} className="text-nova-muted" /> : <ChevronRight size={14} className="text-nova-muted" />)}
      </button>
      {open && hasBody && (
        <div className="px-2.5 pb-2">
          {step.notes && <div className="text-[11px] text-nova-amber mb-1">{step.notes}</div>}
          {Object.keys(body).length > 0 && (
            <pre className="text-[11px] leading-snug rounded-md p-2 overflow-auto" style={{ background: '#0d1117', color: '#4ade80', maxHeight: 300 }}>
              {JSON.stringify(body, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}

export default function AdminDashboard({ sessionId }) {
  const [traceSteps, setTraceSteps] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const bottomRef = useRef(null)
  const sourceRef = useRef(null)

  useEffect(() => {
    if (sourceRef.current) { sourceRef.current.close(); sourceRef.current = null }
    setTraceSteps([])
    setIsConnected(false)
    if (!sessionId) return

    let cancelled = false
    const seen = new Set()

    const addStep = (s) => {
      const key = `${s.step_id}-${s.step_type}-${s.timestamp}`
      if (seen.has(key)) return
      seen.add(key)
      setTraceSteps(prev => [...prev, s])
    }

    fetchTrace(sessionId).then(steps => {
      if (cancelled) return
      steps.forEach(addStep)
    }).catch(() => {})

    const src = createTraceStream(
      sessionId,
      (s) => { if (!cancelled) { setIsConnected(true); addStep(s) } },
      () => { if (!cancelled) setIsConnected(false) }
    )
    sourceRef.current = src
    setIsConnected(true)

    return () => {
      cancelled = true
      if (sourceRef.current) { sourceRef.current.close(); sourceRef.current = null }
    }
  }, [sessionId])

  useEffect(() => {
    const load = () => fetchMetrics().then(setMetrics).catch(() => {})
    load()
    const t = setInterval(load, 5000)
    return () => clearInterval(t)
  }, [traceSteps.length])

  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: 'smooth' })
  }, [traceSteps.length])

  const totalIn = traceSteps.reduce((a, s) => a + (s.llm_input_tokens || 0), 0)
  const totalOut = traceSteps.reduce((a, s) => a + (s.llm_output_tokens || 0), 0)
  const totalLatency = Math.round(traceSteps.reduce((a, s) => a + (s.latency_ms || 0), 0))

  return (
    <div className="flex flex-col h-full bg-nova-dark">
      <div className="px-3 pt-2 pb-1 flex gap-1.5 shrink-0">
        <StatChip value={metrics?.total_sessions ?? 0} label="Sessions" color="text-nova-text" />
        <StatChip value={metrics?.approved ?? 0} label="Approved" color="text-nova-green" />
        <StatChip value={metrics?.denied ?? 0} label="Denied" color="text-nova-red" />
        <StatChip value={metrics?.escalated ?? 0} label="Escalated" color="text-nova-amber" />
        <StatChip value={metrics?.injection_attempts_detected ?? 0} label="Injections" color="text-nova-red" />
      </div>

      <div className="px-3 py-1.5 flex items-center gap-3 text-[11px] text-nova-muted border-b border-nova-border shrink-0">
        <span className="font-semibold text-nova-text">Agent Trace</span>
        <span>Steps: {traceSteps.length}</span>
        <span className="font-mono">Tokens: ↑{totalIn} / ↓{totalOut}</span>
        <span>Latency: {totalLatency}ms</span>
        <span className={`ml-auto flex items-center gap-1 ${isConnected ? 'text-nova-green' : 'text-nova-red'}`}>
          ● {isConnected ? 'Live' : 'Disconnected'}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2">
        {traceSteps.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-nova-muted gap-2">
            <span className="pulse-dot w-2 h-2 rounded-full bg-nova-muted inline-block" />
            Waiting for agent activity…
          </div>
        ) : (
          <>
            {traceSteps.map((s, i) => <TraceCard key={`${s.step_id}-${i}`} step={s} />)}
            <div ref={bottomRef} />
          </>
        )}
      </div>
    </div>
  )
}
