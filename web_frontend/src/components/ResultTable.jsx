const outcomeMap = {
  passed:  { label: '通过', cls: 'badge-passed' },
  failed:  { label: '失败', cls: 'badge-failed' },
  skipped: { label: '跳过', cls: 'badge-pending' },
  error:   { label: '错误', cls: 'badge-error' },
}

export default function ResultTable({ results = [] }) {
  if (results.length === 0) {
    return <p className="text-gray-500 text-center py-8">暂无结果数据</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700 text-gray-400 text-left">
            <th className="py-2 px-3 font-medium">用例名称</th>
            <th className="py-2 px-3 font-medium w-24">结果</th>
            <th className="py-2 px-3 font-medium w-20">耗时</th>
            <th className="py-2 px-3 font-medium">失败信息</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.id} className="border-b border-gray-800 hover:bg-surface-light/50 transition-colors">
              <td className="py-2 px-3">
                <div className="font-medium text-gray-200">{r.test_name}</div>
                {r.nodeid && <div className="text-xs text-gray-500 mt-0.5 truncate max-w-md">{r.nodeid}</div>}
              </td>
              <td className="py-2 px-3">
                <span className={outcomeMap[r.outcome]?.cls || 'badge-pending'}>
                  {outcomeMap[r.outcome]?.label || r.outcome}
                </span>
              </td>
              <td className="py-2 px-3 text-gray-400">{r.duration_sec}s</td>
              <td className="py-2 px-3">
                {r.message ? (
                  <details>
                    <summary className="text-red-400 cursor-pointer hover:text-red-300">
                      {r.message.split('\n')[0].slice(0, 80)}
                    </summary>
                    <pre className="text-xs text-gray-400 mt-1 whitespace-pre-wrap max-w-lg">{r.message}</pre>
                  </details>
                ) : (
                  <span className="text-gray-500">—</span>
                )}
                {r.ai_analysis && (
                  <div className="mt-1 p-2 bg-purple-900/20 border border-purple-800/40 rounded text-xs">
                    <span className="text-purple-400 font-medium">🤖 AI: </span>
                    <span className="text-gray-300">{r.ai_analysis}</span>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
