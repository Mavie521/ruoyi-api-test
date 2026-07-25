"""钉钉通知配置"""
from fastapi import APIRouter
from pydantic import BaseModel
from ..database import get_dingtalk_config, update_dingtalk_config
from ..services.dingtalk import send_notification

router = APIRouter()


def _mask_secret(s: str) -> str:
    """前端只展示掩码，防止浏览器端泄露"""
    if not s:
        return ""
    if len(s) > 8:
        return s[:3] + "****" + s[-4:]
    return "****"


def _mask_url(url: str) -> str:
    """Webhook URL 掩码 access_token"""
    if not url or "access_token=" not in url:
        return url
    # https://oapi.dingtalk.com/robot/send?access_token=xxx → access_token=***xxx
    prefix, token = url.rsplit("access_token=", 1)
    return f"{prefix}access_token=****{token[-4:]}"


class DingTalkConfigRequest(BaseModel):
    webhook_url: str = ""
    secret: str = ""
    enabled: int = 0
    notify_on: str = "all"


@router.get("/config")
async def get_config():
    config = get_dingtalk_config()
    config["secret"] = _mask_secret(config["secret"])
    config["webhook_url"] = _mask_url(config["webhook_url"])
    return {"code": 200, "message": "success", "data": config}


@router.put("/config")
async def update_config(req: DingTalkConfigRequest):
    updates = req.dict()
    # 前端未修改敏感字段（仍是掩码或空）→ 不更新
    if "****" in updates.get("secret", ""):
        del updates["secret"]
    if "****" in updates.get("webhook_url", ""):
        del updates["webhook_url"]
    update_dingtalk_config(**updates)
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
