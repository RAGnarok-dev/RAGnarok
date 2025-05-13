#!/bin/bash

# 配置变量
CONTAINER_NAME="competent_chaplygin"
DB_USER="postgres"
DB_NAME="ragnarok"
DB_PASSWORD="123456"
SQL_FILE="init_data.sql"
CONTAINER_SQL_PATH="/tmp/$SQL_FILE"

# 复制 SQL 文件到容器
echo "Copying SQL file to container..."
docker cp "$(dirname "$0")/$SQL_FILE" $CONTAINER_NAME:$CONTAINER_SQL_PATH

# 执行 SQL 文件
echo "Executing SQL file..."
docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f $CONTAINER_SQL_PATH

# 校验数据
echo "Checking knowledge_bases:"
docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT id, title FROM knowledge_bases;"

echo "Checking files:"
docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT id, name, type, location FROM files;"

echo "Database initialization completed!"
