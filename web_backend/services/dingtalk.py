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
    """任务完成时发送钉钉通知：三种场景不同文案"""
    config = get_dingtalk_config()
    if not config.get("enabled") or not config.get("webhook_url"):
        return False

    notify_on = config.get("notify_on", "all")
    if notify_on == "failed_only" and status == "passed":
        return False

    webhook_url = config["webhook_url"]
    secret = config.get("secret", "")

    if secret:
        timestamp = str(round(time.time() * 1000))
        sign = _sign(secret, timestamp)
        webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0%"

    # ── 按结果分三种消息模板 ──
    if status == "passed" and failed == 0:
        title = f"✅ 测试通过 — {run_tag}"
        text = (
            f"## ✅ 全部通过\n\n"
            f"**任务**: {run_tag}\n\n"
            f"> 用例总数: {total}\n"
            f"> 通过: {passed}  |  失败: {failed}\n"
            f"> 通过率: {pass_rate}\n"
            f"> 耗时: {duration:.1f}s\n"
        )
    elif status == "passed" and failed > 0:
        title = f"⚠️ 部分通过 — {run_tag}"
        text = (
            f"## ⚠️ 部分通过\n\n"
            f"**任务**: {run_tag}\n\n"
            f"> 用例总数: {total}\n"
            f"> <font color=\"#00BB00\">通过: {passed}</font>  |  "
            f"<font color=\"#DD0000\">失败: {failed}</font>\n"
            f"> 通过率: {pass_rate}\n"
            f"> 耗时: {duration:.1f}s\n"
        )
    else:
        title = f"❌ 测试失败 — {run_tag}"
        text = (
            f"## ❌ 存在失败\n\n"
            f"**任务**: {run_tag}\n\n"
            f"> 用例总数: {total}\n"
            f"> 通过: {passed}  |  "
            f"<font color=\"#DD0000\">失败: {failed}</font>\n"
            f"> 通过率: {pass_rate}\n"
            f"> 耗时: {duration:.1f}s\n"
        )

    if report_url:
        text += f"\n---\n📊 [查看 Allure 报告]({report_url})"

    body = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}

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
