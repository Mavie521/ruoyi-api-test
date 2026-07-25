import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import RunTriggerModal from '../components/RunTriggerModal.jsx'

const statusMap = {
  pending: { label: '等待中', cls: 'badge-pending' },
  running: { label: '执行中', cls: 'badge-running' },
  passed:  { label: '通过', cls: 'badge-passed' },
  failed:  { label: '失败', cls: 'badge-failed' },
  error:   { label: '异常', cls: 'badge-error' },
}

export default function RunHistoryPage() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [showTrigger, setShowTrigger] = useState(false)
  const [polling, setPolling] = useState(null)

  const loadRuns = async (pg = page) => {
    try {
      const res = await api.getRuns(pg)
      if (res?.data) {
        setRuns(res.data.items || [])
        setTotal(res.data.total || 0)
      }
    } catch {}
  }

  useEffect(() => { loadRuns() }, [page])

  // 如果列表中有 running 的任务，开启轮询
  useEffect(() => {
    const hasRunning = runs.some((r) => r.status === 'running' || r.status === 'pending')
    if (hasRunning) {
      const interval = setInterval(() => loadRuns(), 2000)
      setPolling(interval)
    } else {
      if (polling) clearInterval(polling)
      setPolling(null)
    }
    return () => { if (polling) clearInterval(polling) }
  }, [runs])

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">执行历史</h2>
        <button
          onClick={() => setShowTrigger(true)}
          className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          ▶ 新建执行
        </button>
      </div>

      {runs.length === 0 ? (
        <p className="text-gray-500 text-center py-16">暂无执行记录</p>
      ) : (
        <>
          <div className="bg-surface rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="py-3 px-4">标签</th>
                  <th className="py-3 px-4">环境</th>
                  <th className="py-3 px-4">标记</th>
                  <th className="py-3 px-4">通过 / 失败 / 总数</th>
                  <th className="py-3 px-4">状态</th>
                  <th className="py-3 px-4">耗时</th>
                  <th className="py-3 px-4">时间</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => navigate(`/runs/${r.id}`)}
                    className="border-b border-gray-800 hover:bg-surface-light/50 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-4 font-mono text-xs">{r.run_tag}</td>
                    <td className="py-2.5 px-4 text-gray-400">{r.environment}</td>
                    <td className="py-2.5 px-4 text-gray-400">{r.markers || '—'}</td>
                    <td className="py-2.5 px-4">
                      <span className="text-emerald-400">{r.passed_tests}</span>
                      <span className="text-gray-600"> / </span>
                      <span className="text-red-400">{r.failed_tests}</span>
                      <span className="text-gray-600"> / </span>
                      <span className="text-gray-300">{r.total_tests}</span>
                    </td>
                    <td className="py-2.5 px-4">
                      <span className={statusMap[r.status]?.cls || 'badge-pending'}>
                        {statusMap[r.status]?.label || r.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-gray-400">{r.duration_sec ? `${r.duration_sec}s` : '—'}</td>
                    <td className="py-2.5 px-4 text-gray-500 text-xs">{r.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded text-sm border border-gray-700 hover:bg-surface-light disabled:opacity-30 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <span className="text-sm text-gray-400">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 rounded text-sm border border-gray-700 hover:bg-surface-light disabled:opacity-30 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}

      <RunTriggerModal isOpen={showTrigger} onClose={() => setShowTrigger(false)} onSuccess={() => loadRuns(1)} />
    </div>
  )
}
