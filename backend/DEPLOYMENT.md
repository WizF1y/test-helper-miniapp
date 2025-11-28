# 部署文档

## 目录

1. [系统要求](#系统要求)
2. [快速开始](#快速开始)
3. [开发环境部署](#开发环境部署)
4. [生产环境部署](#生产环境部署)
5. [配置说明](#配置说明)
6. [数据库管理](#数据库管理)
7. [监控和维护](#监控和维护)
8. [故障排查](#故障排查)
9. [安全建议](#安全建议)

---

## 系统要求

### 硬件要求

- **CPU**: 2核心或以上
- **内存**: 4GB RAM 或以上
- **存储**: 20GB 可用空间或以上

### 软件要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+) / macOS / Windows
- **Docker**: 20.10+ 
- **Docker Compose**: 1.29+
- **Python**: 3.9+ (仅本地开发需要)
- **MySQL**: 8.0+ (Docker 部署已包含)

---

## 快速开始

### 使用 Docker Compose 部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd backend

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 检查服务状态
docker-compose ps
```

服务启动后，后端 API 将在 `http://localhost:5000` 可用。

---

## 开发环境部署

### 方式一：本地 Python 环境

#### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 启动 MySQL 数据库

```bash
# 使用 Docker 启动 MySQL
cd mysql
docker build -t politics-mysql .
docker run -d \
  --name politics-mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=sz_exam \
  -v mysql_data:/var/lib/mysql \
  politics-mysql
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
# 设置 MYSQL_HOST=localhost
# 设置 DEBUG_MODE=True
```

#### 4. 初始化数据库

数据库表会在 MySQL 容器启动时自动创建（通过 init.sql）。

#### 5. 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

### 方式二：完全 Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

---

## 生产环境部署

### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 部署应用

```bash
# 克隆代码
git clone <repository-url>
cd backend

# 配置生产环境变量
cp .env.example .env
nano .env  # 或使用其他编辑器
```

**重要配置项**：
- `DEBUG_MODE=False`
- `MYSQL_PASSWORD=<强密码>`
- `SECRET_KEY=<强随机字符串>`
- `ADMIN_KEY=<强随机字符串>`
- `MYSQL_HOST=mysql`

```bash
# 启动服务
docker-compose up -d

# 验证服务状态
docker-compose ps
docker-compose logs backend
```

### 3. 配置反向代理（可选但推荐）

使用 Nginx 作为反向代理：

```nginx
# /etc/nginx/sites-available/politics-api
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/politics-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. 配置 HTTPS（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d api.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 配置说明

### 环境变量详解

| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| `WECHAT_APPID` | 微信小程序 AppID | 是 | - |
| `WECHAT_SECRET` | 微信小程序 AppSecret | 是 | - |
| `DEBUG_MODE` | 调试模式 | 否 | False |
| `MYSQL_USER` | MySQL 用户名 | 是 | root |
| `MYSQL_PASSWORD` | MySQL 密码 | 是 | - |
| `MYSQL_HOST` | MySQL 主机 | 是 | localhost |
| `MYSQL_DATABASE` | 数据库名称 | 是 | sz_exam |
| `SECRET_KEY` | JWT 密钥 | 是 | - |
| `ADMIN_KEY` | 管理员密钥 | 是 | - |

### 生成安全密钥

```bash
# 生成 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成 ADMIN_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 数据库管理

### 备份数据库

```bash
# 使用 Docker 备份
docker exec politics_mysql mysqldump -u root -p<password> sz_exam > backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用脚本
python scripts/backup_topics.py
```

### 恢复数据库

```bash
# 从备份文件恢复
docker exec -i politics_mysql mysql -u root -p<password> sz_exam < backup.sql
```

### 查看数据库状态

```bash
# 进入 MySQL 容器
docker exec -it politics_mysql mysql -u root -p

# 查看数据库
SHOW DATABASES;
USE sz_exam;
SHOW TABLES;

# 查看表结构
DESCRIBE user;
DESCRIBE topic;
```

### 数据库迁移

如果需要更新表结构：

1. 修改 `mysql/init.sql` 文件
2. 重新构建并启动服务：

```bash
docker-compose down
docker-compose up -d --build
```

**注意**：这会重新创建数据库，请先备份数据！

---

## 监控和维护

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看 MySQL 日志
docker-compose logs -f mysql

# 查看应用日志文件
tail -f logs/app.log
tail -f logs/access.log
tail -f logs/error.log
```

### 服务管理

```bash
# 启动服务
docker-compose start

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 重启单个服务
docker-compose restart backend

# 查看服务状态
docker-compose ps

# 查看资源使用
docker stats
```

### 更新应用

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose down
docker-compose up -d --build

# 查看日志确认启动成功
docker-compose logs -f backend
```

### 清理资源

```bash
# 停止并删除容器
docker-compose down

# 删除容器和卷（会删除数据库数据！）
docker-compose down -v

# 清理未使用的 Docker 资源
docker system prune -a
```

---

## 故障排查

### 问题 1：MySQL 连接失败

**症状**：后端日志显示 "Can't connect to MySQL server"

**解决方案**：

```bash
# 1. 检查 MySQL 容器状态
docker-compose ps mysql

# 2. 查看 MySQL 日志
docker-compose logs mysql

# 3. 检查网络连接
docker-compose exec backend ping mysql

# 4. 验证环境变量
docker-compose exec backend env | grep MYSQL
```

### 问题 2：后端启动失败

**症状**：backend 容器不断重启

**解决方案**：

```bash
# 1. 查看详细日志
docker-compose logs backend

# 2. 检查环境变量配置
cat .env

# 3. 手动进入容器调试
docker-compose run --rm backend sh
python app.py
```

### 问题 3：端口被占用

**症状**：启动时提示端口已被使用

**解决方案**：

```bash
# 查看端口占用
sudo lsof -i :5000
sudo lsof -i :3306

# 修改 docker-compose.yml 中的端口映射
# 或停止占用端口的进程
```

### 问题 4：数据库表不存在

**症状**：API 请求返回表不存在错误

**解决方案**：

```bash
# 1. 检查 init.sql 是否正确执行
docker-compose logs mysql | grep init.sql

# 2. 手动执行初始化脚本
docker exec -i politics_mysql mysql -u root -p<password> sz_exam < mysql/init.sql

# 3. 重新创建数据库
docker-compose down -v
docker-compose up -d
```

### 问题 5：权限问题

**症状**：无法写入日志文件或创建目录

**解决方案**：

```bash
# 创建必要的目录
mkdir -p logs questions

# 设置权限
chmod -R 755 logs questions

# 或在 Docker 中使用正确的用户
```

---

## 安全建议

### 1. 环境变量安全

- ✅ 使用强随机密钥（至少 32 字符）
- ✅ 不要将 `.env` 文件提交到版本控制
- ✅ 定期更换密钥
- ✅ 使用环境变量管理工具（如 AWS Secrets Manager）

### 2. 数据库安全

- ✅ 使用强密码
- ✅ 限制数据库访问 IP
- ✅ 定期备份数据
- ✅ 启用 MySQL 慢查询日志监控性能

### 3. 网络安全

- ✅ 使用 HTTPS
- ✅ 配置防火墙规则
- ✅ 使用反向代理（Nginx）
- ✅ 启用请求限流

### 4. 应用安全

- ✅ 生产环境关闭 DEBUG 模式
- ✅ 定期更新依赖包
- ✅ 实施日志监控和告警
- ✅ 定期审查访问日志

### 5. Docker 安全

- ✅ 使用官方基础镜像
- ✅ 定期更新镜像
- ✅ 限制容器资源使用
- ✅ 使用非 root 用户运行容器

---

## 性能优化

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_user_created ON user(created_at);
CREATE INDEX idx_topic_month_type ON topic(month, type_id);

-- 定期优化表
OPTIMIZE TABLE user;
OPTIMIZE TABLE topic;
```

### 2. 应用优化

- 增加 Gunicorn worker 数量（根据 CPU 核心数）
- 启用数据库连接池
- 使用 Redis 缓存热点数据
- 启用 gzip 压缩

### 3. 监控指标

- API 响应时间
- 数据库查询性能
- 内存和 CPU 使用率
- 错误率和异常日志

---

## 附录

### A. 常用命令速查

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 备份数据库
docker exec politics_mysql mysqldump -u root -p sz_exam > backup.sql

# 进入容器
docker-compose exec backend sh
docker-compose exec mysql mysql -u root -p
```

### B. 目录结构

```
backend/
├── app.py                  # 主应用文件
├── requirements.txt        # Python 依赖
├── Dockerfile             # 后端 Docker 配置
├── docker-compose.yml     # Docker Compose 配置
├── start.sh              # 启动脚本
├── .env                  # 环境变量（不提交到 Git）
├── .env.example          # 环境变量模板
├── mysql/
│   ├── Dockerfile        # MySQL Docker 配置
│   ├── init.sql         # 数据库初始化脚本
│   └── my.cnf           # MySQL 配置
├── logs/                # 日志目录
├── questions/           # 题目文件目录
├── scripts/            # 管理脚本
└── middleware/         # 中间件
```

### C. 技术支持

如遇到问题，请：

1. 查看本文档的故障排查部分
2. 检查日志文件
3. 查看 GitHub Issues
4. 联系技术支持团队

---

**最后更新**: 2024-05-20
**版本**: 1.0.0
