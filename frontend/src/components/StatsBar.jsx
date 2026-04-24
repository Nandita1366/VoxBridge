export default function StatsBar({ stats }) {
  const items = [
    { label: 'Total Calls',       value: stats.total_calls,       color: 'var(--teal)' },
    { label: 'Orders Confirmed',  value: stats.confirmed_orders,  color: '#10B981' },
    { label: 'Escalations',       value: stats.escalations,       color: '#EF4444' },
    { label: 'Conversion Rate',
      value: stats.total_calls > 0
        ? Math.round((stats.confirmed_orders / stats.total_calls) * 100) + '%'
        : '-',
      color: '#F59E0B' }
  ]
  return (
    <div className="grid grid-cols-4 gap-px"
         style={{background:'var(--border)', borderBottom:'1px solid var(--border)'}}>
      {items.map(item => (
        <div key={item.label} className="flex flex-col gap-1 p-5"
             style={{background:'var(--surface)'}}>
          <span style={{fontSize:'11px', color:'var(--subtext)', textTransform:'uppercase',
                        letterSpacing:'0.08em', fontFamily:"'IBM Plex Mono',monospace"}}>
            {item.label}
          </span>
          <span style={{fontFamily:"'Syne',sans-serif", fontSize:'2rem',
                        fontWeight:700, color:item.color, lineHeight:1}}>
            {item.value}
          </span>
        </div>
      ))}
    </div>
  )
}
