import { formatDistanceToNow } from 'date-fns'

const LANG_LABELS = {
  hi:'Hindi', kn:'Kannada', mr:'Marathi', en:'English', '?':'Detecting...'
}
const LANG_COLORS = {
  hi:'#F59E0B', kn:'#A78BFA', mr:'#F472B6', en:'#60A5FA', '?':'#94A3B8'
}

export default function CallCard({ call }) {
  const sentimentColor = {
    POSITIVE:'var(--green)', NEUTRAL:'var(--subtext)', NEGATIVE:'var(--red)'
  }[call.sentiment] || 'var(--subtext)'

  const statusConfig = {
    active:    { label:'Active',    color:'var(--teal)' },
    completed: { label:'Done ✓',   color:'var(--green)' },
    escalated: { label:'Escalated',color:'var(--amber)' },
  }[call.status] || { label:call.status, color:'var(--subtext)' }

  return (
    <div className="card card-hover mb-3 overflow-hidden">
      <div className="flex items-center justify-between p-4 pb-3">
        <div className="flex items-center gap-3">
          <div style={{
            width:36, height:36, borderRadius:8, background:'rgba(0,217,184,0.08)',
            border:'1px solid rgba(0,217,184,0.2)', display:'flex',
            alignItems:'center', justifyContent:'center', fontSize:16
          }}>📞</div>
          <div>
            <p style={{fontSize:'13px', fontWeight:500, color:'var(--text)',
                       fontFamily:"'IBM Plex Mono',monospace"}}>
              {call.phone || 'Unknown'}
            </p>
            <p style={{fontSize:'11px', color:'var(--subtext)'}}>
              {call.timestamp ? formatDistanceToNow(new Date(call.timestamp), {addSuffix:true}) : '-'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap justify-end">
          <span style={{
            background:`${LANG_COLORS[call.language]}18`,
            color:LANG_COLORS[call.language],
            border:`1px solid ${LANG_COLORS[call.language]}40`,
            padding:'2px 8px', borderRadius:999, fontSize:'11px',
            fontFamily:"'IBM Plex Mono',monospace", fontWeight:500
          }}>
            {LANG_LABELS[call.language] || call.language}
          </span>

          <span style={{
            background:'transparent', color:statusConfig.color,
            border:`1px solid ${statusConfig.color}40`,
            padding:'2px 8px', borderRadius:999, fontSize:'11px',
            fontFamily:"'IBM Plex Mono',monospace", fontWeight:500
          }}>
            {call.status==='active' && <span style={{display:'inline-block',width:6,height:6,background:'var(--teal)',borderRadius:'50%',marginRight:5,verticalAlign:'middle',animation:'pulse 1.5s infinite'}}/>}
            {statusConfig.label}
          </span>

          {call.sentinel && (
            <span style={{
              background:'rgba(245,158,11,0.15)', color:'var(--amber)',
              border:'1px solid rgba(245,158,11,0.3)',
              padding:'2px 8px', borderRadius:999, fontSize:'11px',
              fontFamily:"'IBM Plex Mono',monospace"
            }}>
              ⚡ Sentinel
            </span>
          )}
        </div>
      </div>

      {call.transcript && call.transcript.length > 0 && (
        <div style={{
          borderTop:'1px solid var(--border)', padding:'12px 16px',
          maxHeight:180, overflowY:'auto', background:'rgba(10,15,30,0.5)'
        }}>
          {call.transcript.slice(-6).map((t, i) => (
            <div key={i} className={t.role==='customer' ? 'bubble-customer' : 'bubble-bot'}>
              <span style={{
                fontSize:'10px', color:'var(--subtext)',
                fontFamily:"'IBM Plex Mono',monospace", textTransform:'uppercase',
                display:'block', marginBottom:2
              }}>
                {t.role==='customer' ? '👤 Customer' : '🤖 VoxBridge'}
                {t.sentiment && t.role==='customer' && (
                  <span style={{
                    marginLeft:6, color:
                      t.sentiment==='POSITIVE' ? 'var(--green)' :
                      t.sentiment==='NEGATIVE' ? 'var(--red)' : 'var(--subtext)'
                  }}>● {t.sentiment}</span>
                )}
              </span>
              <p style={{fontSize:'13px', color:'var(--text)', lineHeight:1.5}}>
                {t.text}
              </p>
            </div>
          ))}
        </div>
      )}

      {call.order && (
        <div style={{
          borderTop:'1px solid rgba(16,185,129,0.2)', padding:'10px 16px',
          background:'rgba(16,185,129,0.06)'
        }}>
          <p style={{fontSize:'12px', color:'var(--green)', fontWeight:500}}>
            ✅ Order: {call.order.item} × {call.order.qty} → {call.order.address}
          </p>
        </div>
      )}
    </div>
  )
}
