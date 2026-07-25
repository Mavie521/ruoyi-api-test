"""
若依API测试管理平台 — FastAPI 主入口

约定:
  - 业务路由注册在前，静态挂载在后，防止静态路由抢占 API 接口
  - 数据库文件在 cache/，报告在 reports/，路径统一通过 config.py 管理
  - 无鉴权，所有接口放开

启动:
  uvicorn web_backend.main:app --host 0.0.0.0 --port 8000 --reload
  API 文档: http://localhost:8000/docs
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import CORS_ORIGINS, PROJECT_ROOT, REPORTS_DIR
from .database import init_db, close_db
from .routers import project_routes, run_routes, report_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时建表，关闭时清理连接"""
    init_db()
    yield
    close_db()


app = FastAPI(
    title="若依API测试管理平台",
    description="基于 pytest 的 Web 测试管理平台 — 用例浏览 / 执行触发 / 状态轮询 / Allure 报告",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS（开发模式下允许 Vite :5173 跨域） ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 一期宽松策略
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 业务路由（注册在前，确保优先匹配） ──
app.include_router(project_routes.router, prefix="/api/projects", tags=["用例浏览"])
app.include_router(run_routes.router, prefix="/api/runs", tags=["执行管理"])
app.include_router(report_routes.router, prefix="/api/reports", tags=["报告服务"])


# ── 系统接口 ──
@app.get("/api/health", tags=["系统"])
async def health():
    """健康检查"""
    return {
        "code": 200, "message": "OK",
        "data": {
            "python": sys.version.split()[0],
            "project_root": str(PROJECT_ROOT),
            "db_location": "cache/test_platform.db",
            "reports_location": "reports/",
        },
    }


@app.get("/api/dashboard/stats", tags=["系统"])
async def dashboard_stats():
    """仪表盘统计数据"""
    from .database import get_dashboard_stats
    return {"code": 200, "message": "success", "data": get_dashboard_stats()}


@app.get("/api/environment/options", tags=["系统"])
async def env_options():
    """环境下拉选项（一期硬编码）"""
    from .config import ENV_OPTIONS
    return {"code": 200, "message": "success", "data": {"options": ENV_OPTIONS}}


# ── 静态文件挂载（注册在最后，防止抢占业务路由） ──

# Allure 报告静态服务（通过 /allure/{tag}/... 访问）
if REPORTS_DIR.exists():
    app.mount("/allure", StaticFiles(directory=str(REPORTS_DIR)), name="allure_static")

# 前端 SPA 静态文件（prod 模式下挂载）
frontend_dir = PROJECT_ROOT / "web_frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


# ── 直接运行入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web_backend.main:app", host="0.0.0.0", port=8000, reload=True)
