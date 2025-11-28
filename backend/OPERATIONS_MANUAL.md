# 运维操作手册

## 目录

1. [日常运维](#日常运维)
2. [备份与恢复](#备份与恢复)
3. [监控告警](#监控告警)
4. [应急处理](#应急处理)
5. [性能调优](#性能调优)
6. [安全审计](#安全审计)

---

## 日常运维

### 每日检查清单

#### 1. 服务健康检查

```bash
# 检查所有容器状态
docker-compose ps

# 预期输出：所有服务状态为 Up
# politics_backend    Up
# politics_mysql      Up (healthy)
```

#### 2. 查看系统资源使用

```bash
# 查看容器资源使用情况
docker stats --no-stream

# 检查磁盘空间
df -h

# 检查内存使用
free -h
```

#### 3. 检查应用日志

```bash
# 查看最近的错误日志
tail -n 100 logs/error.log | grep ERROR

# 查看应用日志
tail -n 100 logs/app.log

# 检查是否有异常
docker-compose logs --tail=100 backend | grep -i error
```

#### 4. 数据库健康检查

```bash
# 连接数据库
docker exec -it politics_mysql mysql -u root -p

# 执行健康检查 SQL
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Threads_running';
SELECT COUNT(*) FROM user;
SELECT COUNT(*) FROM topic;
```

### 每周维护任务

#### 1. 日志清理

```bash
# 清理 30 天前的日志
find logs/ -name "*.log.*" -mtime +30 -delete

# 压缩旧日志
gzip logs/app.log.1
gzip logs/access.log.1
```

#### 2. 数据库优化

```bash
# 进入 MySQL 容器
docker exec -it politics_mysql mysql -u root -p

# 优化表
USE sz_exam;
OPTIMIZE TABLE user;
OPTIMIZE TABLE topic;
OPTIMIZE TABLE user_mistake;
OPTIMIZE TABLE user_favorite;
OPTIMIZE TABLE exam_record;
OPTIMIZE TABLE exam_detail;
OPTIMIZE TABLE user_topic_progress;
OPTIMIZE TABLE payment;
```

#### 3. Docker 清理

```bash
# 清理未使用的镜像
docker image prune -a -f

# 清理未使用的容器
docker container prune -f

# 清理未使用的网络
docker network prune -f

# 查看磁盘使用
docker system df
```

### 每月维护任务

#### 1. 完整备份

```bash
# 创建备份目录
mkdir -p backups/$(date +%Y%m)

# 备份数据库
docker exec politics_mysql mysqldump -u root -p sz_exam > backups/$(date +%Y%m)/db_backup_$(date +%Y%m%d).sql

# 备份题目文件
tar -czf backups/$(date +%Y%m)/questions_$(date +%Y%m%d).tar.gz questions/

# 备份配置文件
cp .env backups/$(date +%Y%m)/env_backup_$(date +%Y%m%d)
```

#### 2. 安全更新

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新 Docker 镜像
docker-compose pull

# 重新构建应用
docker-compose up -d --build
```

#### 3. 性能报告

```bash
# 生成数据库性能报告
docker exec -it politics_mysql mysql -u root -p -e "
SELECT 
    table_name,
    table_rows,
    ROUND(data_length / 1024 / 1024, 2) AS data_mb,
    ROUND(index_length / 1024 / 1024, 2) AS index_mb
FROM information_schema.tables
WHERE table_schema = 'sz_exam'
ORDER BY data_length DESC;
"
```

---

## 备份与恢复

### 自动备份脚本

创建 `backup.sh` 脚本：

```bash
#!/bin/bash

# 配置
BACKUP_DIR="/path/to/backups"
MYSQL_PASSWORD="your_password"
RETENTION_DAYS=30

# 创建备份目录
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR/$DATE

# 备份数据库
echo "Backing up database..."
docker exec politics_mysql mysqldump -u root -p$MYSQL_PASSWORD sz_exam > $BACKUP_DIR/$DATE/database.sql

# 备份题目文件
echo "Backing up questions..."
tar -czf $BACKUP_DIR/$DATE/questions.tar.gz questions/

# 备份日志
echo "Backing up logs..."
tar -czf $BACKUP_DIR/$DATE/logs.tar.gz logs/

# 删除旧备份
echo "Cleaning old backups..."
find $BACKUP_DIR -type d -mtime +$RETENTION_DAYS -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$DATE"
```

设置定时任务：

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点执行备份
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

### 数据恢复流程

#### 1. 恢复数据库

```bash
# 停止应用
docker-compose stop backend

# 恢复数据库
docker exec -i politics_mysql mysql -u root -p sz_exam < backups/20240520/database.sql

# 验证数据
docker exec -it politics_mysql mysql -u root -p -e "USE sz_exam; SELECT COUNT(*) FROM user; SELECT COUNT(*) FROM topic;"

# 重启应用
docker-compose start backend
```

#### 2. 恢复题目文件

```bash
# 解压备份
tar -xzf backups/20240520/questions.tar.gz -C ./

# 验证文件
ls -la questions/
```

#### 3. 完整系统恢复

```bash
# 1. 停止所有服务
docker-compose down

# 2. 恢复数据库
docker-compose up -d mysql
sleep 10
docker exec -i politics_mysql mysql -u root -p sz_exam < backups/20240520/database.sql

# 3. 恢复文件
tar -xzf backups/20240520/questions.tar.gz -C ./

# 4. 启动所有服务
docker-compose up -d

# 5. 验证服务
docker-compose ps
docker-compose logs -f
```

---

## 监控告警

### 关键指标监控

#### 1. 应用性能指标

```bash
# API 响应时间监控
tail -f logs/access.log | awk '{print $NF}' | awk '{sum+=$1; count++} END {print "Avg response time:", sum/count, "ms"}'

# 错误率监控
grep -c "ERROR" logs/app.log
```

#### 2. 数据库性能指标

```sql
-- 慢查询监控
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 连接数监控
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- 查询缓存命中率
SHOW STATUS LIKE 'Qcache%';
```

#### 3. 系统资源监控

```bash
# CPU 使用率
top -bn1 | grep "Cpu(s)" | awk '{print "CPU Usage: " $2 + $4 "%"}'

# 内存使用率
free | grep Mem | awk '{print "Memory Usage: " $3/$2 * 100.0 "%"}'

# 磁盘使用率
df -h | grep -v tmpfs | awk '{if(NR>1)print $5, $6}'
```

### 告警规则配置

#### 1. 服务异常告警

```bash
# 检查服务状态脚本
#!/bin/bash

# 检查容器状态
if ! docker-compose ps | grep -q "Up"; then
    echo "ALERT: Service is down!" | mail -s "Service Alert" admin@example.com
fi

# 检查错误日志
ERROR_COUNT=$(grep -c "ERROR" logs/app.log)
if [ $ERROR_COUNT -gt 100 ]; then
    echo "ALERT: Too many errors: $ERROR_COUNT" | mail -s "Error Alert" admin@example.com
fi
```

#### 2. 资源使用告警

```bash
# 磁盘空间告警
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Disk usage is ${DISK_USAGE}%" | mail -s "Disk Alert" admin@example.com
fi

# 内存使用告警
MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    echo "ALERT: Memory usage is ${MEM_USAGE}%" | mail -s "Memory Alert" admin@example.com
fi
```

---

## 应急处理

### 场景 1：服务无响应

#### 症状
- API 请求超时
- 用户无法访问

#### 处理步骤

```bash
# 1. 检查服务状态
docker-compose ps

# 2. 查看日志
docker-compose logs --tail=100 backend

# 3. 检查资源使用
docker stats --no-stream

# 4. 重启服务
docker-compose restart backend

# 5. 如果问题持续，完全重启
docker-compose down
docker-compose up -d

# 6. 验证恢复
curl http://localhost:5000/api/health
```

### 场景 2：数据库连接失败

#### 症状
- 后端日志显示数据库连接错误
- API 返回 500 错误

#### 处理步骤

```bash
# 1. 检查 MySQL 容器状态
docker-compose ps mysql

# 2. 查看 MySQL 日志
docker-compose logs mysql

# 3. 检查网络连接
docker-compose exec backend ping mysql

# 4. 重启 MySQL
docker-compose restart mysql

# 5. 等待 MySQL 完全启动
sleep 10

# 6. 重启后端
docker-compose restart backend

# 7. 验证连接
docker-compose exec backend python -c "from mysql.database import get_db_connection; print('OK' if get_db_connection() else 'FAIL')"
```

### 场景 3：磁盘空间不足

#### 症状
- 无法写入日志
- 数据库操作失败

#### 处理步骤

```bash
# 1. 检查磁盘使用
df -h

# 2. 清理 Docker 资源
docker system prune -a -f

# 3. 清理旧日志
find logs/ -name "*.log.*" -mtime +7 -delete

# 4. 清理旧备份
find backups/ -type d -mtime +30 -exec rm -rf {} +

# 5. 压缩大文件
gzip logs/*.log.1

# 6. 验证空间
df -h
```

### 场景 4：数据库损坏

#### 症状
- 查询返回错误
- 表无法访问

#### 处理步骤

```bash
# 1. 停止应用
docker-compose stop backend

# 2. 备份当前数据
docker exec politics_mysql mysqldump -u root -p sz_exam > emergency_backup.sql

# 3. 检查表
docker exec -it politics_mysql mysql -u root -p -e "USE sz_exam; CHECK TABLE user, topic, exam_record;"

# 4. 修复表
docker exec -it politics_mysql mysql -u root -p -e "USE sz_exam; REPAIR TABLE user, topic, exam_record;"

# 5. 如果修复失败，从备份恢复
docker exec -i politics_mysql mysql -u root -p sz_exam < backups/latest/database.sql

# 6. 重启应用
docker-compose start backend
```

---

## 性能调优

### 数据库优化

#### 1. 索引优化

```sql
-- 分析慢查询
SHOW PROCESSLIST;

-- 添加必要的索引
CREATE INDEX idx_user_last_login ON user(last_login);
CREATE INDEX idx_topic_created ON topic(created_at);
CREATE INDEX idx_exam_user_created ON exam_record(user_id, created_at);

-- 分析索引使用情况
EXPLAIN SELECT * FROM topic WHERE month = 5 AND type_id = 1;
```

#### 2. 查询优化

```sql
-- 优化慢查询
-- 不好的查询
SELECT * FROM topic WHERE content LIKE '%时政%';

-- 优化后
SELECT id, content, type_id, answer FROM topic WHERE month = 5 LIMIT 100;

-- 使用连接代替子查询
-- 不好
SELECT * FROM user WHERE id IN (SELECT user_id FROM exam_record WHERE score > 80);

-- 优化后
SELECT DISTINCT u.* FROM user u 
INNER JOIN exam_record e ON u.id = e.user_id 
WHERE e.score > 80;
```

#### 3. 配置优化

编辑 `mysql/my.cnf`：

```ini
[mysqld]
# 连接数
max_connections = 200

# 缓冲池大小（根据服务器内存调整）
innodb_buffer_pool_size = 1G

# 查询缓存
query_cache_size = 64M
query_cache_type = 1

# 慢查询日志
slow_query_log = 1
long_query_time = 2
slow_query_log_file = /var/log/mysql/slow.log
```

### 应用优化

#### 1. Gunicorn 配置

编辑 `start.sh`：

```bash
# 根据 CPU 核心数调整 worker 数量
# workers = (2 * CPU_CORES) + 1
gunicorn --bind 0.0.0.0:5000 \
  --workers 4 \
  --threads 2 \
  --worker-class gthread \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  app:app
```

#### 2. 连接池配置

在 `mysql/database.py` 中：

```python
# 配置连接池
pool = PooledDB(
    creator=pymysql,
    maxconnections=20,  # 最大连接数
    mincached=2,        # 最小空闲连接
    maxcached=5,        # 最大空闲连接
    blocking=True,      # 连接池满时阻塞
    ping=1             # 检查连接有效性
)
```

---

## 安全审计

### 日志审计

#### 1. 访问日志分析

```bash
# 统计访问最多的 IP
awk '{print $1}' logs/access.log | sort | uniq -c | sort -rn | head -10

# 统计访问最多的接口
awk '{print $7}' logs/access.log | sort | uniq -c | sort -rn | head -10

# 查找异常请求
grep "POST" logs/access.log | grep -v "200\|201" | tail -20
```

#### 2. 错误日志分析

```bash
# 统计错误类型
grep "ERROR" logs/app.log | awk '{print $4}' | sort | uniq -c | sort -rn

# 查找最近的错误
grep "ERROR" logs/app.log | tail -20

# 分析数据库错误
grep "MySQL" logs/app.log | grep "ERROR"
```

### 安全检查清单

#### 每周检查

- [ ] 检查是否有异常登录
- [ ] 检查是否有大量失败请求
- [ ] 检查数据库访问日志
- [ ] 检查系统用户和权限
- [ ] 检查防火墙规则

#### 每月检查

- [ ] 更新系统安全补丁
- [ ] 审查用户权限
- [ ] 检查密钥是否需要轮换
- [ ] 审查备份完整性
- [ ] 进行安全扫描

---

## 附录

### 常用命令速查表

| 操作 | 命令 |
|------|------|
| 查看服务状态 | `docker-compose ps` |
| 查看日志 | `docker-compose logs -f` |
| 重启服务 | `docker-compose restart` |
| 进入容器 | `docker-compose exec backend sh` |
| 备份数据库 | `docker exec politics_mysql mysqldump -u root -p sz_exam > backup.sql` |
| 恢复数据库 | `docker exec -i politics_mysql mysql -u root -p sz_exam < backup.sql` |
| 清理 Docker | `docker system prune -a -f` |
| 查看资源使用 | `docker stats` |

### 联系方式

- **技术支持**: support@example.com
- **紧急联系**: +86 xxx-xxxx-xxxx
- **文档更新**: 2024-05-20

---

**版本**: 1.0.0  
**维护者**: 运维团队
