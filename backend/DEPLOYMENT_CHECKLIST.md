# 部署检查清单

使用本清单确保系统正确部署和配置。

## 部署前检查

### 环境准备

- [ ] 服务器满足最低要求（2核 CPU，4GB RAM，20GB 存储）
- [ ] 已安装 Docker 20.10+
- [ ] 已安装 Docker Compose 1.29+
- [ ] 防火墙已配置（开放 5000 和 3306 端口）
- [ ] 已获取微信小程序 AppID 和 AppSecret

### 配置文件

- [ ] 已复制 `.env.example` 到 `.env`
- [ ] 已设置 `WECHAT_APPID`
- [ ] 已设置 `WECHAT_SECRET`
- [ ] 已设置强 `MYSQL_PASSWORD`（至少 16 字符）
- [ ] 已生成并设置 `SECRET_KEY`（使用 `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] 已生成并设置 `ADMIN_KEY`
- [ ] 已设置 `DEBUG_MODE=False`（生产环境）
- [ ] 已设置 `MYSQL_HOST=mysql`（Docker 环境）

### 文件权限

- [ ] `start.sh` 有执行权限（`chmod +x start.sh`）
- [ ] `scripts/health_check.sh` 有执行权限
- [ ] `logs/` 目录存在且可写
- [ ] `questions/` 目录存在且可写

## 部署过程检查

### 构建和启动

- [ ] 运行 `docker-compose build` 成功
- [ ] 运行 `docker-compose up -d` 成功
- [ ] 等待 30 秒让服务完全启动

### 容器状态

- [ ] `docker-compose ps` 显示所有容器状态为 `Up`
- [ ] MySQL 容器健康检查状态为 `healthy`
- [ ] 后端容器没有重启循环

### 日志检查

- [ ] `docker-compose logs mysql` 没有错误
- [ ] `docker-compose logs backend` 显示 "MySQL is up and running!"
- [ ] `docker-compose logs backend` 显示 "Database connection successful!"
- [ ] `docker-compose logs backend` 显示应用启动成功

## 功能验证

### 数据库验证

- [ ] 可以连接到 MySQL：`docker exec -it politics_mysql mysql -u root -p`
- [ ] 数据库 `sz_exam` 存在
- [ ] 所有表已创建（8 个表）：
  - [ ] `user`
  - [ ] `topic`
  - [ ] `user_mistake`
  - [ ] `user_favorite`
  - [ ] `exam_record`
  - [ ] `exam_detail`
  - [ ] `user_topic_progress`
  - [ ] `payment`

验证命令：
```sql
USE sz_exam;
SHOW TABLES;
```

### API 验证

- [ ] 健康检查接口可访问：`curl http://localhost:5000/api/health`
- [ ] 返回 `{"status": "ok"}`
- [ ] 登录接口可访问（返回正确的错误信息）
- [ ] 题目列表接口需要认证（返回 401）

### 网络验证

- [ ] 后端可以 ping 通 MySQL：`docker-compose exec backend ping mysql`
- [ ] 外部可以访问 API（如果配置了公网访问）
- [ ] 小程序可以连接到后端 API

## 安全检查

### 密钥和密码

- [ ] 所有密钥都是强随机字符串（至少 32 字符）
- [ ] `.env` 文件不在版本控制中
- [ ] MySQL root 密码足够强（至少 16 字符，包含大小写字母、数字、特殊字符）
- [ ] 生产环境已关闭调试模式（`DEBUG_MODE=False`）

### 访问控制

- [ ] 数据库端口（3306）不对外开放（仅容器内部访问）
- [ ] 已配置防火墙规则
- [ ] 如果使用公网，已配置 HTTPS
- [ ] 已配置反向代理（Nginx）

### 文件权限

- [ ] `.env` 文件权限为 600：`chmod 600 .env`
- [ ] 日志目录权限正确
- [ ] 敏感文件不可被其他用户读取

## 性能检查

### 资源使用

- [ ] CPU 使用率正常（< 70%）
- [ ] 内存使用率正常（< 80%）
- [ ] 磁盘空间充足（> 20% 可用）
- [ ] 容器资源使用正常：`docker stats`

### 响应时间

- [ ] API 响应时间 < 500ms
- [ ] 数据库查询时间正常
- [ ] 没有慢查询

## 监控和备份

### 日志配置

- [ ] 日志文件正常写入
- [ ] 日志轮转配置正确
- [ ] 错误日志可以正常记录

### 备份配置

- [ ] 备份脚本可以正常运行
- [ ] 备份目录存在且可写
- [ ] 已配置自动备份（cron job）
- [ ] 已测试恢复流程

### 监控配置

- [ ] 已配置健康检查脚本
- [ ] 已配置告警通知（可选）
- [ ] 已配置日志监控（可选）

## 生产环境额外检查

### HTTPS 配置

- [ ] 已安装 SSL 证书
- [ ] HTTPS 可以正常访问
- [ ] HTTP 自动重定向到 HTTPS
- [ ] 证书自动续期已配置

### 反向代理

- [ ] Nginx 配置正确
- [ ] 已配置请求限流
- [ ] 已配置 gzip 压缩
- [ ] 已配置超时设置

### 域名配置

- [ ] 域名 DNS 解析正确
- [ ] 域名可以正常访问
- [ ] 小程序配置了正确的域名

### 高可用配置（可选）

- [ ] 数据库主从复制
- [ ] 负载均衡配置
- [ ] 自动故障转移

## 文档检查

- [ ] 已记录服务器信息
- [ ] 已记录配置信息（不包含密码）
- [ ] 已记录部署日期和版本
- [ ] 已记录紧急联系方式
- [ ] 团队成员知道如何访问系统

## 测试验证

### 功能测试

- [ ] 用户可以正常登录
- [ ] 可以获取题目列表
- [ ] 可以提交答案
- [ ] 错题本功能正常
- [ ] 收藏功能正常
- [ ] 考试功能正常

### 压力测试（可选）

- [ ] 系统可以处理预期的并发用户数
- [ ] 数据库连接池配置合理
- [ ] 没有内存泄漏

### 故障恢复测试

- [ ] 重启容器后服务正常
- [ ] 数据库重启后服务正常
- [ ] 从备份恢复数据成功

## 上线后检查

### 第一天

- [ ] 监控错误日志
- [ ] 检查用户反馈
- [ ] 验证所有功能正常
- [ ] 检查性能指标

### 第一周

- [ ] 每日检查日志
- [ ] 监控资源使用
- [ ] 验证备份正常
- [ ] 收集用户反馈

### 第一月

- [ ] 每周检查系统状态
- [ ] 分析性能数据
- [ ] 优化慢查询
- [ ] 更新文档

## 问题记录

如果发现问题，请记录：

| 日期 | 问题描述 | 解决方案 | 负责人 |
|------|----------|----------|--------|
|      |          |          |        |

## 签署确认

- [ ] 部署工程师已完成所有检查项
- [ ] 技术负责人已审核
- [ ] 已通知相关团队成员

**部署工程师**: ________________  
**日期**: ________________  
**签名**: ________________

**技术负责人**: ________________  
**日期**: ________________  
**签名**: ________________

---

## 快速命令参考

```bash
# 健康检查
bash scripts/health_check.sh

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart

# 备份数据库
docker exec politics_mysql mysqldump -u root -p sz_exam > backup.sql

# 查看资源使用
docker stats
```

---

**版本**: 1.0.0  
**最后更新**: 2024-05-20
