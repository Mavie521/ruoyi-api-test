#!/bin/bash
# DingTalk notification — 从环境变量读取敏感信息，jq 构建 JSON，校验推送结果

# ── 配置：从环境变量读取（无环境变量时使用默认值，但 Token 必须有） ──
TOKEN="${DINGTALK_TOKEN:-26b5bada9e95f4f06cbb126b8a5d1d59f350a140f60a199d3f71d0ed88bdc804}"
HOST="${REPORT_HOST:-192.168.149.100}"
JENKINS_PORT="${JENKINS_PORT:-8081}"
NGINX_PORT="${NGINX_PORT:-8088}"

WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=${TOKEN}"

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

# ── 用 jq 构建 JSON（避免字符串拼接导致特殊字符破坏结构） ──
TEXT=$(cat <<ENDTEXT
### RuoYi API Test Report
---
**Result:** ${RESULT}

**Level:** ${MARKER}
**Build:** #${BUILD}
**Pass Rate:** ${PASSED} / ${TOTAL}
**Duration:** ${DURATION}s

---
[View Allure Report](http://${HOST}:${JENKINS_PORT}/job/ruoyi-api-test/${BUILD}/allure/) | [Nginx Report](http://${HOST}:${NGINX_PORT})
---
_Test:_ ${INFO}_
ENDTEXT
)

# ── 构建 JSON（优先用 jq，不存在则 fallback 到拼接） ──
if command -v jq &>/dev/null; then
  MSG=$(jq -n --arg title "${TITLE} - ${RESULT}" --arg text "$TEXT" \
    '{msgtype:"markdown", markdown:{title:$title, text:$text}}')
else
  # fallback：手动转义双引号和反斜杠
  TEXT_ESC=$(echo "$TEXT" | sed 's/"/\\"/g; s/\\/\\\\/g')
  MSG='{"msgtype":"markdown","markdown":{"title":"'"${TITLE} - ${RESULT}"'","text":"'"$TEXT_ESC"'"}}'
fi

# ── 日志脱敏：替换 URL 中的 token 为 *** ──
mask_token() {
  echo "$1" | sed "s/access_token=[a-zA-Z0-9_\-]*/access_token=***/g"
}

# ── 发送并校验结果 ──
RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$MSG" "$WEBHOOK_URL")
if command -v jq &>/dev/null; then
  ERRCODE=$(echo "$RESPONSE" | jq -r '.errcode // empty')
else
  ERRCODE=$(echo "$RESPONSE" | grep -o '"errcode":[0-9]*' | cut -d: -f2)
fi

if [ "$ERRCODE" = "0" ]; then
  echo "[OK] 钉钉通知发送成功"
else
  echo "[WARN] 钉钉通知发送失败（$(mask_token "$RESPONSE")）"
fi
