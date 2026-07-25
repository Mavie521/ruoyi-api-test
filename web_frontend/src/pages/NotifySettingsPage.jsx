import { useState, useEffect } from 'react'
import api from '../api/client.js'

export default function NotifySettingsPage() {
  const [config, setConfig] = useState(null)
  const [form, setForm] = useState({ webhook_url: '', secret: '', enabled: 0, notify_on: 'all' })
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [msg, setMsg] = useState('')

  const load = async () => {
    const res = await api.get('/api/notify/dingtalk/config')
    if (res?.data) {
      setConfig(res.data)
      setForm({ webhook_url: res.data.webhook_url || '', secret: res.data.secret || '', enabled: res.data.enabled || 0, notify_on: res.data.notify_on || 'all' })
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setMsg('')
    try {
      await api.put('/api/notify/dingtalk/config', form)
      setMsg('已保存')
      load()
    } catch (e) { setMsg('保存失败: ' + e.message) }
    setSaving(false)
  }

  const handleTest = async () => {
    setTesting(true)
    setMsg('')
    try {
      const res = await api.post('/api/notify/dingtalk/test')
      setMsg(res.message)
    } catch (e) { setMsg('发送失败: ' + e.message) }
    setTesting(false)
  }

  useEffect(() => { load() }, [])

  if (!config) return <div className="p-6" />

  return (
    <div className="p-6 space-y-6 max-w-3xl mx-auto">
      <h2 className="text-xl font-bold">钉钉通知配置</h2>

      <div className="bg-surface rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Webhook URL</label>
          <input type="text" value={form.webhook_url} onChange={(e) => setForm({ ...form, webhook_url: e.target.value })}
            placeholder="https://oapi.dingtalk.com/robot/send?access_token=..."
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary placeholder-gray-600" />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">加签 Secret（可选）</label>
          <input type="text" value={form.secret} onChange={(e) => setForm({ ...form, secret: e.target.value })}
            placeholder="SEC..."
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary placeholder-gray-600" />
        </div>

        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-gray-400">
            <input type="checkbox" checked={form.enabled === 1} onChange={(e) => setForm({ ...form, enabled: e.target.checked ? 1 : 0 })}
              className="rounded accent-primary" />
            启用通知
          </label>

          <div>
            <label className="text-sm text-gray-400 mr-2">通知条件</label>
            <select value={form.notify_on} onChange={(e) => setForm({ ...form, notify_on: e.target.value })}
              className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-primary">
              <option value="all">全部通知</option>
              <option value="failed_only">仅失败通知</option>
            </select>
          </div>
        </div>

        {msg && <div className={`text-sm px-3 py-2 rounded-lg ${msg.includes('失败') ? 'bg-red-900/50 text-red-300' : 'bg-emerald-900/50 text-emerald-300'}`}>{msg}</div>}

        <div className="flex gap-3 pt-2">
          <button onClick={handleSave} disabled={saving}
            className="bg-primary hover:bg-primary-dark text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
            {saving ? '保存中...' : '保存配置'}
          </button>
          <button onClick={handleTest} disabled={testing || !form.webhook_url}
            className="bg-surface hover:bg-surface-light border border-gray-600 text-gray-200 px-5 py-2 rounded-lg text-sm transition-colors disabled:opacity-50">
            {testing ? '发送中...' : '发送测试消息'}
          </button>
        </div>
      </div>

      <div className="bg-surface rounded-lg p-4 text-xs text-gray-500 space-y-1">
        <p>1. 在钉钉群设置中添加自定义机器人（Webhook 方式）</p>
        <p>2. 复制 Webhook URL 粘贴到上方输入框</p>
        <p>3. 如开启了加签，复制 Secret 填入</p>
        <p>4. 保存后点击"发送测试消息"验证配置是否正确</p>
        <p>5. 每次测试任务完成后将自动推送通知</p>
      </div>
    </div>
  )
}
