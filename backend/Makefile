.PHONY: help build up down restart logs shell db-shell backup clean health test

# 默认目标
help:
	@echo "可用命令："
	@echo "  make build      - 构建 Docker 镜像"
	@echo "  make up         - 启动所有服务"
	@echo "  make down       - 停止所有服务"
	@echo "  make restart    - 重启所有服务"
	@echo "  make logs       - 查看日志"
	@echo "  make shell      - 进入后端容器"
	@echo "  make db-shell   - 进入 MySQL 容器"
	@echo "  make backup     - 备份数据库"
	@echo "  make health     - 健康检查"
	@echo "  make test       - 运行测试"
	@echo "  make clean      - 清理资源"

# 构建镜像
build:
	docker-compose build

# 启动服务
up:
	docker-compose up -d
	@echo "服务已启动，访问 http://localhost:5000"
	@echo "运行 'make logs' 查看日志"

# 停止服务
down:
	docker-compose down

# 重启服务
restart:
	docker-compose restart

# 查看日志
logs:
	docker-compose logs -f

# 进入后端容器
shell:
	docker-compose exec backend sh

# 进入 MySQL 容器
db-shell:
	docker-compose exec mysql mysql -u root -p

# 备份数据库
backup:
	@mkdir -p backups
	@echo "备份数据库..."
	docker exec politics_mysql mysqldump -u root -p sz_exam > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "备份完成: backups/backup_$$(date +%Y%m%d_%H%M%S).sql"

# 健康检查
health:
	@bash scripts/health_check.sh

# 运行测试
test:
	docker-compose exec backend python scripts/verify_implementation.py

# 清理资源
clean:
	docker-compose down -v
	docker system prune -f
	@echo "清理完成"

# 查看服务状态
status:
	docker-compose ps

# 查看资源使用
stats:
	docker stats --no-stream

# 初始化环境
init:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "已创建 .env 文件，请编辑配置"; \
	else \
		echo ".env 文件已存在"; \
	fi

# 完整部署（初始化 + 构建 + 启动）
deploy: init build up
	@echo "部署完成！"
	@echo "请等待约 30 秒让服务完全启动"
	@sleep 5
	@make health
