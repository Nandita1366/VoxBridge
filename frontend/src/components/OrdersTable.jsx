import { formatDistanceToNow } from 'date-fns'

const LANG_COLORS = { hi:'#F59E0B', kn:'#A78BFA', mr:'#F472B6', en:'#60A5FA' }

export default function OrdersTable({ orders }) {
  const exportCSV = () => {
    const rows = [
      ['ID','Item','Qty','Address','Language','WhatsApp','Time'],
      ...orders.map(o => [
        o.id, o.item, o.qty, o.address, o.language,
        o.whatsapp_sent ? 'Sent' : 'Pending',
        o.created_at ? new Date(o.created_at).toLocaleString() : '-'
      ])
    ]
    const csv = rows.map(r => r.join(',')).join('\n')
    const a = document.createElement('a')
    a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv)
    a.download = 'voxbridge_orders.csv'
    a.click()
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <p style={{fontSize:'13px', color:'var(--subtext)', fontFamily:"'IBM Plex Mono',monospace"}}>
          {orders.length} confirmed orders
        </p>
        <button onClick={exportCSV} style={{
          padding:'6px 14px', borderRadius:6, fontSize:'12px',
          background:'rgba(0,217,184,0.08)', color:'var(--teal)',
          border:'1px solid rgba(0,217,184,0.2)', cursor:'pointer',
          fontFamily:"'IBM Plex Mono',monospace"
        }}>
          ↓ Export CSV
        </button>
      </div>

      <div style={{overflowX:'auto'}}>
        <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
          <thead>
            <tr style={{borderBottom:'1px solid var(--border)'}}>
              {['Item','Qty','Address','Lang','WhatsApp','Time'].map(h => (
                <th key={h} style={{
                  padding:'8px 12px', textAlign:'left', color:'var(--subtext)',
                  fontSize:'11px', fontFamily:"'IBM Plex Mono',monospace",
                  textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:500
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {orders.map((o, i) => (
              <tr key={o.id || i}
                  style={{borderBottom:'1px solid var(--border)',
                          background: i%2===0 ? 'transparent' : 'rgba(255,255,255,0.01)'}}>
                <td style={{padding:'10px 12px', color:'var(--text)', fontWeight:500}}>{o.item}</td>
                <td style={{padding:'10px 12px', fontFamily:"'IBM Plex Mono',monospace", color:'var(--teal)'}}>{o.qty}</td>
                <td style={{padding:'10px 12px', color:'var(--subtext)', maxWidth:200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{o.address}</td>
                <td style={{padding:'10px 12px'}}>
                  <span style={{
                    color:LANG_COLORS[o.language]||'#94A3B8',
                    fontFamily:"'IBM Plex Mono',monospace", fontSize:'12px'
                  }}>{o.language?.toUpperCase()}</span>
                </td>
                <td style={{padding:'10px 12px'}}>
                  <span style={{
                    color: o.whatsapp_sent ? 'var(--green)' : 'var(--muted)',
                    fontSize:'12px'
                  }}>{o.whatsapp_sent ? '✅ Sent' : '⏳ Pending'}</span>
                </td>
                <td style={{padding:'10px 12px', color:'var(--subtext)', fontSize:'12px',
                            fontFamily:"'IBM Plex Mono',monospace"}}>
                  {o.created_at ? formatDistanceToNow(new Date(o.created_at),{addSuffix:true}) : '-'}
                </td>
              </tr>
            ))}
            {orders.length===0 && (
              <tr><td colSpan={6} style={{padding:'40px', textAlign:'center', color:'var(--muted)', fontFamily:"'IBM Plex Mono',monospace", fontSize:'13px'}}>
                No confirmed orders yet
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
