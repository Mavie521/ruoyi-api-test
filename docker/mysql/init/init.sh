#!/bin/bash
# 每次 MySQL 首次启动时自动导入 ruoyi.sql
# 如果已初始化则跳过（幂等）
mysql -uroot -proot ry-vue -e "SELECT COUNT(*) FROM sys_config;" 2>/dev/null
if [ $? -ne 0 ]; then
  echo ">>> 导入 ruoyi.sql 初始化数据库..."
  mysql -uroot -proot ry-vue < /docker-entrypoint-initdb.d/ruoyi.sql
  echo ">>> 数据库初始化完成"
else
  echo ">>> 数据库已初始化，跳过"
fi
