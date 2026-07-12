#!/bin/bash
# =============================================
# RuoYi API Test — 一键部署脚本
# 在 Linux 上通过 Docker 部署完整测试环境
# =============================================
set -e

echo "=============================================="
echo " RuoYi API Test Framework — Docker 部署"
echo "=============================================="

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# ---- 1. 检查 Docker ----
echo ""
echo "📦 [1/5] 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ 未安装 Docker，请先安装:"
    echo "   curl -fsSL https://get.docker.com | bash"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose 未安装，尝试用 docker compose..."
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi
echo "   Docker: $(docker --version)"
echo "   $($COMPOSE_CMD version 2>/dev/null || echo 'compose plugin OK')"
echo "   ✅"

# ---- 2. 下载 SQL 初始化脚本 ----
echo ""
echo "🗄️ [2/5] 获取数据库初始化脚本..."
if [ ! -f "docker/mysql/init/ruoyi.sql" ]; then
    bash scripts/download_sql.sh
else
    size=$(wc -c < "docker/mysql/init/ruoyi.sql" 2>/dev/null || echo 0)
    echo "   ruoyi.sql 已存在（${size} bytes），跳过下载"
fi
echo "   ✅"

# ---- 3. 创建环境变量 ----
echo ""
echo "🔧 [3/5] 配置环境变量..."
ENV_FILE="docker/.env.docker"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'ENVEOF'
# Docker 环境变量（覆盖 .env）
BASE_URL=http://ruoyi-api:8080
DB_HOST=mysql
DB_PORT=3306
DB_NAME=ry-vue
DB_USER=root
DB_PASSWORD=root
LOG_LEVEL=INFO
ENVEOF
    echo "   已创建 $ENV_FILE"
fi
echo "   ✅"

# ---- 4. 启动所有服务 ----
echo ""
echo "🐳 [4/5] 启动 Docker 服务..."
$COMPOSE_CMD down 2>/dev/null || true
$COMPOSE_CMD up -d

echo ""
echo "   等待 RuoYi 后端启动（约 30-60 秒）..."
echo "   可通过 docker-compose logs -f ruoyi-api 查看进度"

# 等待后端就绪
TIMEOUT=90
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if curl -sf http://localhost:8080/actuator/health 2>/dev/null | grep -q "UP"; then
        echo "   ✅ RuoYi 后端已就绪"
        break
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo "   ...等待中 ($ELAPSED 秒)"
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo ""
    echo "⚠️  RuoYi 后端启动超时，请检查日志:"
    echo "   docker-compose logs ruoyi-api"
fi

# ---- 5. 运行测试 ----
echo ""
echo "🧪 [5/5] 运行测试..."
$COMPOSE_CMD up test-runner

echo ""
echo "=============================================="
echo " ✅ 部署完成！"
echo "=============================================="
echo ""
echo " 📊 Allure 报告: ./reports/allure-report/index.html"
echo " 🔗 若依前端:   http://localhost"
echo " 🔗 若依后端:   http://localhost:8080"
echo ""
echo " 常用命令:"
echo "   docker-compose logs -f ruoyi-api    # 查看后端日志"
echo "   docker-compose run test-runner      # 重新运行测试"
echo "   docker-compose down -v              # 停止并清除数据"
echo ""
