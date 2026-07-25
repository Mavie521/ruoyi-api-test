"""Mock 平台 —— 规则管理 + 调用日志查询"""
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..database import (
    list_mock_rules, get_mock_rule, create_mock_rule, update_mock_rule,
    delete_mock_rule, toggle_mock_rule, list_mock_logs, clear_mock_logs,
)

router = APIRouter()


class MockRuleRequest(BaseModel):
    name: str
    path: str
    http_method: str = "GET"
    status_code: int = 200
    response_body: str = "{}"
    delay_ms: int = 0
    description: str = ""


# ── 规则 CRUD ──
@router.get("/rules")
async def get_rules():
    return {"code": 200, "message": "success", "data": {"rules": list_mock_rules()}}


@router.post("/rules")
async def create_rule(req: MockRuleRequest):
    rid = create_mock_rule(
        name=req.name, path=req.path, http_method=req.http_method,
        status_code=req.status_code, response_body=req.response_body,
        delay_ms=req.delay_ms, description=req.description,
    )
    return {"code": 200, "message": "已创建", "data": {"id": rid}}


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: int, req: MockRuleRequest):
    if not get_mock_rule(rule_id):
        raise HTTPException(status_code=404, detail="规则不存在")
    update_mock_rule(
        rule_id, name=req.name, path=req.path, http_method=req.http_method,
        status_code=req.status_code, response_body=req.response_body,
        delay_ms=req.delay_ms, description=req.description,
    )
    return {"code": 200, "message": "已更新", "data": None}


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int):
    if not get_mock_rule(rule_id):
        raise HTTPException(status_code=404, detail="规则不存在")
    delete_mock_rule(rule_id)
    return {"code": 200, "message": "已删除", "data": None}


@router.put("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: int):
    rule = toggle_mock_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return {"code": 200, "message": f"已{'启用' if rule['enabled'] else '禁用'}", "data": rule}


# ── 调用日志 ──
@router.get("/logs")
async def get_logs(page: int = 1, page_size: int = 50):
    data = list_mock_logs(page=page, page_size=page_size)
    return {"code": 200, "message": "success", "data": data}


@router.delete("/logs")
async def clear_logs():
    clear_mock_logs()
    return {"code": 200, "message": "已清空", "data": None}
