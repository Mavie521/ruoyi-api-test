#!/bin/bash
# DingTalk notification - enterprise format
WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=26b5bada9e95f4f06cbb126b8a5d1d59f350a140f60a199d3f71d0ed88bdc804"
STATUS=$1; PASSED=$2; TOTAL=$3; DURATION=$4; MARKER=$5

if [ "$STATUS" = "success" ]; then
  RESULT="Pass"
else
  RESULT="Failed"
fi

MSG='{"msgtype":"markdown","markdown":{"title":"Test: RuoYi API - '"$RESULT"'","text":"### Test: RuoYi API Test Report\n---\n- **Result:** '"$RESULT"'\n- **Level:** '"$MARKER"'\n- **Pass Rate:** '"$PASSED"' / '"$TOTAL"'\n- **Duration:** '"$DURATION"'s\n- **Report:** http://192.168.159.128:8088\n- **Jenkins:** http://192.168.159.128:8081/job/ruoyi-api-test/\n---\n_RuoYi API Test Framework_"}}'
curl -s -X POST -H "Content-Type: application/json" -d "$MSG" $WEBHOOK_URL
