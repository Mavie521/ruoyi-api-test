/**
 * API 客户端 — fetch 封装，统一 baseURL 和错误处理
 * 一期无鉴权，直接请求
 */

const BASE = '' // Vite proxy 转发 /api → localhost:8000

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  }
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }
  const res = await fetch(url, config)
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || data.message || `HTTP ${res.status}`)
  }
  return data
}

const api = {
  // 用例浏览
  getModules:       ()           => request('/api/projects/modules'),
  getCases:         (module)     => request(`/api/projects/cases?module=${encodeURIComponent(module)}`),
  refreshCases:     ()           => request('/api/projects/refresh', { method: 'POST' }),

  // 执行管理
  triggerRun:       (body)       => request('/api/runs', { method: 'POST', body }),
  getRuns:          (page = 1)   => request(`/api/runs?page=${page}`),
  getRunDetail:     (id)         => request(`/api/runs/${id}`),
  getRunStatus:     (id)         => request(`/api/runs/${id}/status`),

  // 报告
  getReports:       ()           => request('/api/reports/list'),

  // 系统
  getHealth:        ()           => request('/api/health'),
  getDashboard:     ()           => request('/api/dashboard/stats'),
  getEnvOptions:    ()           => request('/api/environment/options'),
}

export default api
