# CLAUDE.md — 若依API测试管理平台

## 项目定位
React + FastAPI + SQLite 接口测试管理平台，12小时三阶段全栈交付，面试展示用。

## 核心约束（不可违反）
1. **pytest 框架一字不改** — api/ tests/ config/ utils/ conftest.py run.py 只读
2. **subprocess 调度 pytest** — 不直接 import pytest
3. **前后端分离** — HTTP JSON 通信，FastAPI 直接 serve dist/
4. **密钥不进代码** — AI_API_KEY / ENCRYPTION_KEY 仅环境变量，不存 config.py 不存 DB
5. **Windows 开发 → Linux 生产** — 双平台兼容

## 目录结构
```
ruoyi-api-test/
├── api/              # pytest 原有代码，不改
├── tests/            # pytest 测试用例，不改
├── config/           # 原有配置，不改
├── utils/            # 原工具库 + crypto_utils.py（加密）
├── conftest.py       # 不改
├── web_backend/      # FastAPI（16文件）
│   ├── main.py       # 入口 + lifespan 清理 + 静态文件兜底
│   ├── config.py     # 路径常量 + AI/加密密钥（环境变量）
│   ├── database.py   # SQLite CRUD + 加密存取
│   ├── routers/      # project / run / report / notify / mock / env
│   └── services/     # collector / runner / parser / dingtalk / ai_analyzer
├── web_frontend/     # React 18 + Vite + Tailwind（19文件）
│   └── src/pages/    # Dashboard / TestCases / RunHistory / RunDetail / Report / Mock / Notify
├── cache/            # SQLite 数据库
└── reports/          # Allure 报告独立目录
```

## 常用命令
```bash
# 本地启动
cd web_frontend && npm run build && cd ..
uvicorn web_backend.main:app --host 0.0.0.0 --port 8001

# 服务器部署
ssh yy@192.168.149.100
cd ~/ruoyi-api-test && git pull
cd ~/ruoyi-api-test/web_frontend && npm run build && cd ..
pkill -f uvicorn ; sleep 1 && nohup uvicorn web_backend.main:app --host 0.0.0.0 --port 8001 > /dev/null 2>&1 &

# 数据库直查
python -c "import sqlite3; r=sqlite3.connect('cache/test_platform.db').execute('...').fetchall()"

# 生成 Fernet 密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 关键技术决策
| 决策 | 选择 | 原因 |
|------|------|------|
| subprocess | ThreadPoolExecutor + Popen | 跨平台，避开 ProactorEventLoop |
| 实时通信 | 2秒前端轮询 | 一期最简 |
| 鉴权 | 无 | 内网单人使用 |
| 加密 | Fernet (AES-128-CBC+HMAC) | 2行代码，面试加分 |
| 前端路由 | 404 exception_handler | 不拦截 API |
| 数据库 | SQLite | 零配置，标准库 |

## 敏感字段处理
- `dingtalk_config.secret` — Fernet 加密入库，API 返回掩码 `SEC****xxx`
- `dingtalk_config.webhook_url` — Fernet 加密入库，API 返回掩码 `...access_token=****xxx`
- 解密失败自动回退明文（兼容旧数据），下次保存自动转密文

## 已实现功能矩阵
| 阶段 | 功能 |
|------|------|
| 一 | 用例收集/浏览 · 异步执行 · 状态轮询 · Allure 报告 · 仪表盘 |
| 二 | 失败重跑 · 环境管理+健康探测 · 钉钉通知(加签+模板) · AI 失败分析 · 孤儿进程清理 |
| 三 | Mock 平台(规则引擎+通配符+日志+异常模拟) |

## API 端点（20+）
```
POST   /api/runs                触发执行
GET    /api/runs                执行历史
GET    /api/runs/{id}           执行详情
GET    /api/runs/{id}/status    轮询状态
POST   /api/runs/{id}/rerun-failed  重跑失败
POST   /api/runs/{id}/ai-analyze    AI分析
POST   /api/runs/clear-stuck    清除卡住任务
POST   /api/runs/debug-run      调试执行
DELETE /api/runs/{id}           删除记录
GET    /api/notify/config       钉钉配置
PUT    /api/notify/config       更新配置
POST   /api/notify/test         测试通知
GET    /api/projects/modules    用例模块
GET    /api/projects/cases      用例列表
POST   /api/projects/refresh    刷新缓存
GET    /api/environment/options 环境选项
GET    /api/reports/list        报告列表
ANY    /mock/{path}             Mock入口
GET    /api/dashboard/stats     仪表盘统计
GET    /api/health              健康检查
```

## Bug 修复总计：18 个
详见 phase1-review.html 幻灯片

## 下一步
- 幂等性（防重提交 client_token）
- HTTPS 反代（Caddy/Nginx）
- CLAUDE.md 完善
