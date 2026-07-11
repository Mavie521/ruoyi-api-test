"""
断言工具 —— 封装常用响应断言
支持状态码、JSONPath、包含、数据库等断言方式
"""
import json
import allure
import jsonpath
import requests
from utils.logger import logger


class HttpAssert:
    """HTTP 响应断言器"""

    @staticmethod
    @allure.step("断言: 状态码")
    def status_code(res: requests.Response, expected: int = 200):
        """断言 HTTP 状态码"""
        actual = res.status_code
        assert actual == expected, \
            f"状态码断言失败: 预期 {expected}, 实际 {actual}"
        logger.info(f"✅ 状态码断言通过: {actual}")

    @staticmethod
    @allure.step("断言: 响应成功标志")
    def success(res: requests.Response):
        """断言若依响应的 success 字段为 True"""
        body = res.json()
        assert body.get("success", False) is True, \
            f"success标志断言失败: {body.get('msg', '无msg')}"
        logger.info(f"✅ success=True, msg={body.get('msg', '')}")

    @staticmethod
    @allure.step("断言: 响应 code")
    def code(res: requests.Response, expected: int = 200):
        """断言响应中的 code 字段"""
        actual = res.json().get("code")
        assert actual == expected, \
            f"code断言失败: 预期 {expected}, 实际 {actual}"
        logger.info(f"✅ code 断言通过: {actual}")

    @staticmethod
    @allure.step("断言: JSONPath 精确匹配")
    def jsonpath_match(res: requests.Response, jsonpath_expr: str, expected):
        """
        JSONPath 精确断言
        例如: jsonpath_match(res, "$.data.username", "admin")
        """
        actual_list = jsonpath.jsonpath(res.json(), jsonpath_expr)
        assert actual_list is not False, f"JSONPath 未匹配: {jsonpath_expr}"
        actual = actual_list[0]
        assert actual == expected, \
            f"JSONPath断言失败: {jsonpath_expr}\n  预期: {expected}\n  实际: {actual}"
        logger.info(f"✅ JSONPath断言通过: {jsonpath_expr} == {expected}")

    @staticmethod
    @allure.step("断言: 响应包含文本")
    def contains(res: requests.Response, text: str):
        """断言响应体包含指定文本"""
        assert text in res.text, \
            f"包含断言失败: 响应中未找到 '{text}'"
        logger.info(f"✅ 包含断言通过: 包含 '{text}'")

    @staticmethod
    @allure.step("断言: 列表不为空")
    def list_not_empty(res: requests.Response, jsonpath_expr: str = "$.rows"):
        """断言列表数据不为空"""
        actual_list = jsonpath.jsonpath(res.json(), jsonpath_expr)
        assert actual_list is not False, f"JSONPath 未匹配: {jsonpath_expr}"
        assert len(actual_list[0]) > 0, \
            f"列表为空: {jsonpath_expr}"
        logger.info(f"✅ 列表不为空: {jsonpath_expr} ({len(actual_list[0])}条)")

    @staticmethod
    @allure.step("断言: 字段包含预期值")
    def field_contains(res: requests.Response, jsonpath_expr: str, expected: str):
        """断言某个字段值包含预期文本"""
        actual_list = jsonpath.jsonpath(res.json(), jsonpath_expr)
        assert actual_list is not False, f"JSONPath 未匹配: {jsonpath_expr}"
        actual = str(actual_list[0])
        assert expected in actual, \
            f"包含断言失败: 字段值 '{actual}' 未包含 '{expected}'"
        logger.info(f"✅ 字段包含断言通过: '{actual}' 包含 '{expected}'")
