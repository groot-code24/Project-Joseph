import React, { useState } from 'react'
import { Zap, Circle } from 'lucide-react'
import SessionSidebar from './components/SessionSidebar'
import ChatWindow from './components/ChatWindow'
import AdminDashboard from './components/AdminDashboard'
import PolicyViewer from './components/PolicyViewer'

export default function App() {
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  const handleNewSession = () => {
    const id = crypto.randomUUID()
    setActiveSessionId(id)
    setReloadKey(k => k + 1)
  }

  const handleSelect = (id) => {
    setActiveSessionId(id)
    setReloadKey(k => k + 1)
  }

  const handleActivity = () => setReloadKey(k => k + 1)

  return (
    <div className="h-screen w-screen flex flex-col bg-nova-dark text-nova-text overflow-hidden">
      <header className="h-12 flex items-center justify-between px-4 border-b border-nova-border bg-nova-panel shrink-0">
        <div className="flex items-center gap-2 font-semibold text-nova-purple">
          <Zap size={18} className="fill-nova-purple" />
          <span>NovaMart</span>
        </div>
        <div className="text-sm text-nova-muted">AI Refund Agent</div>
        <div className="flex items-center gap-2 text-xs text-nova-muted">
          <Circle size={8} className="fill-nova-green text-nova-green" />
          <span className="font-mono">Groq Llama</span>
        </div>
      </header>

      <div className="flex-1 grid min-h-0" style={{ gridTemplateColumns: '280px 1fr 320px' }}>
        <div className="border-r border-nova-border bg-nova-panel min-h-0 overflow-hidden">
          <SessionSidebar
            activeSessionId={activeSessionId}
            onSessionSelect={handleSelect}
            onNewSession={handleNewSession}
            reloadKey={reloadKey}
          />
        </div>

        <div className="flex flex-col min-h-0 min-w-0" style={{ minWidth: '480px' }}>
          <div className="min-h-0 overflow-hidden border-b border-nova-border" style={{ flexBasis: '58%', flexGrow: 0, flexShrink: 1 }}>
            <ChatWindow sessionId={activeSessionId} onActivity={handleActivity} />
          </div>
          <div className="min-h-0 overflow-hidden" style={{ flexBasis: '42%', flexGrow: 1, flexShrink: 1 }}>
            <AdminDashboard sessionId={activeSessionId} />
          </div>
        </div>

        <div className="border-l border-nova-border bg-nova-panel min-h-0 overflow-hidden">
          <PolicyViewer />
        </div>
      </div>
    </div>
  )
}
