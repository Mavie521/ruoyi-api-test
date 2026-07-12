#!/bin/bash
# =============================================
# 获取若依数据库初始化 SQL（v3.9.2 版本）
# 从官方 GitHub 仓库下载
# =============================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INIT_DIR="$PROJECT_DIR/docker/mysql/init"
SQL_FILE="$INIT_DIR/ruoyi.sql"

mkdir -p "$INIT_DIR"

if [ -f "$SQL_FILE" ] && [ -s "$SQL_FILE" ]; then
    echo "✅ ruoyi.sql 已存在（$(wc -c < "$SQL_FILE") bytes），跳过下载"
    exit 0
fi

echo "📥 下载若依数据库初始化脚本（v3.9.2）..."

# https://github.com/yangzongzhuan/RuoYi-Vue/blob/v3.9.2/sql/ry-vue_8.0.sql
# 使用 raw.githubusercontent.com 下载 raw 文件

if command -v wget &> /dev/null; then
    wget -q --show-progress \
        -O "$SQL_FILE" \
        "https://raw.githubusercontent.com/yangzongzhuan/RuoYi-Vue/v3.9.2/sql/ry-vue_8.0.sql"
elif command -v curl &> /dev/null; then
    curl -sS -L -o "$SQL_FILE" \
        "https://raw.githubusercontent.com/yangzongzhuan/RuoYi-Vue/v3.9.2/sql/ry-vue_8.0.sql"
else
    echo "❌ 请先安装 wget 或 curl"
    exit 1
fi

if [ -f "$SQL_FILE" ] && [ -s "$SQL_FILE" ]; then
    echo "✅ 下载完成: $(wc -c < "$SQL_FILE") bytes"
else
    echo "❌ 下载失败，检查网络或手动下载:"
    echo "   https://raw.githubusercontent.com/yangzongzhuan/RuoYi-Vue/v3.9.2/sql/ry-vue_8.0.sql"
    exit 1
fi
