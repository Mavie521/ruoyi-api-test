#!/bin/bash
echo "等待后端就绪..."
for i in $(seq 1 25); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://ruoyi-api:8080/login 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" != "000" ] && [ "$HTTP_CODE" != "502" ] && [ "$HTTP_CODE" != "503" ]; then
    echo "就绪 (HTTP $HTTP_CODE)"
    exit 0
  fi
  echo "等待中 ($i/25) — HTTP $HTTP_CODE"
  sleep 4
done
echo "超时 — 后端 100 秒未能就绪"
exit 1
