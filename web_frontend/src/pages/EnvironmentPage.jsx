import { useState, useEffect } from 'react'
import api from '../api/client.js'

export default function EnvironmentPage() {
  const [envs, setEnvs] = useState(null)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', base_url: '', description: '' })
  const [pingResult, setPingResult] = useState({})

  const load = async () => {
    const res = await api.get('/api/environments')
    if (res?.data?.environments) setEnvs(res.data.environments)
  }

  const handleSave = async () => {
    if (editing?.id) {
      await api.put(`/api/environments/${editing.id}`, form)
    } else {
      await api.post('/api/environments', form)
    }
    setEditing(null)
    setForm({ name: '', base_url: '', description: '' })
    load()
  }

  const handleEdit = (env) => {
    setEditing(env)
    setForm({ name: env.name, base_url: env.base_url, description: env.description || '' })
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除？')) return
    await api.delete(`/api/environments/${id}`)
    load()
  }

  const handlePing = async (id) => {
    const res = await api.post(`/api/environments/${id}/ping`)
    if (res?.data) {
      setPingResult((prev) => ({ ...prev, [id]: res.data }))
    }
  }

  useEffect(() => { load() }, [])

  if (!envs) return <div className="p-6" />

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">环境管理</h2>
        <button onClick={() => { setEditing({}); setForm({ name: '', base_url: '', description: '' }) }}
          className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          + 新增环境
        </button>
      </div>

      {/* 编辑弹窗 */}
      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setEditing(null)}>
          <div className="bg-surface rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold">{editing.id ? '编辑环境' : '新增环境'}</h3>
            <input type="text" placeholder="名称 (如 dev/staging/prod)" value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            <input type="text" placeholder="Base URL (如 http://localhost:8080)" value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            <input type="text" placeholder="描述（可选）" value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary" />
            <div className="flex justify-end gap-3">
              <button onClick={() => setEditing(null)} className="px-4 py-2 rounded-lg text-sm border border-gray-600 hover:bg-surface-light">取消</button>
              <button onClick={handleSave} disabled={!form.name || !form.base_url}
                className="px-4 py-2 rounded-lg text-sm bg-primary hover:bg-primary-dark text-white disabled:opacity-50">保存</button>
            </div>
          </div>
        </div>
      )}

      {/* 环境列表 */}
      {envs.length === 0 ? (
        <p className="text-gray-500 text-center py-16">暂无环境配置</p>
      ) : (
        <div className="bg-surface rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 text-left">
                <th className="py-3 px-4">名称</th>
                <th className="py-3 px-4">Base URL</th>
                <th className="py-3 px-4">描述</th>
                <th className="py-3 px-4">状态</th>
                <th className="py-3 px-4">操作</th>
              </tr>
            </thead>
            <tbody>
              {envs.map((env) => (
                <tr key={env.id} className="border-b border-gray-800 hover:bg-surface-light/50">
                  <td className="py-2.5 px-4 font-medium">{env.name}</td>
                  <td className="py-2.5 px-4 font-mono text-xs text-gray-400">{env.base_url}</td>
                  <td className="py-2.5 px-4 text-gray-500">{env.description || '—'}</td>
                  <td className="py-2.5 px-4">
                    {pingResult[env.id] ? (
                      pingResult[env.id].alive
                        ? <span className="badge-passed">在线 ({pingResult[env.id].status_code})</span>
                        : <span className="badge-failed">不可达</span>
                    ) : (
                      <span className="text-gray-500">—</span>
                    )}
                  </td>
                  <td className="py-2.5 px-4 flex gap-2">
                    <button onClick={() => handlePing(env.id)} className="text-xs text-primary hover:underline">探测</button>
                    <button onClick={() => handleEdit(env)} className="text-xs text-gray-400 hover:text-white">编辑</button>
                    <button onClick={() => handleDelete(env.id)} className="text-xs text-red-400 hover:text-red-300">删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
