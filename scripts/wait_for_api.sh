#!/bin/bash
echo "等待后端就绪..."
for i in $(seq 1 15); do
  if curl -sf http://ruoyi-api:8080/login > /dev/null 2>&1; then
    echo "就绪"
    exit 0
  fi
  echo "等待中 ($i/15)"
  sleep 4
done
echo "超时"
exit 1
