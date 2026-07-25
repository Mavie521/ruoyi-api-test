"""钉钉通知配置"""
from fastapi import APIRouter
from pydantic import BaseModel
from ..database import get_dingtalk_config, update_dingtalk_config
from ..services.dingtalk import send_notification

router = APIRouter()


class DingTalkConfigRequest(BaseModel):
    webhook_url: str = ""
    secret: str = ""
    enabled: int = 0
    notify_on: str = "all"


@router.get("/config")
async def get_config():
    return {"code": 200, "message": "success", "data": get_dingtalk_config()}


@router.put("/config")
async def update_config(req: DingTalkConfigRequest):
    update_dingtalk_config(
        webhook_url=req.webhook_url,
        secret=req.secret,
        enabled=req.enabled,
        notify_on=req.notify_on,
    )
    return {"code": 200, "message": "已更新", "data": None}


@router.post("/test")
async def test_notify():
    """发送测试消息"""
    ok = send_notification(
        run_tag="test-message",
        status="passed",
        total=1, passed=1, failed=0,
        duration=0.1,
        report_url="",
        force=True,  # 测试发送跳过 enabled 检查
    )
    return {"code": 200, "message": "测试消息已发送" if ok else "发送失败，请检查配置", "data": {"sent": ok}}
