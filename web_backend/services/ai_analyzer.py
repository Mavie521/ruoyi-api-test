"""AI 失败分析 —— 调用 LLM API 分析测试失败原因"""
import json
import requests
from ..config import AI_ENABLED, AI_API_URL, AI_API_KEY, AI_MODEL


def analyze_failure(test_name: str, nodeid: str, error_message: str) -> str:
    """
    调用 AI API 分析单条失败用例

    参数:
      test_name:     用例名称
      nodeid:        pytest nodeid
      error_message: 错误堆栈信息

    返回:
      AI 分析文本，失败返回空字符串
    """
    if not AI_ENABLED or not AI_API_KEY:
        return ""

    # 截断过长的错误信息
    error_snippet = error_message[:1500] if error_message else "(无错误信息)"

    prompt = (
        f"你是软件测试专家。请用中文分析以下 pytest 测试失败的原因，"
        f"并用 2-3 句话给出修复建议。\n\n"
        f"测试用例: {test_name}\n"
        f"路径: {nodeid}\n"
        f"错误信息:\n{error_snippet}\n\n"
        f"请直接输出分析结果，不要开场白。"
    )

    try:
        resp = requests.post(
            AI_API_URL,
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是软件测试专家，擅长分析接口测试失败原因。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return ""


def analyze_failures_batch(failed_results: list) -> None:
    """
    批量分析失败用例并更新数据库（后台异步执行）

    failed_results: list of dicts with keys: id, test_name, nodeid, message
    """
    if not AI_ENABLED or not AI_API_KEY:
        return

    from ..database import update_result_analysis

    for result in failed_results:
        analysis = analyze_failure(
            test_name=result.get("test_name", ""),
            nodeid=result.get("nodeid", ""),
            error_message=result.get("message", ""),
        )
        if analysis:
            update_result_analysis(result["id"], analysis)
