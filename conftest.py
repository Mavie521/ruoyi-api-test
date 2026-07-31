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

#自动生成这个文件,代码自动写入：被测网址、测试环境、Python 版本、运行时间、操作系统
@pytest.fixture(scope="session", autouse=True)
def allure_environment():
    """
    自动生成 Allure 环境信息文件
    在 Allure 报告 > 环境 面板中显示
    """
    #保证存放 allure 数据的文件夹一定存在，不存在就新建，文件夹已经存在，不会报错
    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    #pathlib 语法，拼接路径 最终路径：allure-results/environment.properties
    #.properties 是简单配置文本文件，纯文本键值对
    #Allure 工具固定规则：只要 allure-results 里有这个文件，网页报告【环境】面板自动读取展示内容
    env_file = ALLURE_RESULTS_DIR / "environment.properties"
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(f"BaseURL={BASE_URL}\n")
        f.write(f"Environment={ACTIVE_ENV.value}\n")
        f.write(f"Python={sys.version.split()[0]}\n")
        f.write("测试框架=若依接口测试框架 v1.1\n")
        f.write(f"测试时间={datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"操作系统={sys.platform}\n")

    # categories.json Allure 官方识别的用例失败分类规则文件
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

    yield   #yield 之前 = 测试开始前执行 yield 之后 = 全部测试跑完执行（这里后面没有代码）


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
# item：当前正在执行这条测试用例对象包含：用例名称、文件路径、标签 @pytest.mark、参数化数据等等
# call：本次执行的信息对象保存着本次运行产生的异常、执行耗时等内容
    """
    测试失败时自动 attach 相关信息到 Allure 报告
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        try:
            from utils.logger import logger
            if call.excinfo:  #如果用例运行抛出异常（断言失败、接口报错）→ excinfo 有内容，执行下面保存报错信息的代码
                allure.attach(
                    f"异常类型: {call.excinfo.type.__name__}\n\n异常信息:\n{call.excinfo.value}",  #打印效果：异常类型: AssertionError
                    name="失败原因",
                    attachment_type=allure.attachment_type.TEXT,
                )
                logger.error(f"[FAIL] {report.nodeid} — {call.excinfo.value}")
            else:
                logger.error(f"[FAIL] {report.nodeid}")
        except Exception as e:  #含义：就算自动保存报错这段代码本身出问题，也不会导致测试全部卡死，仅仅打印一行警告（防御代码）
            print(f"[WARN] 日志/Allure 挂附件失败（不影响测试结果）: {e}")


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


# fixture：准备杯子、原料、吸管（测试账号、测试数据）
# pytest 钩子：监控订单、打印日报、整理台账、分类差评（报告增强、日志、监控执行结果）

# 整个文件一共 4 组功能：
# session 自动执行 fixture：生成 Allure 报告需要的配置文件，让报告信息完整、失败自动分类
# 钩子监听每条用例：用例失败，自动把报错存入 Allure 报告
# 启动钩子：程序启动打印环境信息，防止跑错环境
# 结束钩子：全部跑完，控制台输出汇总统计
# 区分两个极易混淆概念（你一定要分清）
# fixture（上一份 conftest：登录账号、创建角色、数据库）
# 作用：准备测试数据、账号、资源，给测试用例调用
# pytest 钩子（这份文件）
# 不准备测试数据！负责改造 pytest 运行规则、优化报告、日志

# ✅ 层级关系：
# pytest 主程序
# ├── 触发各类 hook 钩子（监听事件）
# └── 执行测试生命周期
# 　　├── setup 阶段（运行 fixture 前置）
# 　　├── call 阶段（运行测试函数代码）
# 　　└── teardown 阶段（运行 fixture 后置清理）
# Hook 是旁观者、监工；Fixture 是执行流程里的工人。
# 运行时序完整链条（一条用例）：
# pytest 触发钩子事件
# 执行 fixture setup（前置准备）
# 执行测试函数代码
# 执行 fixture teardown（后置清理）
# 钩子拿到最终执行结果
# 钩子只是全程监控，不会接管、不包含 fixture 代码。
# 极简总结区分（面试直接背）
# fixture：聚焦资源准备与释放，服务测试用例，无法感知用例成败；
# hook 钩子：pytest 底层事件监听机制，能捕捉整个运行生命周期状态（成功 / 失败），适合全局日志、报告增强；
# item、call、excinfo、nodeid 全部为 pytest 官方内置对象，钩子触发时自动传入；
# 二者是协作关系，不是包含关系；项目中通常搭配一起使用。
