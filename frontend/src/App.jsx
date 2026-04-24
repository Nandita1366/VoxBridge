import { useState, useEffect, useRef, useCallback } from 'react'
import StatsBar from './components/StatsBar.jsx'
import CallFeed from './components/CallFeed.jsx'
import OrdersTable from './components/OrdersTable.jsx'
import LangChart from './components/LangChart.jsx'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS  = API.replace('http', 'ws') + '/ws'

export default function App() {
  const [calls, setCalls]   = useState({})
  const [orders, setOrders] = useState([])
  const [stats, setStats]   = useState({total_calls:0, confirmed_orders:0, escalations:0, language_distribution:{}})
  const [wsStatus, setWsStatus] = useState('connecting')
  const [activeTab, setActiveTab] = useState('calls')
  const wsRef = useRef(null)

  const fetchData = useCallback(async () => {
    try {
      const [s, o] = await Promise.all([
        fetch(`${API}/api/stats`).then(r => r.json()),
        fetch(`${API}/api/orders`).then(r => r.json())
      ])
      setStats(s)
      setOrders(o)
    } catch {}
  }, [])

  useEffect(() => {
    fetchData()
    const iv = setInterval(fetchData, 15000)
    return () => clearInterval(iv)
  }, [fetchData])

  useEffect(() => {
    let ws
    const connect = () => {
      ws = new WebSocket(WS)
      wsRef.current = ws
      ws.onopen  = () => setWsStatus('live')
      ws.onclose = () => { setWsStatus('reconnecting'); setTimeout(connect, 3000) }
      ws.onerror = () => setWsStatus('error')
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data)
        if (msg.type === 'ping') return

        if (msg.type === 'new_call') {
          setCalls(prev => ({
            ...prev,
            [msg.call_sid]: {
              call_sid: msg.call_sid,
              phone: msg.phone,
              status: 'active',
              language: '?',
              sentiment: 'NEUTRAL',
              neg_streak: 0,
              sentinel: false,
              transcript: [],
              timestamp: msg.timestamp
            }
          }))
        }

        if (msg.type === 'transcript_update') {
          setCalls(prev => {
            const existing = prev[msg.call_sid] || {}
            return {
              ...prev,
              [msg.call_sid]: {
                ...existing,
                call_sid: msg.call_sid,
                language: msg.language,
                sentiment: msg.sentiment,
                neg_streak: msg.neg_streak,
                sentinel: msg.sentinel_active,
                transcript: [
                  ...(existing.transcript || []),
                  { role: 'customer', text: msg.customer_text, sentiment: msg.sentiment },
                  { role: 'bot',      text: msg.bot_text }
                ]
              }
            }
          })
        }

        if (msg.type === 'order_confirmed') {
          setCalls(prev => ({
            ...prev,
            [msg.call_sid]: { ...(prev[msg.call_sid]||{}), status: 'completed', order: msg.order }
          }))
          setOrders(prev => [
            { id: Date.now(), call_sid: msg.call_sid, item: msg.order.item,
              qty: msg.order.qty, address: msg.order.address,
              language: msg.language, confirmed: true,
              whatsapp_sent: msg.whatsapp_sent,
              created_at: msg.timestamp },
            ...prev
          ])
          fetchData()
        }

        if (msg.type === 'escalation') {
          setCalls(prev => ({
            ...prev,
            [msg.call_sid]: { ...(prev[msg.call_sid]||{}), status: 'escalated' }
          }))
        }
      }
    }
    connect()
    return () => ws?.close()
  }, [fetchData])

  const callList = Object.values(calls).sort((a,b) =>
    new Date(b.timestamp||0) - new Date(a.timestamp||0)
  )

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-8 py-4 border-b"
              style={{borderColor:'var(--border)', background:'var(--surface)'}}>
        <div className="flex items-center gap-3">
          <div style={{
            width:36, height:36, background:'var(--teal)', borderRadius:8,
            display:'flex', alignItems:'center', justifyContent:'center'
          }}>
            <span style={{fontSize:18}}>🎙</span>
          </div>
          <div>
            <h1 className="font-display" style={{fontSize:'1.2rem', fontWeight:700, letterSpacing:'-0.02em', color:'var(--text)'}}>
              VoxBridge
            </h1>
            <p style={{fontSize:'11px', color:'var(--subtext)', fontFamily:"'IBM Plex Mono',monospace"}}>
              Automaton AI · Live Operations
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="live-dot" />
          <span style={{
            fontSize:'11px', fontFamily:"'IBM Plex Mono',monospace",
            color: wsStatus==='live' ? 'var(--teal)' : 'var(--amber)',
            textTransform:'uppercase', letterSpacing:'0.06em'
          }}>
            {wsStatus}
          </span>
        </div>
      </header>

      <StatsBar stats={stats} />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <div className="flex gap-1 px-6 pt-4 pb-0">
            {['calls','orders'].map(tab => (
              <button key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding:'6px 18px', borderRadius:8, fontSize:'13px', fontWeight:500,
                  border:'1px solid',
                  borderColor: activeTab===tab ? 'var(--teal)' : 'var(--border)',
                  background: activeTab===tab ? 'rgba(0,217,184,0.08)' : 'transparent',
                  color: activeTab===tab ? 'var(--teal)' : 'var(--subtext)',
                  cursor:'pointer', transition:'all 0.15s', textTransform:'capitalize'
                }}>
                {tab}
                {tab==='calls' && (
                  <span style={{
                    marginLeft:6, background:'var(--teal)', color:'var(--navy)',
                    borderRadius:999, padding:'0 6px', fontSize:'10px', fontWeight:700
                  }}>
                    {callList.filter(c=>c.status==='active').length}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {activeTab==='calls'  && <CallFeed calls={callList} />}
            {activeTab==='orders' && <OrdersTable orders={orders} />}
          </div>
        </div>

        <aside className="w-72 border-l p-6 overflow-y-auto hidden lg:block"
               style={{borderColor:'var(--border)', background:'var(--surface)'}}>
          <LangChart distribution={stats.language_distribution} />
        </aside>
      </div>
    </div>
  )
}
