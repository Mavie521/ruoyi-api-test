import { useState, useEffect } from 'react'
import api from '../api/client.js'

export default function MockPage() {
  const [rules, setRules] = useState(null)
  const [logs, setLogs] = useState(null)
  const [tab, setTab] = useState('rules')
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', path: '', http_method: 'GET', status_code: 200, response_body: '{}', delay_ms: 0, description: '' })

  const loadRules = async () => {
    const res = await api.get('/api/mock/rules')
    if (res?.data?.rules) setRules(res.data.rules)
  }
  const loadLogs = async () => {
    const res = await api.get('/api/mock/logs')
    if (res?.data) setLogs(res.data)
  }

  const handleSave = async () => {
    if (editing?.id) {
      await api.put(`/api/mock/rules/${editing.id}`, form)
    } else {
      await api.post('/api/mock/rules', form)
    }
    setEditing(null)
    setForm({ name: '', path: '', http_method: 'GET', status_code: 200, response_body: '{}', delay_ms: 0, description: '' })
    loadRules()
  }

  const handleToggle = async (id) => { await api.put(`/api/mock/rules/${id}/toggle`); loadRules() }
  const handleDelete = async (id) => { if (!confirm('确定删除？')) return; await api.delete(`/api/mock/rules/${id}`); loadRules() }
  const handleClearLogs = async () => { if (!confirm('清空所有日志？')) return; await api.delete('/api/mock/logs'); loadLogs() }

  useEffect(() => { loadRules(); loadLogs() }, [])

  if (!rules) return <div className="p-6" />

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-xl font-bold">Mock 平台</h2>

      {/* Tab 切换 */}
      <div className="flex gap-2 border-b border-gray-700 pb-2">
        {['rules','logs'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${tab === t ? 'bg-surface text-primary border-b-2 border-primary' : 'text-gray-400 hover:text-gray-200'}`}>
            {t === 'rules' ? '📋 Mock 规则' : '📜 调用日志'}
          </button>
        ))}
      </div>

      {tab === 'rules' ? (
        <>
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-400">Mock 入口: <code className="text-primary bg-surface px-2 py-0.5 rounded text-xs">/mock/你的路径</code>（支持 GET/POST/PUT/DELETE/PATCH）</p>
            <button onClick={() => { setEditing({}); setForm({ name: '', path: '', http_method: 'GET', status_code: 200, response_body: '{}', delay_ms: 0, description: '' }) }}
              className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium">+ 新增规则</button>
          </div>

          {/* Rules table */}
          <div className="bg-surface rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="py-3 px-4">名称</th>
                  <th className="py-3 px-4">方法</th>
                  <th className="py-3 px-4">路径</th>
                  <th className="py-3 px-4">状态码</th>
                  <th className="py-3 px-4">延迟</th>
                  <th className="py-3 px-4">状态</th>
                  <th className="py-3 px-4">操作</th>
                </tr>
              </thead>
              <tbody>
                {rules.length === 0 ? (
                  <tr><td colSpan="7" className="py-8 text-center text-gray-500">暂无 Mock 规则</td></tr>
                ) : rules.map(r => (
                  <tr key={r.id} className="border-b border-gray-800 hover:bg-surface-light/50">
                    <td className="py-2.5 px-4 font-medium">{r.name}</td>
                    <td className="py-2.5 px-4"><span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded">{r.http_method}</span></td>
                    <td className="py-2.5 px-4 font-mono text-xs text-gray-300">/{r.path}</td>
                    <td className="py-2.5 px-4"><span className={r.status_code >= 400 ? 'badge-failed' : 'badge-passed'}>{r.status_code}</span></td>
                    <td className="py-2.5 px-4 text-gray-400">{r.delay_ms ? `${r.delay_ms}ms` : '—'}</td>
                    <td className="py-2.5 px-4">
                      <button onClick={() => handleToggle(r.id)}
                        className={`text-xs px-2 py-0.5 rounded ${r.enabled ? 'bg-emerald-900/50 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                        {r.enabled ? '启用' : '禁用'}
                      </button>
                    </td>
                    <td className="py-2.5 px-4 flex gap-2">
                      <button onClick={() => { setEditing(r); setForm({ name: r.name, path: r.path, http_method: r.http_method, status_code: r.status_code, response_body: r.response_body, delay_ms: r.delay_ms, description: r.description || '' }) }}
                        className="text-xs text-gray-400 hover:text-white">编辑</button>
                      <button onClick={() => handleDelete(r.id)} className="text-xs text-red-400 hover:text-red-300">删除</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <>
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-400">共 {logs?.total || 0} 条调用记录</p>
            <button onClick={handleClearLogs} className="text-xs text-red-400 hover:text-red-300">清空日志</button>
          </div>
          <div className="bg-surface rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  <th className="py-3 px-4">时间</th>
                  <th className="py-3 px-4">方法</th>
                  <th className="py-3 px-4">路径</th>
                  <th className="py-3 px-4">规则</th>
                  <th className="py-3 px-4">状态码</th>
                  <th className="py-3 px-4">命中</th>
                </tr>
              </thead>
              <tbody>
                {(logs?.items || []).length === 0 ? (
                  <tr><td colSpan="6" className="py-8 text-center text-gray-500">暂无调用日志</td></tr>
                ) : (logs?.items || []).map(l => (
                  <tr key={l.id} className="border-b border-gray-800 hover:bg-surface-light/50">
                    <td className="py-2 px-4 text-xs text-gray-500">{l.created_at}</td>
                    <td className="py-2 px-4"><span className="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded">{l.http_method}</span></td>
                    <td className="py-2 px-4 font-mono text-xs text-gray-300">/{l.path}</td>
                    <td className="py-2 px-4 text-gray-400">{l.rule_name || '—'}</td>
                    <td className="py-2 px-4"><span className={l.status_code >= 400 ? 'badge-failed' : 'badge-passed'}>{l.status_code}</span></td>
                    <td className="py-2 px-4">{l.matched ? <span className="badge-passed">✓</span> : <span className="badge-failed">✗</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* 编辑弹窗 */}
      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setEditing(null)}>
          <div className="bg-surface rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6 space-y-4 max-h-[85vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold">{editing.id ? '编辑规则' : '新增规则'}</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">名称</label>
                <input value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">HTTP 方法</label>
                <select value={form.http_method} onChange={e => setForm({...form, http_method: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary">
                  {['GET','POST','PUT','DELETE','PATCH'].map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs text-gray-400 mb-1">路径（不含 /mock/ 前缀）</label>
                <input value={form.path} onChange={e => setForm({...form, path: e.target.value})}
                  placeholder="api/user/info"
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">状态码</label>
                <input type="number" value={form.status_code} onChange={e => setForm({...form, status_code: parseInt(e.target.value) || 200})}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">延迟 (ms)</label>
                <input type="number" value={form.delay_ms} onChange={e => setForm({...form, delay_ms: parseInt(e.target.value) || 0})}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">响应 JSON</label>
              <textarea value={form.response_body} onChange={e => setForm({...form, response_body: e.target.value})}
                rows={6} className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm font-mono focus:outline-none focus:border-primary" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">描述（可选）</label>
              <input value={form.description} onChange={e => setForm({...form, description: e.target.value})}
                className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-primary" />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button onClick={() => setEditing(null)} className="px-4 py-2 rounded-lg text-sm border border-gray-600 hover:bg-surface-light">取消</button>
              <button onClick={handleSave} disabled={!form.name || !form.path}
                className="px-4 py-2 rounded-lg text-sm bg-primary hover:bg-primary-dark text-white disabled:opacity-50">保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
