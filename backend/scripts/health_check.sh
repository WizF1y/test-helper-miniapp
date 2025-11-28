#!/bin/bash

# 健康检查脚本
# 用于验证系统各组件是否正常运行

set -e

echo "=========================================="
echo "系统健康检查"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local service_name=$1
    local check_command=$2
    
    echo -n "检查 $service_name... "
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 异常${NC}"
        return 1
    fi
}

# 检查 Docker 服务
echo "1. Docker 服务检查"
echo "-------------------"
check_service "Docker" "docker ps"
check_service "Docker Compose" "docker-compose version"
echo ""

# 检查容器状态
echo "2. 容器状态检查"
echo "-------------------"
if docker-compose ps | grep -q "Up"; then
    check_service "Backend 容器" "docker-compose ps backend | grep -q 'Up'"
    check_service "MySQL 容器" "docker-compose ps mysql | grep -q 'Up'"
else
    echo -e "${RED}✗ 容器未运行${NC}"
    echo "请先启动服务: docker-compose up -d"
    exit 1
fi
echo ""

# 检查网络连接
echo "3. 网络连接检查"
echo "-------------------"
check_service "Backend 网络" "docker-compose exec -T backend ping -c 1 mysql"
echo ""

# 检查数据库
echo "4. 数据库检查"
echo "-------------------"
check_service "MySQL 连接" "docker-compose exec -T mysql mysqladmin ping -h localhost -u root -p\${MYSQL_PASSWORD}"

# 检查表是否存在
echo -n "检查数据库表... "
TABLE_COUNT=$(docker-compose exec -T mysql mysql -u root -p${MYSQL_PASSWORD} -D sz_exam -e "SHOW TABLES;" 2>/dev/null | wc -l)
if [ "$TABLE_COUNT" -gt 8 ]; then
    echo -e "${GREEN}✓ 正常 ($((TABLE_COUNT-1)) 个表)${NC}"
else
    echo -e "${RED}✗ 异常 (表数量不足)${NC}"
fi
echo ""

# 检查 API 接口
echo "5. API 接口检查"
echo "-------------------"
check_service "API 健康检查" "curl -s http://localhost:5000/api/health | grep -q 'ok'"
echo ""

# 检查日志
echo "6. 日志检查"
echo "-------------------"
echo -n "检查错误日志... "
if [ -f "logs/app.log" ]; then
    ERROR_COUNT=$(grep -c "ERROR" logs/app.log 2>/dev/null || echo 0)
    if [ "$ERROR_COUNT" -lt 10 ]; then
        echo -e "${GREEN}✓ 正常 ($ERROR_COUNT 个错误)${NC}"
    else
        echo -e "${YELLOW}⚠ 警告 ($ERROR_COUNT 个错误)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 日志文件不存在${NC}"
fi
echo ""

# 检查磁盘空间
echo "7. 资源使用检查"
echo "-------------------"
echo -n "检查磁盘空间... "
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ 正常 (${DISK_USAGE}%)${NC}"
else
    echo -e "${YELLOW}⚠ 警告 (${DISK_USAGE}%)${NC}"
fi

echo -n "检查内存使用... "
if command -v free > /dev/null; then
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$MEM_USAGE" -lt 90 ]; then
        echo -e "${GREEN}✓ 正常 (${MEM_USAGE}%)${NC}"
    else
        echo -e "${YELLOW}⚠ 警告 (${MEM_USAGE}%)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 无法检查${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo "健康检查完成"
echo "=========================================="
echo ""
echo "如果发现异常，请查看详细日志："
echo "  docker-compose logs -f"
echo ""
echo "或查看应用日志："
echo "  tail -f logs/app.log"
echo ""
