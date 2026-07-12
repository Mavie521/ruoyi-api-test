#!/bin/bash
# =============================================
# 企业级一键测试 + 报告生成 + 托管
# 用法: bash scripts/test_and_report.sh
# =============================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=============================================="
echo " RuoYi API Test Framework — 企业级流水线"
echo "=============================================="

# 1. 运行测试
echo ""
echo " [1/4] 执行测试..."
docker compose --profile test run --rm test-runner

# 2. 生成 Allure 报告
echo ""
echo " [2/4] 生成 Allure 报告..."
docker compose --profile report run --rm allure-reporter

# 3. 启动 / 刷新 Nginx 报告服务
echo ""
echo " [3/4] 刷新报告服务..."
docker compose up -d allure-report

# 4. 验证
echo ""
echo " [4/4] 完成！"
echo "=============================================="
echo " 报告地址: http://192.168.159.128:8088"
echo " 若依后端: http://192.168.159.128:8080"
echo "=============================================="
