# 教师编时政刷题系统 - 后端服务

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)

基于 Flask + MySQL 的教师编制考试时政题库后端服务，为微信小程序提供 RESTful API 接口。

## ✨ 功能特性

- 🔐 **用户认证**：基于微信登录和 JWT 的安全认证
- 📚 **题库管理**：支持单选、多选、判断题，按月份和地区分类
- 📝 **多种练习模式**：随机练习、专项练习、模拟考试
- ❌ **智能错题本**：自动收集错题，支持筛选和统计
- ⭐ **收藏功能**：收藏重点题目，方便复习
- 📊 **学习进度**：详细的学习统计和进度追踪
- 💰 **支付集成**：支持微信支付打赏功能
- 🔧 **管理接口**：题目导入、备份、数据管理

## 📋 目录

- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API 文档](#api-文档)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [维护手册](#维护手册)

## 🚀 快速开始

### 使用 Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd backend

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要配置

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

服务启动后访问：`http://localhost:5000`

详细步骤请参考 [快速开始指南](QUICKSTART.md)

### 本地开发环境

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 MySQL（使用 Docker）
docker run -d --name mysql -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=sz_exam \
  mysql:8.0

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，设置 MYSQL_HOST=localhost

# 5. 启动应用
python app.py
```

## 📁 项目结构

```
backend/
├── app.py                      # 主应用入口
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 配置
├── docker-compose.yml          # Docker Compose 配置
├── start.sh                    # 启动脚本
├── .env.example               # 环境变量模板
│
├── mysql/                     # MySQL 配置
│   ├── Dockerfile            # MySQL Docker 配置
│   ├── init.sql             # 数据库初始化脚本
│   └── my.cnf               # MySQL 配置文件
│
├── middleware/               # 中间件
│   ├── __init__.py
│   └── auth.py              # JWT 认证中间件
│
├── config/                  # 配置文件
│   └── logging.py          # 日志配置
│
├── questions/              # 题目管理
│   ├── extractPDF.py      # PDF 解析脚本
│   └── *.pdf              # 题目 PDF 文件
│
├── scripts/               # 管理脚本
│   ├── backup_topics.py  # 题目备份脚本
│   ├── test_import.py    # 测试数据导入
│   └── verify_*.py       # 验证脚本
│
├── logs/                 # 日志目录
│   ├── app.log          # 应用日志
│   ├── access.log       # 访问日志
│   └── error.log        # 错误日志
│
└── docs/                # 文档
    ├── README.md              # 本文件
    ├── QUICKSTART.md          # 快速开始
    ├── DEPLOYMENT.md          # 部署文档
    ├── OPERATIONS_MANUAL.md   # 运维手册
    ├── AUTH_README.md         # 认证说明
    ├── TOPIC_MANAGEMENT_README.md  # 题目管理
    └── ERROR_HANDLING_IMPLEMENTATION.md  # 错误处理
```

## 📡 API 文档

### 认证接口

#### 用户登录
```http
POST /api/login
Content-Type: application/json

{
  "code": "wx_login_code"
}

Response:
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "token": "jwt_token",
    "userInfo": {
      "id": 123456,
      "nickname": "用户昵称",
      "avatarUrl": "头像URL"
    }
  }
}
```

### 题目接口

#### 获取题目列表
```http
GET /api/topics?month=5&type=1&page=1&size=20
Authorization: Bearer {token}

Response:
{
  "code": 0,
  "data": {
    "topics": [...],
    "total": 100,
    "page": 1,
    "size": 20
  }
}
```

#### 随机获取题目
```http
GET /api/topics/random?startMonth=1&endMonth=12&count=20
Authorization: Bearer {token}

Response:
{
  "code": 0,
  "data": [
    {
      "id": 1,
      "content": "题目内容",
      "type": 1,
      "options": [...],
      "answer": "A",
      "analysis": "解析"
    }
  ]
}
```

### 错题本接口

#### 添加错题
```http
POST /api/mistake/add
Authorization: Bearer {token}
Content-Type: application/json

{
  "topicId": 1
}
```

#### 获取错题列表
```http
GET /api/mistake/list?month=5&type=1
Authorization: Bearer {token}

Response:
{
  "code": 0,
  "data": [...]
}
```

### 考试接口

#### 提交考试
```http
POST /api/exam/submit
Authorization: Bearer {token}
Content-Type: application/json

{
  "score": 85,
  "totalQuestions": 20,
  "correctCount": 17,
  "usedTime": 1500,
  "details": [...]
}
```

完整 API 文档请参考各功能模块的 README 文件。

## 🛠️ 开发指南

### 添加新的 API 接口

1. 在 `app.py` 中定义路由：

```python
@app.route('/api/your-endpoint', methods=['POST'])
@token_required  # 如果需要认证
def your_function():
    try:
        # 获取请求参数
        data = request.get_json()
        
        # 业务逻辑
        result = process_data(data)
        
        # 返回响应
        return jsonify({
            'code': 0,
            'message': '成功',
            'data': result
        })
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({
            'code': 500,
            'message': str(e)
        }), 500
```

2. 添加数据库操作：

```python
from mysql.database import get_db_connection

def process_data(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM table WHERE id = %s", (data['id'],))
        result = cursor.fetchall()
        return result
    finally:
        cursor.close()
        conn.close()
```

### 运行测试

```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python scripts/verify_implementation.py

# 测试错误处理
python test_error_handling.py
```

### 代码规范

- 使用 PEP 8 代码风格
- 添加适当的注释和文档字符串
- 使用类型提示（Python 3.9+）
- 错误处理要完善
- 记录重要操作日志

## 📦 部署指南

### 生产环境部署

详细部署步骤请参考 [部署文档](DEPLOYMENT.md)

关键步骤：

1. **服务器准备**
   - 安装 Docker 和 Docker Compose
   - 配置防火墙规则
   - 设置域名和 SSL 证书

2. **配置环境变量**
   - 使用强密码和密钥
   - 关闭调试模式
   - 配置生产数据库

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **配置反向代理**
   - 使用 Nginx 作为反向代理
   - 配置 HTTPS
   - 设置请求限流

5. **监控和备份**
   - 配置日志监控
   - 设置自动备份
   - 配置告警通知

### 性能优化

- 调整 Gunicorn worker 数量
- 配置数据库连接池
- 添加 Redis 缓存
- 优化数据库索引
- 启用 gzip 压缩

## 🔧 维护手册

日常运维操作请参考 [运维手册](OPERATIONS_MANUAL.md)

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 备份数据库
docker exec politics_mysql mysqldump -u root -p sz_exam > backup.sql

# 进入容器
docker-compose exec backend sh
```

### 监控指标

- API 响应时间
- 错误率
- 数据库连接数
- 内存和 CPU 使用率
- 磁盘空间

### 备份策略

- 每日自动备份数据库
- 保留最近 30 天的备份
- 定期测试恢复流程

## 📚 相关文档

- [快速开始指南](QUICKSTART.md) - 5 分钟快速部署
- [部署文档](DEPLOYMENT.md) - 详细的部署说明
- [运维手册](OPERATIONS_MANUAL.md) - 日常运维操作
- [认证说明](AUTH_README.md) - JWT 认证实现
- [题目管理](TOPIC_MANAGEMENT_README.md) - 题目导入和管理
- [错误处理](ERROR_HANDLING_IMPLEMENTATION.md) - 错误处理机制

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

- 项目主页：<repository-url>
- 问题反馈：GitHub Issues
- 技术支持：support@example.com

## 🙏 致谢

感谢所有贡献者和使用者的支持！

---

**最后更新**: 2024-05-20  
**版本**: 1.0.0
