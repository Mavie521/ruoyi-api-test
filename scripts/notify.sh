#!/bin/bash
# DingTalk notification - enterprise format
WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=26b5bada9e95f4f06cbb126b8a5d1d59f350a140f60a199d3f71d0ed88bdc804"
STATUS=$1; PASSED=$2; TOTAL=$3; DURATION=$4; MARKER=$5; BUILD=${6:-latest}; TYPE=${7:-build}

if [ "$STATUS" = "success" ]; then
  RESULT="Pass"
else
  RESULT="Failed"
fi

# 构建类型标识
TIME_STR=$(date "+%Y-%m-%d %H:%M")
if [ "$TYPE" = "patrol" ]; then
  TITLE="Daily Patrol"
  INFO="Daily Test Report - ${TIME_STR}"
else
  TITLE="Test: RuoYi API"
  INFO="Build #${BUILD} - ${MARKER} - ${TIME_STR}"
fi

# 日常构建：只发失败
if [ "$TYPE" = "build" ] && [ "$STATUS" = "success" ]; then
  exit 0
fi

MSG='{"msgtype":"markdown","markdown":{"title":"'"$TITLE"' - '"$RESULT"'","text":"### RuoYi API Test Report\n---\n**Result:** '"$RESULT"'\n\n**Level:** '"$MARKER"'\\n**Build:** #'"$BUILD"'\n**Pass Rate:** '"$PASSED"' / '"$TOTAL"'\n**Duration:** '"$DURATION"'s\n\n---\n[View Allure Report](http://192.168.159.128:8081/job/ruoyi-api-test/'"$BUILD"'/allure/) | [Nginx Report](http://192.168.159.128:8088)\n---\n_Test:_ '"$INFO"'_"}}'
curl -s -X POST -H "Content-Type: application/json" -d "$MSG" $WEBHOOK_URL
