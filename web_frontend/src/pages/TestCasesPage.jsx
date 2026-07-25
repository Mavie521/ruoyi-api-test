import { useState, useEffect } from 'react'
import api from '../api/client.js'

export default function TestCasesPage() {
  const [modules, setModules] = useState([])
  const [cases, setCases] = useState([])
  const [selectedModule, setSelectedModule] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [message, setMessage] = useState('')

  // 加载模块列表
  const loadModules = async () => {
    setLoading(true)
    try {
      const res = await api.getModules()
      if (res?.data?.modules) {
        setModules(res.data.modules)
      }
    } catch {}
    setLoading(false)
  }

  // 加载模块下的用例
  const loadCases = async (module) => {
    setSelectedModule(module)
    setLoading(true)
    try {
      const res = await api.getCases(module)
      if (res?.data?.cases) {
        setCases(res.data.cases)
      } else {
        setCases([])
      }
    } catch {}
    setLoading(false)
  }

  // 刷新用例缓存
  const handleRefresh = async () => {
    setRefreshing(true)
    setMessage('')
    try {
      const res = await api.refreshCases()
      setMessage(res.message || `已刷新，共 ${res.data?.count} 条用例`)
      await loadModules()
      if (selectedModule) await loadCases(selectedModule)
    } catch (err) {
      setMessage(`刷新失败: ${err.message}`)
    }
    setRefreshing(false)
  }

  useEffect(() => { loadModules() }, [])

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">用例浏览</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="bg-surface hover:bg-surface-light border border-gray-600 text-gray-200 px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-50"
        >
          {refreshing ? '🔄 收集用例中...' : '🔄 手动刷新用例'}
        </button>
      </div>

      {message && (
        <div className="bg-primary/10 border border-primary/30 rounded-lg px-4 py-2 text-sm text-primary">
          {message}
        </div>
      )}

      <div className="flex gap-4">
        {/* 左侧模块列表 */}
        <div className="w-64 flex-shrink-0 bg-surface rounded-lg p-3 space-y-1 max-h-[70vh] overflow-auto">
          <h3 className="text-xs text-gray-400 uppercase tracking-wider px-3 py-2">测试模块</h3>
          {modules.length === 0 && !loading && (
            <p className="text-gray-500 text-sm px-3 py-4">
              暂无用例缓存，请点击"手动刷新用例"
            </p>
          )}
          {modules.map((m) => (
            <button
              key={m.module}
              onClick={() => loadCases(m.module)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex justify-between items-center ${
                selectedModule === m.module
                  ? 'bg-primary/20 text-primary font-medium'
                  : 'text-gray-300 hover:bg-surface-light'
              }`}
            >
              <span className="truncate">{m.module}</span>
              <span className="text-xs text-gray-500 ml-2">{m.case_count}</span>
            </button>
          ))}
        </div>

        {/* 右侧用例列表 */}
        <div className="flex-1 bg-surface rounded-lg p-4 min-h-[300px]">
          {selectedModule ? (
            <>
              <h3 className="text-sm font-semibold text-gray-300 mb-3">
                {selectedModule} <span className="text-gray-500 font-normal">({cases.length} 条用例)</span>
              </h3>
              {loading ? (
                <div className="p-6" />
              ) : cases.length === 0 ? (
                <p className="text-gray-500 text-center py-8">该模块下暂无用例（或缓存为空）</p>
              ) : (
                <div className="space-y-1">
                  {cases.map((c) => (
                    <div key={c.nodeid} className="flex items-start gap-3 px-3 py-2 rounded hover:bg-surface-light/50 transition-colors">
                      <span className="text-emerald-400 mt-0.5 text-sm">●</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-gray-200">{c.func_name}</div>
                        <div className="text-xs text-gray-500 truncate">{c.nodeid}</div>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {c.markers?.map((marker) => (
                          <span key={marker} className="bg-primary/10 text-primary text-xs px-1.5 py-0.5 rounded">
                            {marker}
                          </span>
                        ))}
                        {c.class_name && (
                          <span className="text-gray-500 text-xs ml-1">{c.class_name}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 text-sm">
              ← 请选择左侧测试模块查看用例
            </div>
          )}
        </div>
      </div>

      <p className="text-xs text-gray-600 mt-4">
        用例列表来自 SQLite 缓存（通过 pytest --collect-only 收集）。如测试代码有变更，请点击"手动刷新用例"按钮更新缓存。
      </p>
    </div>
  )
}
