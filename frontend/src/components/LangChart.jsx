import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const COLORS = { hi:'#F59E0B', kn:'#A78BFA', mr:'#F472B6', en:'#60A5FA' }
const LANG_NAMES = { hi:'Hindi', kn:'Kannada', mr:'Marathi', en:'English' }

const CustomTooltip = ({ active, payload }) => {
  if (active && payload?.length) {
    const d = payload[0]
    return (
      <div style={{
        background:'var(--card)', border:'1px solid var(--border)',
        borderRadius:8, padding:'8px 12px', fontSize:'12px',
        fontFamily:"'IBM Plex Mono',monospace"
      }}>
        <p style={{color:'var(--text)', fontWeight:500}}>{LANG_NAMES[d.payload.lang] || d.payload.lang}</p>
        <p style={{color:d.color}}>{d.value} orders</p>
      </div>
    )
  }
  return null
}

export default function LangChart({ distribution }) {
  const data = Object.entries(distribution || {}).map(([lang, count]) => ({
    lang, name: LANG_NAMES[lang] || lang, count
  }))

  return (
    <div>
      <h3 className="font-display" style={{
        fontSize:'14px', fontWeight:600, color:'var(--text)',
        marginBottom:4, letterSpacing:'-0.01em'
      }}>
        Language Breakdown
      </h3>
      <p style={{fontSize:'11px', color:'var(--subtext)', marginBottom:20,
                 fontFamily:"'IBM Plex Mono',monospace"}}>
        By confirmed orders
      </p>

      {data.length === 0 ? (
        <div style={{textAlign:'center', color:'var(--muted)', fontSize:'12px',
                     fontFamily:"'IBM Plex Mono',monospace", padding:'40px 0'}}>
          No data yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} layout="vertical" margin={{left:0, right:16}}>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" width={72}
                   tick={{fill:'var(--subtext)', fontSize:12, fontFamily:"'IBM Plex Mono',monospace"}} />
            <Tooltip content={<CustomTooltip />} cursor={{fill:'rgba(255,255,255,0.04)'}} />
            <Bar dataKey="count" radius={[0,4,4,0]}>
              {data.map((d) => (
                <Cell key={d.lang} fill={COLORS[d.lang] || '#60A5FA'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}

      <div style={{marginTop:16, display:'flex', flexDirection:'column', gap:8}}>
        {data.map(d => (
          <div key={d.lang} style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <div style={{display:'flex', alignItems:'center', gap:8}}>
              <div style={{width:10, height:10, borderRadius:2, background:COLORS[d.lang]||'#60A5FA'}} />
              <span style={{fontSize:'12px', color:'var(--subtext)'}}>{d.name}</span>
            </div>
            <span style={{
              fontFamily:"'IBM Plex Mono',monospace", fontSize:'12px',
              color:COLORS[d.lang]||'#60A5FA', fontWeight:500
            }}>{d.count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
