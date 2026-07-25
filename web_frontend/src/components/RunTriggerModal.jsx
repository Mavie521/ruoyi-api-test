import { useState, useEffect } from 'react'
import api from '../api/client.js'

export default function RunTriggerModal({ isOpen, onClose, onSuccess }) {
  const [envOptions, setEnvOptions] = useState(['dev', 'staging', 'prod', 'docker'])
  const [form, setForm] = useState({
    environment: 'dev',
    markers: '',
    test_path: 'tests/',
    keyword: '',
    extra_args: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getEnvOptions()
      .then((res) => { if (res?.data?.options) setEnvOptions(res.data.options) })
      .catch(() => {})
  }, [])

  if (!isOpen) return null

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setError('')
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.triggerRun(form)
      if (res.code === 200) {
        onSuccess?.()
        onClose()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-surface rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-5 border-b border-gray-700">
          <h2 className="text-lg font-bold">触发测试执行</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">&times;</button>
        </div>

        <div className="p-5 space-y-4">
          {/* 环境 */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">测试环境</label>
            <select
              value={form.environment}
              onChange={(e) => handleChange('environment', e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
            >
              {envOptions.map((env) => (
                <option key={env} value={env}>{env}</option>
              ))}
            </select>
          </div>

          {/* Marker */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Marker 标记</label>
            <input
              type="text"
              value={form.markers}
              onChange={(e) => handleChange('markers', e.target.value)}
              placeholder="如: p0 / p0 and not slow / security"
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary placeholder-gray-600"
            />
          </div>

          {/* 测试路径 */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">测试路径</label>
            <input
              type="text"
              value={form.test_path}
              onChange={(e) => handleChange('test_path', e.target.value)}
              placeholder="tests/"
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary"
            />
          </div>

          {/* 关键字 */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">关键字过滤 (-k)</label>
            <input
              type="text"
              value={form.keyword}
              onChange={(e) => handleChange('keyword', e.target.value)}
              placeholder="如: login"
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary placeholder-gray-600"
            />
          </div>

          {/* 自定义参数 */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">自定义参数（自由输入）</label>
            <input
              type="text"
              value={form.extra_args}
              onChange={(e) => handleChange('extra_args', e.target.value)}
              placeholder="如: --maxfail=5 --tb=long"
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary placeholder-gray-600"
            />
            <p className="text-xs text-gray-500 mt-1">
              输入原始 pytest 参数，空格分隔。后端使用 list 方式组装命令，shell=False
            </p>
          </div>

          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 p-5 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm border border-gray-600 hover:bg-surface-light transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-5 py-2 rounded-lg text-sm bg-primary hover:bg-primary-dark text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '提交中...' : '确认执行'}
          </button>
        </div>
      </div>
    </div>
  )
}
