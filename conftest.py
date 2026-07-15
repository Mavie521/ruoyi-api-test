"""
全局 conftest.py —— 环境初始化 + Allure 配置 + 失败自动附件 + 数据清理
"""
import os
import sys
import json
import pytest
import allure
from pathlib import Path
from datetime import datetime
from config.config import ALLURE_RESULTS_DIR, BASE_URL, ACTIVE_ENV


@pytest.fixture(scope="session", autouse=True)
def allure_environment():
    """
    自动生成 Allure 环境信息文件
    在 Allure 报告 > 环境 面板中显示
    """
    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    env_file = ALLURE_RESULTS_DIR / "environment.properties"
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(f"BaseURL={BASE_URL}\n")
        f.write(f"Environment={ACTIVE_ENV.value}\n")
        f.write(f"Python={sys.version.split()[0]}\n")
        f.write("测试框架=若依接口测试框架 v1.1\n")
        f.write(f"测试时间={datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"操作系统={sys.platform}\n")

    # categories.json
    cat_file = ALLURE_RESULTS_DIR / "categories.json"
    if not cat_file.exists():
        categories = [
            {"name": "API 请求异常", "matchedStatuses": ["failed", "broken"],
             "messageRegex": "(?i).*(?:ConnectionError|timeout|HTTPError|status.*code|500|404|请求异常).*"},
            {"name": "数据库断言失败", "matchedStatuses": ["failed", "broken"],
             "messageRegex": "(?i).*(?:数据库断言|assert_value|SQL|pymysql|DB).*"},
            {"name": "业务校验失败", "matchedStatuses": ["failed"],
             "messageRegex": "(?i).*(?:assert|断言|预期|期望|code.*200|success).*"},
            {"name": "其他异常", "matchedStatuses": ["broken"]},
            {"name": "已跳过", "matchedStatuses": ["skipped"]},
        ]
        with open(cat_file, "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

    # 记录环境信息到 Allure
    allure.attach(
        f"环境: {ACTIVE_ENV.value}\nURL: {BASE_URL}\n时间: {datetime.now()}",
        name="环境信息",
        attachment_type=allure.attachment_type.TEXT,
    )

    yield


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试失败时自动 attach 相关信息到 Allure 报告
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if call.excinfo:
            exc_type = call.excinfo.type.__name__
            exc_msg = str(call.excinfo.value)
            allure.attach(
                f"异常类型: {exc_type}\n\n异常信息:\n{exc_msg}",
                name="失败原因",
                attachment_type=allure.attachment_type.TEXT,
            )

        node_id = report.nodeid
        allure.attach(
            f"测试节点: {node_id}\n"
            f"运行时间: {datetime.now().strftime('%H:%M:%S')}",
            name="测试定位信息",
            attachment_type=allure.attachment_type.TEXT,
        )

        from utils.logger import logger
        logger.error(f"[FAIL] {node_id}")
        if call.excinfo:
            logger.error(f"  Reason: {call.excinfo.value}")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """测试开始前输出环境信息"""
    from utils.logger import logger
    logger.info("=" * 60)
    logger.info(f"RuoYi API Test Framework Starting [env={ACTIVE_ENV.value}]")
    logger.info(f"  Target: {BASE_URL}")
    logger.info(f"  Python: {sys.version.split()[0]}")
    logger.info(f"  WorkDir: {Path(__file__).resolve().parent}")
    logger.info("=" * 60)


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """测试结束后输出汇总"""
    from utils.logger import logger

    total = getattr(session, 'testscollected', 0)
    failed_count = getattr(session, 'testsfailed', 0)
    passed_count = total - failed_count

    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info(f"  Total: {total}")
    logger.info(f"  Passed: {passed_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"  ExitCode: {exitstatus}")
    logger.info("=" * 60)
