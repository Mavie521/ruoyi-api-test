import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/client.js'

export default function ReportPage() {
  const [searchParams] = useSearchParams()
  const [reports, setReports] = useState([])
  const [selectedTag, setSelectedTag] = useState(searchParams.get('tag') || '')
  const [loading, setLoading] = useState(false)

  const loadReports = async () => {
    setLoading(true)
    try {
      const res = await api.getReports()
      if (res?.data?.reports) {
        setReports(res.data.reports)
        // 如果 URL 带了 tag 且没选中，自动选中
        const tagFromUrl = searchParams.get('tag')
        if (tagFromUrl && !selectedTag) {
          setSelectedTag(tagFromUrl)
        }
      }
    } catch {}
    setLoading(false)
  }

  useEffect(() => { loadReports() }, [])

  const formatTime = (ts) => {
    if (!ts) return '—'
    return new Date(ts * 1000).toLocaleString('zh-CN')
  }

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-bold">测试报告</h2>

      {selectedTag ? (
        /* 查看报告 */
        <div className="space-y-3">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSelectedTag('')}
              className="text-gray-400 hover:text-white transition-colors text-sm"
            >
              ← 返回列表
            </button>
            <span className="text-sm text-gray-300 font-mono">{selectedTag}</span>
            <a
              href={`/api/reports/${selectedTag}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline text-sm"
            >
              新标签页打开 ↗
            </a>
          </div>
          <iframe
            src={`/api/reports/${selectedTag}`}
            className="w-full rounded-lg border border-gray-700"
            style={{ height: 'calc(100vh - 200px)', minHeight: '600px' }}
            title="Allure Report"
          />
        </div>
      ) : (
        /* 报告列表 */
        <>
          <button
            onClick={loadReports}
            disabled={loading}
            className="self-start bg-surface hover:bg-surface-light border border-gray-600 text-gray-200 px-4 py-2 rounded-lg text-sm transition-colors"
          >
            {loading ? '加载中...' : '🔄 刷新列表'}
          </button>

          {reports.length === 0 ? (
            <div className="text-gray-500 text-center py-16 space-y-2">
              <p className="text-4xl">📭</p>
              <p>暂无可用报告</p>
              <p className="text-xs">执行测试任务完成后，Allure 报告将自动生成并出现在此列表中</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {reports.map((r) => (
                <div
                  key={r.tag}
                  onClick={() => setSelectedTag(r.tag)}
                  className="bg-surface rounded-lg p-4 flex items-center justify-between hover:bg-surface-light/50 cursor-pointer transition-colors border border-gray-800 hover:border-gray-700"
                >
                  <div>
                    <div className="font-mono text-sm font-medium">{r.tag}</div>
                    <div className="text-xs text-gray-500 mt-1">{formatTime(r.created_ts)}</div>
                  </div>
                  <span className="text-primary text-sm">查看报告 →</span>
                </div>
              ))}
            </div>
          )}

          <p className="text-xs text-gray-600 mt-4">
            报告位于 reports/allure-report-{"{run_tag}"}/ 目录。每条任务独立存储，历史报告不覆盖。
            点击报告可在此页面内嵌 iframe 查看，也可新标签页打开。
          </p>
        </>
      )}
    </div>
  )
}
