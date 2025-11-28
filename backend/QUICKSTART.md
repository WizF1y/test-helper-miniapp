# 快速开始指南

本指南帮助您在 5 分钟内快速部署和运行教师编时政刷题系统。

## 前置要求

- Docker 20.10+
- Docker Compose 1.29+
- 2GB+ 可用内存
- 10GB+ 可用磁盘空间

## 快速部署（3 步）

### 第 1 步：克隆项目

```bash
git clone <repository-url>
cd backend
```

### 第 2 步：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件（必须修改以下项）
nano .env
```

**必须修改的配置项**：

```bash
# 微信小程序配置（从微信公众平台获取）
WECHAT_APPID=your_wechat_app_id
WECHAT_SECRET=your_wechat_app_secret

# 数据库密码（设置强密码）
MYSQL_PASSWORD=your_secure_password

# JWT 密钥（生成强随机字符串）
SECRET_KEY=your_jwt_secret_key

# 管理员密钥（生成强随机字符串）
ADMIN_KEY=your_admin_key
```

**生成安全密钥**：

```bash
# 生成 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成 ADMIN_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 第 3 步：启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

等待约 30 秒，服务启动完成！

## 验证部署

### 1. 检查服务状态

```bash
docker-compose ps
```

预期输出：
```
NAME                COMMAND             STATUS          PORTS
politics_backend    sh /app/start.sh    Up              0.0.0.0:5000->5000/tcp
politics_mysql      docker-entrypoint   Up (healthy)    0.0.0.0:3306->3306/tcp
```

### 2. 测试 API

```bash
# 测试健康检查接口
curl http://localhost:5000/api/health

# 预期返回
{"status": "ok"}
```

### 3. 检查数据库

```bash
# 进入 MySQL 容器
docker exec -it politics_mysql mysql -u root -p

# 输入密码后执行
USE sz_exam;
SHOW TABLES;

# 应该看到以下表
# - user
# - topic
# - user_mistake
# - user_favorite
# - exam_record
# - exam_detail
# - user_topic_progress
# - payment
```

## 导入题目数据

### 方式 1：使用 PDF 导入

```bash
# 将 PDF 文件放到 questions 目录
cp your_questions.pdf backend/questions/

# 进入后端容器
docker-compose exec backend sh

# 运行导入脚本
python questions/extractPDF.py
```

### 方式 2：使用测试数据

```bash
# 运行测试导入脚本
docker-compose exec backend python scripts/test_import.py
```

## 配置小程序

### 1. 修改小程序配置

编辑 `PoliticsSolver/utils/request.js`：

```javascript
const BASE_URL = 'http://your-server-ip:5000/api';
```

### 2. 配置微信开发者工具

1. 打开微信开发者工具
2. 导入项目，选择 `PoliticsSolver` 目录
3. 填入 AppID
4. 点击"编译"

### 3. 测试小程序

- 点击"登录"按钮
- 浏览题目列表
- 尝试答题功能

## 常用操作

### 查看日志

```bash
# 查看所有日志
docker-compose logs -f

# 只查看后端日志
docker-compose logs -f backend

# 只查看 MySQL 日志
docker-compose logs -f mysql
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 只重启后端
docker-compose restart backend
```

### 停止服务

```bash
# 停止所有服务
docker-compose stop

# 完全停止并删除容器
docker-compose down
```

### 备份数据

```bash
# 备份数据库
docker exec politics_mysql mysqldump -u root -p<password> sz_exam > backup_$(date +%Y%m%d).sql

# 备份题目文件
tar -czf questions_backup_$(date +%Y%m%d).tar.gz questions/
```

## 故障排查

### 问题 1：容器启动失败

```bash
# 查看详细日志
docker-compose logs backend

# 常见原因：
# - 端口被占用：修改 docker-compose.yml 中的端口
# - 环境变量错误：检查 .env 文件
# - 内存不足：增加 Docker 内存限制
```

### 问题 2：无法连接数据库

```bash
# 检查 MySQL 是否启动
docker-compose ps mysql

# 查看 MySQL 日志
docker-compose logs mysql

# 测试连接
docker-compose exec backend ping mysql
```

### 问题 3：API 返回 500 错误

```bash
# 查看应用日志
docker-compose logs backend | tail -50

# 进入容器调试
docker-compose exec backend sh
python app.py
```

## 下一步

- 📖 阅读 [部署文档](DEPLOYMENT.md) 了解详细配置
- 🔧 阅读 [运维手册](OPERATIONS_MANUAL.md) 了解日常维护
- 🔐 配置 HTTPS 和域名
- 📊 设置监控和告警
- 💾 配置自动备份

## 获取帮助

- 查看文档：`DEPLOYMENT.md`
- 查看运维手册：`OPERATIONS_MANUAL.md`
- 提交 Issue：GitHub Issues
- 技术支持：support@example.com

---

**祝您使用愉快！** 🎉
