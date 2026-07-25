import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: '仪表盘', icon: '📊', end: true },
  { to: '/tests', label: '用例浏览', icon: '📋' },
  { to: '/runs', label: '执行历史', icon: '📜' },
  { to: '/reports', label: '测试报告', icon: '📈' },
]

const toolItems = [
  { to: '/environments', label: '环境管理', icon: '🔧' },
  { to: '/settings/notify', label: '钉钉通知', icon: '🔔' },
  { to: '/mock', label: 'Mock 平台', icon: '🎭' },
]

export default function Layout({ children }) {
  return (
    <div className="flex h-screen">
      {/* 侧边栏 */}
      <aside className="w-56 bg-surface flex-shrink-0 flex flex-col border-r border-gray-700">
        <div className="p-5 border-b border-gray-700">
          <h1 className="text-lg font-bold text-primary flex items-center gap-2">
            <span>🧪</span> @Mavie521
          </h1>
          <p className="text-xs text-gray-400 mt-1">Web 测试管理平台</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary/20 text-primary font-medium'
                    : 'text-gray-400 hover:bg-surface-light hover:text-gray-200'
                }`
              }
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
          <div className="pt-3 mt-3 border-t border-gray-700">
            <p className="px-3 py-1 text-xs text-gray-500 uppercase tracking-wider">工具</p>
            {toolItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-primary/20 text-primary font-medium'
                      : 'text-gray-400 hover:bg-surface-light hover:text-gray-200'
                  }`
                }
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>
        <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
          v1.0.0 · 无鉴权模式
        </div>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto bg-gray-950">
        {children}
      </main>
    </div>
  )
}
