"""
用例浏览 — 模块列表 + 用例列表 + 手动刷新缓存

接口:
  GET  /api/projects/modules           — 模块列表（从缓存读）
  GET  /api/projects/cases?module=xxx  — 模块下用例列表（从缓存读）
  POST /api/projects/refresh           — 刷新用例缓存（调 pytest --collect-only）
"""
from fastapi import APIRouter, HTTPException
from ..database import get_modules, get_cases_by_module
from ..services.collector import refresh_case_cache

router = APIRouter()


@router.get("/modules")
async def list_modules():
    """列出所有测试模块及用例数量"""
    modules = get_modules()
    return {"code": 200, "message": "success", "data": {"modules": modules}}


@router.get("/cases")
async def list_cases(module: str):
    """获取指定模块下的所有用例"""
    cases = get_cases_by_module(module)
    if not cases:
        # 可能是缓存为空或模块名不对
        return {"code": 200, "message": "该模块下无用例（或缓存未刷新）", "data": {"cases": []}}
    return {"code": 200, "message": "success", "data": {"module": module, "cases": cases}}


@router.post("/refresh")
async def refresh_cases():
    """手动刷新用例缓存（调用 pytest --collect-only）"""
    result = refresh_case_cache()
    if result["count"] == 0:
        raise HTTPException(status_code=500, detail=result["message"])
    return {"code": 200, "message": result["message"], "data": {"count": result["count"]}}
