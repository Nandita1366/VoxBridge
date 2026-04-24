import CallCard from './CallCard.jsx'

export default function CallFeed({ calls }) {
  if (calls.length === 0) {
    return (
      <div style={{
        display:'flex', flexDirection:'column', alignItems:'center',
        justifyContent:'center', height:300, color:'var(--muted)',
        gap:12
      }}>
        <span style={{fontSize:48}}>📵</span>
        <p style={{fontFamily:"'IBM Plex Mono',monospace", fontSize:'13px'}}>
          Waiting for incoming calls...
        </p>
        <p style={{fontSize:'12px', color:'var(--muted)'}}>
          Configure Twilio webhook → {window.location.origin.replace('3000','8000')}/voice/inbound
        </p>
      </div>
    )
  }
  return (
    <div>
      {calls.map(call => <CallCard key={call.call_sid} call={call} />)}
    </div>
  )
}
