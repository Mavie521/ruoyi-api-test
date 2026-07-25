import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client.js'
import StatCard from '../components/StatCard.jsx'
import ResultTable from '../components/ResultTable.jsx'

const statusMap = {
  pending: { label: '等待中', cls: 'badge-pending' },
  running: { label: '执行中', cls: 'badge-running' },
  passed:  { label: '✅ 全部通过', cls: 'badge-passed' },
  failed:  { label: '❌ 存在失败', cls: 'badge-failed' },
  error:   { label: '⚠ 执行异常', cls: 'badge-error' },
}

export default function RunDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [run, setRun] = useState(null)
  const [filterOutcome, setFilterOutcome] = useState('')
  const pollingRef = useRef(null)

  const loadDetail = async () => {
    try {
      const res = await api.getRunDetail(id)
      if (res?.data) setRun(res.data)
    } catch {}
  }

  const loadStatus = async () => {
    try {
      const res = await api.getRunStatus(id)
      if (res?.data) {
        setRun((prev) => prev ? { ...prev, ...res.data } : prev)
        if (res.data.status !== 'running' && res.data.status !== 'pending') {
          // 执行完毕，停止轮询，加载完整结果
          clearInterval(pollingRef.current)
          pollingRef.current = null
          loadDetail()
        }
      }
    } catch {}
  }

  useEffect(() => {
    loadDetail()
    // 启动 2 秒轮询
    pollingRef.current = setInterval(loadStatus, 2000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [id])

  if (!run) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="p-6" />
      </div>
    )
  }

  const results = run.results || []
  const filtered = filterOutcome
    ? results.filter((r) => r.outcome === filterOutcome)
    : results

  return (
    <div className="p-6 space-y-6">
      {/* 顶部导航 */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/runs')}
          className="text-gray-400 hover:text-white transition-colors"
        >
          ← 返回历史
        </button>
        <h2 className="text-xl font-bold">{run.run_tag}</h2>
        <span className={statusMap[run.status]?.cls || 'badge-pending'}>
          {statusMap[run.status]?.label || run.status}
        </span>
      </div>

      {/* 元信息 */}
      <div className="flex gap-6 text-sm text-gray-400">
        <span>环境: <span className="text-gray-200">{run.environment}</span></span>
        <span>标记: <span className="text-gray-200">{run.markers || '—'}</span></span>
        {run.keyword && <span>关键字: <span className="text-gray-200">{run.keyword}</span></span>}
        {run.test_path && <span>路径: <span className="text-gray-200">{run.test_path}</span></span>}
        {run.started_at && <span>开始: <span className="text-gray-200">{run.started_at}</span></span>}
        {run.finished_at && <span>结束: <span className="text-gray-200">{run.finished_at}</span></span>}
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-5 gap-3">
        <StatCard title="总计" value={run.total_tests || 0} icon="📊" color="blue" />
        <StatCard title="通过" value={run.passed_tests || 0} icon="✅" color="green" />
        <StatCard title="失败" value={run.failed_tests || 0} icon="❌" color="red" />
        <StatCard title="跳过" value={run.skipped_tests || 0} icon="⏭" color="yellow" />
        <StatCard title="耗时" value={run.duration_sec ? `${run.duration_sec}s` : '—'} icon="⏱" color="purple" />
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center gap-3">
        {/* 查看报告 */}
        {run.allure_dir && (
          <>
            <button
              onClick={() => navigate(`/reports?tag=${run.run_tag}`)}
              className="bg-surface hover:bg-surface-light border border-gray-600 text-gray-200 px-4 py-2 rounded-lg text-sm transition-colors"
            >
              📊 查看 Allure 报告（iframe）
            </button>
            <a
              href={`/api/reports/${run.run_tag}`}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-surface hover:bg-surface-light border border-gray-600 text-gray-200 px-4 py-2 rounded-lg text-sm transition-colors"
            >
              🔗 新标签页打开报告
            </a>
          </>
        )}
        {/* 重跑失败用例 */}
        {run.failed_tests > 0 && run.status !== 'running' && (
          <>
            <button
              onClick={async () => {
                const res = await api.post(`/api/runs/${id}/rerun-failed`)
                if (res.code === 200) { alert(res.message); window.location.reload() }
                else alert(res.message || '重跑失败')
              }}
              className="bg-amber-700/30 hover:bg-amber-700/50 border border-amber-600 text-amber-300 px-4 py-2 rounded-lg text-sm transition-colors"
            >
              🔄 重跑失败用例 ({run.failed_tests})
            </button>
            <button
              onClick={async () => {
                const res = await api.post(`/api/runs/${id}/ai-analyze`)
                alert(res.message || '分析完成')
                loadDetail()
              }}
              className="bg-purple-900/30 hover:bg-purple-900/50 border border-purple-700 text-purple-300 px-4 py-2 rounded-lg text-sm transition-colors"
            >
              🤖 AI 分析失败原因
            </button>
          </>
        )}
      </div>

      {/* 结果过滤 */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">过滤:</span>
        {['', 'passed', 'failed', 'skipped', 'error'].map((outcome) => (
          <button
            key={outcome}
            onClick={() => setFilterOutcome(outcome)}
            className={`px-3 py-1 rounded text-xs transition-colors ${
              filterOutcome === outcome
                ? 'bg-primary/30 text-primary'
                : 'bg-surface text-gray-400 hover:text-gray-200'
            }`}
          >
            {outcome === '' ? `全部 (${results.length})` : outcome}
          </button>
        ))}
      </div>

      {/* 结果表格 */}
      <ResultTable results={filtered} />

      {/* 执行输出（可折叠） */}
      {run.output_log && (
        <details className="mt-4">
          <summary className="text-sm text-gray-400 cursor-pointer hover:text-gray-200">
            📜 查看完整执行日志
          </summary>
          <pre className="log-terminal mt-2">{run.output_log}</pre>
        </details>
      )}
    </div>
  )
}
