"""钉钉机器人推送 —— Webhook + 加签"""
import time
import hmac
import hashlib
import base64
import requests
from urllib.parse import quote_plus
from ..database import get_dingtalk_config


def send_notification(run_tag: str, status: str, total: int, passed: int,
                      failed: int, duration: float, report_url: str = "") -> bool:
    """任务完成时发送钉钉通知"""

    config = get_dingtalk_config()
    if not config.get("enabled") or not config.get("webhook_url"):
        return False

    notify_on = config.get("notify_on", "all")
    if notify_on == "failed_only" and status == "passed":
        return False  # 只通知失败，当前通过 → 跳过

    webhook_url = config["webhook_url"]
    secret = config.get("secret", "")

    # 加签
    if secret:
        timestamp = str(round(time.time() * 1000))
        sign = _sign(secret, timestamp)
        webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    # 构造消息
    pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"
    status_emoji = "✅" if status == "passed" else "❌"

    text = (
        f"{status_emoji} 测试任务完成\n\n"
        f"**任务标签**: {run_tag}\n"
        f"**最终状态**: {status}\n"
        f"**通过率**: {pass_rate}\n"
        f"**总数**: {total}  |  通过: {passed}  |  失败: {failed}\n"
        f"**耗时**: {duration:.1f}s\n"
    )
    if report_url:
        text += f"\n[查看 Allure 报告]({report_url})"

    body = {"msgtype": "markdown", "markdown": {"title": f"测试任务 {run_tag}", "text": text}}

    try:
        resp = requests.post(webhook_url, json=body, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _sign(secret: str, timestamp: str) -> str:
    """钉钉加签算法: HMAC-SHA256 → Base64 → URLEncode"""
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode("utf-8")
    return quote_plus(sign)
