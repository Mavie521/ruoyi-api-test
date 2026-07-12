#!/bin/bash
# =============================================
# 在 Docker 环境中运行测试（支持参数）
#
# 用法:
#   bash scripts/run_tests.sh                    # 默认 p0
#   bash scripts/run_tests.sh -m smoke -n 4      # 冒烟 + 4并发
#   bash scripts/run_tests.sh -k login           # 按关键字
#   bash scripts/run_tests.sh --reruns 2         # 失败重试
# =============================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 收集额外参数
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
    EXTRA_ARGS+=("$1")
    shift
done

echo "🧪 运行测试 (Docker)..."
echo "   参数: ${EXTRA_ARGS[*]:-默认 p0}"

docker-compose run --rm test-runner \
    sh -c "pytest tests/ ${EXTRA_ARGS[*]} \
        --alluredir=./reports/allure-results \
        --clean-alluredir -v"

echo ""
echo "📊 报告已生成: reports/allure-results"
