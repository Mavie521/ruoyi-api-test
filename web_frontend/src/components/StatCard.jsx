export default function StatCard({ title, value, icon, color = 'blue', subtitle }) {
  const colors = {
    blue:   'border-l-blue-500',
    green:  'border-l-emerald-500',
    red:    'border-l-red-500',
    yellow: 'border-l-amber-500',
    purple: 'border-l-purple-500',
  }

  return (
    <div className={`bg-surface rounded-lg p-5 border-l-4 ${colors[color] || colors.blue}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{title}</span>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="text-3xl font-bold">{value}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  )
}
