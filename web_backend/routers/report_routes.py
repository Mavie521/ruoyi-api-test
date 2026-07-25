"""
报告服务 — Allure 报告列表 + 离线 HTML 静态文件服务

接口:
  GET /api/reports/list          — 可用报告列表
  GET /api/reports/{tag}         — 重定向到报告 index.html
  GET /api/reports/{tag}/{path}  — 服务报告静态资源

报告存储路径: reports/allure-report-{run_tag}/
"""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse
from ..config import REPORTS_DIR

router = APIRouter()


@router.get("/list")
async def list_reports():
    """列出所有可用的 Allure 报告（按时间倒序）"""
    reports = []
    for d in sorted(REPORTS_DIR.glob("allure-report-*"), reverse=True):
        index_html = d / "index.html"
        if index_html.exists():
            tag = d.name.replace("allure-report-", "")
            reports.append({
                "tag": tag,
                "path": f"/api/reports/{tag}",
                "created_ts": d.stat().st_mtime,
            })

    return {
        "code": 200,
        "message": "success",
        "data": {"reports": reports},
    }


@router.get("/{tag}")
async def serve_report(tag: str):
    """服务 Allure 报告首页"""
    report_dir = REPORTS_DIR / f"allure-report-{tag}"
    index_path = report_dir / "index.html"
    if not index_path.exists():
        return {"code": 404, "message": f"报告 {tag} 不存在", "data": None}
    return FileResponse(str(index_path))


@router.get("/{tag}/{rest_path:path}")
async def serve_report_assets(tag: str, rest_path: str):
    """服务 Allure 报告的静态资源（JS/CSS/JSON/图片）"""
    report_dir = REPORTS_DIR / f"allure-report-{tag}"
    file_path = report_dir / rest_path
    # 安全检查：防止路径穿越
    try:
        file_path.resolve().relative_to(report_dir.resolve())
    except ValueError:
        return {"code": 403, "message": "禁止访问", "data": None}
    if not file_path.exists():
        return {"code": 404, "message": "文件不存在", "data": None}
    return FileResponse(str(file_path))
