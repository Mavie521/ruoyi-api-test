#!/bin/bash
set +e; cd /app/ruoyi-api-test
MARKER=${1:-p0}; MODE=${2:-fast}; START_TIME=$(date +%s)
if [ "$MODE" = "clean" ]; then docker compose down -v 2>/dev/null; fi
docker compose up -d 2>/dev/null
docker compose run --rm test-runner bash /app/scripts/wait_for_api.sh
mkdir -p reports/allure-results
if [ "$MARKER" = "all" ]; then
  docker compose run --rm test-runner pytest tests/ --alluredir=reports/allure-results --clean-alluredir -v --reruns 1
else
  docker compose run --rm test-runner pytest tests/ -m "$MARKER" --alluredir=reports/allure-results --clean-alluredir -v --reruns 1
fi
EXIT_CODE=$?
DURATION=$(($(date +%s)-START_TIME))
PASSED=$(grep -oP '\d+(?= passed)' reports/allure-results/*.txt 2>/dev/null | tail -1 || echo "0")
TOTAL=$(grep -oP '\d+(?= deselected)' reports/allure-results/*.txt 2>/dev/null | tail -1 || echo "0"); [ "$TOTAL" = "0" ] && TOTAL="$PASSED"
if [ $EXIT_CODE -ne 0 ]; then bash scripts/notify.sh "failure" "$PASSED" "$TOTAL" "$DURATION" "$MARKER"; else bash scripts/notify.sh "success" "$PASSED" "$TOTAL" "$DURATION" "$MARKER"; fi
exit $EXIT_CODE
