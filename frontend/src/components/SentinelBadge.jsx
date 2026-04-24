export default function SentinelBadge({ active }) {
  if (!active) return null
  return <span>⚡ Sentinel</span>
}
