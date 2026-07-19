#!/bin/bash
# =============================================
# 等待若依 API 就绪（POST /login 验证 token）
# 只有真正拿到 token 才认为就绪
# =============================================
set -e

MAX_RETRIES=${1:-40}
SLEEP=${2:-5}
ADMIN_USER="${ADMIN_USERNAME:-admin}"
ADMIN_PASS="${ADMIN_PASSWORD:-admin123}"
URL="http://ruoyi-api:8080/login"

echo "⏳ 等待后端就绪... (POST $URL)"

for i in $(seq 1 $MAX_RETRIES); do
  # POST /login 并提取 token（密码从环境变量读取，不硬编码）
  RESP=$(curl -s --connect-timeout 5 -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}" 2>/dev/null || echo "")

  TOKEN=$(echo "$RESP" | grep -o '"token"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | grep -o '"[^"]*"$' | tr -d '"')

  if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo "✅ 后端就绪 (第${i}次) — token 已获取"
    exit 0
  fi

  # 输出响应摘要（取前200字符）
  SUMMARY=$(echo "$RESP" | head -c 200 | tr '\n' ' ' | sed 's/  */ /g')
  [ -z "$SUMMARY" ] && SUMMARY="(无响应)"
  echo "  等待中 ($i/$MAX_RETRIES) — $SUMMARY"
  sleep $SLEEP
done

echo "❌ 超时 — 后端 $((MAX_RETRIES * SLEEP)) 秒未能登录"
exit 1
