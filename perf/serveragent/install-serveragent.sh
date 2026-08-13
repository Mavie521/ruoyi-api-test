#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# ServerAgent (PerfMon Agent) 部署脚本 — 在【被测服务器】上执行
# 用途：向 JMeter 的 jp@gc PerfMon 监听器上报本机 CPU/内存/磁盘/网络
# 运行环境：若依后端所在的 VM (192.168.149.100)，Rocky Linux 9
# 监听端口：4444（默认，需对本机防火墙放行）
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

AGENT_VERSION="2.2.3"
AGENT_ZIP="ServerAgent-${AGENT_VERSION}.zip"
DOWNLOAD_URL="https://github.com/undera/perfmon-agent/releases/download/${AGENT_VERSION}/${AGENT_ZIP}"
INSTALL_DIR="$HOME/serveragent"
TCP_PORT="4444"

echo "==> [1/4] 检查 Java（ServerAgent 需要 JDK/JRE）"
if command -v java >/dev/null 2>&1; then
    java -version 2>&1 | head -1
else
    echo "    未检测到 Java，尝试安装 OpenJDK 17 ..."
    sudo yum install -y java-17-openjdk
fi

echo "==> [2/4] 下载 ServerAgent ${AGENT_VERSION}"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
if [ ! -f "$AGENT_ZIP" ]; then
    curl -L -o "$AGENT_ZIP" "$DOWNLOAD_URL"
else
    echo "    ${AGENT_ZIP} 已存在，跳过下载"
fi

echo "==> [3/4] 解压"
if [ ! -f "startAgent.sh" ]; then
    unzip -o "$AGENT_ZIP"
fi

echo "==> [4/4] 启动 ServerAgent（后台，端口 ${TCP_PORT}）"
# 先停掉可能残留的旧进程
pkill -f "startAgent.sh" 2>/dev/null || true
pkill -f "perfmon-agent" 2>/dev/null || true
sleep 1

nohup ./startAgent.sh --udp-port 0 --tcp-port "${TCP_PORT}" > /tmp/serveragent.log 2>&1 &
sleep 2

if pgrep -f "startAgent.sh" >/dev/null 2>&1 || pgrep -f "perfmon-agent" >/dev/null 2>&1; then
    echo "✅ ServerAgent 已启动，监听 ${TCP_PORT} 端口"
    echo "   日志：/tmp/serveragent.log"
    echo "   验证：ss -lntp | grep ${TCP_PORT}"
else
    echo "❌ 启动失败，请查看日志：cat /tmp/serveragent.log"
    exit 1
fi

echo ""
echo "⚠️  防火墙放行（若压测机无法连接，执行）："
echo "   sudo firewall-cmd --add-port=${TCP_PORT}/tcp --permanent && sudo firewall-cmd --reload"
echo ""
echo "📌 JMeter 侧配置：PerfMon 监听器 → 服务器 IP 填 192.168.149.100，端口 4444"
