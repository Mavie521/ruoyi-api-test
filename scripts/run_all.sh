#!/bin/bash
set +e
MARKER=${1:-p0}; MODE=${2:-fast}; TYPE=${3:-build}; START_TIME=$(date +%s)

PROJECT_DIR="/home/yy/ruoyi-api-test"
[ -d "$PROJECT_DIR" ] || PROJECT_DIR="/app/ruoyi-api-test"
cd "$PROJECT_DIR"

REPORT_DIR="$PROJECT_DIR/reports"
ALLURE_DIR="$REPORT_DIR/allure-results"

# 显式启动带 profile 的服务（test-runner、ruoyi-api、mysql 等）
if [ "$MODE" = "clean" ]; then
  docker compose --profile test down 2>/dev/null
  docker compose --profile test up -d
else
  docker compose --profile test up -d 2>/dev/null
fi
docker compose --profile test run --rm test-runner bash /app/scripts/wait_for_api.sh

if [ "$MARKER" = "all" ]; then
  docker compose --profile test run --rm test-runner sh -c "rm -rf /app/reports/temp-allure && pytest tests/ --alluredir=/app/reports/temp-allure -v --reruns 1; rm -rf /app/reports/allure-results && mv /app/reports/temp-allure /app/reports/allure-results"
else
  docker compose --profile test run --rm test-runner sh -c "rm -rf /app/reports/temp-allure && pytest tests/ -m $MARKER --alluredir=/app/reports/temp-allure -v --reruns 1; rm -rf /app/reports/allure-results && mv /app/reports/temp-allure /app/reports/allure-results"
fi

EXIT_CODE=$?
DURATION=$(($(date +%s)-START_TIME))
PASSED=$(grep -oP '\d+(?= passed)' "$ALLURE_DIR"/*.txt 2>/dev/null | tail -1 || echo "0")
TOTAL=$(grep -oP '(?<=Total: )\d+' "$ALLURE_DIR"/*.txt 2>/dev/null | tail -1 || echo "0"); [ "$TOTAL" = "0" ] && TOTAL="$PASSED"

cd "$PROJECT_DIR" && docker compose run --rm allure-reporter 2>/dev/null || true

if [ $EXIT_CODE -ne 0 ]; then bash scripts/notify.sh "failure" "$PASSED" "$TOTAL" "$DURATION" "$MARKER" "${BUILD_NUMBER:-}" "$TYPE"; else bash scripts/notify.sh "success" "$PASSED" "$TOTAL" "$DURATION" "$MARKER" "${BUILD_NUMBER:-}" "$TYPE"; fi

# 重建 allure-report（修复 iptables 规则，不影响测试）
docker compose up -d --force-recreate allure-report 2>/dev/null || true

exit $EXIT_CODE
