import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import StatCard from '../components/StatCard.jsx'
import RunTriggerModal from '../components/RunTriggerModal.jsx'

const statusMap = {
  pending: { label: '等待中', cls: 'badge-pending' },
  running: { label: '执行中', cls: 'badge-running' },
  passed:  { label: '通过', cls: 'badge-passed' },
  failed:  { label: '失败', cls: 'badge-failed' },
  error:   { label: '异常', cls: 'badge-error' },
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [showTrigger, setShowTrigger] = useState(false)

  const loadStats = useCallback(async () => {
    try {
      const res = await api.getDashboard()
      if (res?.data) setStats(res.data)
    } catch {}
  }, [])

  useEffect(() => { loadStats() }, [loadStats])

  const passRatePct = stats ? `${(stats.pass_rate * 100).toFixed(1)}%` : '—'

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">仪表盘</h2>
        <button
          onClick={() => setShowTrigger(true)}
          className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <span>▶</span> 新建执行
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard title="总执行次数" value={stats?.runs_total ?? '—'} icon="📊" color="blue" />
        <StatCard title="通过率" value={passRatePct} icon="📈" color="green" />
        <StatCard title="缓存用例数" value={stats?.case_count ?? '—'} icon="📋" color="purple" />
        <StatCard
          title="最近执行"
          value={stats?.latest_run ? statusMap[stats.latest_run.status]?.label : '无'}
          icon={stats?.latest_run?.status === 'passed' ? '✅' : '❌'}
          color={stats?.latest_run?.status === 'passed' ? 'green' : 'red'}
          subtitle={stats?.latest_run?.run_tag}
        />
      </div>

      {/* 最近执行列表 */}
      <div>
        <h3 className="text-lg font-semibold mb-3">最近执行</h3>
        {stats?.recent_runs?.length > 0 ? (
          <div className="bg-surface rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="py-2 px-4">标签</th>
                  <th className="py-2 px-4">环境</th>
                  <th className="py-2 px-4">标记</th>
                  <th className="py-2 px-4">通过/失败</th>
                  <th className="py-2 px-4">状态</th>
                  <th className="py-2 px-4">耗时</th>
                  <th className="py-2 px-4">时间</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_runs.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => navigate(`/runs/${r.id}`)}
                    className="border-b border-gray-800 hover:bg-surface-light/50 cursor-pointer transition-colors"
                  >
                    <td className="py-2 px-4 font-mono text-xs">{r.run_tag}</td>
                    <td className="py-2 px-4 text-gray-400">{r.environment}</td>
                    <td className="py-2 px-4 text-gray-400">{r.markers || '—'}</td>
                    <td className="py-2 px-4">
                      <span className="text-emerald-400">{r.passed_tests}</span>
                      <span className="text-gray-600">/</span>
                      <span className="text-red-400">{r.failed_tests}</span>
                    </td>
                    <td className="py-2 px-4">
                      <span className={statusMap[r.status]?.cls || 'badge-pending'}>
                        {statusMap[r.status]?.label || r.status}
                      </span>
                    </td>
                    <td className="py-2 px-4 text-gray-400">{r.duration_sec ? `${r.duration_sec}s` : '—'}</td>
                    <td className="py-2 px-4 text-gray-500 text-xs">{r.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">暂无执行记录，点击"新建执行"开始</p>
        )}
      </div>

      <RunTriggerModal isOpen={showTrigger} onClose={() => setShowTrigger(false)} onSuccess={loadStats} />
    </div>
  )
}
