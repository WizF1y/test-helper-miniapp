# JWT认证使用说明

## 概述

本系统使用JWT (JSON Web Token) 进行用户认证和授权。所有需要用户身份验证的API接口都需要在请求头中携带有效的token。

## 认证流程

### 1. 用户登录

用户通过微信小程序登录接口获取token：

```bash
POST /api/login
Content-Type: application/json

{
  "code": "微信登录code",
  "userInfo": {
    "nickName": "用户昵称",
    "avatarUrl": "头像URL"
  }
}
```

响应：
```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "userId": 123,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "nickname": "用户昵称",
    "avatarUrl": "头像URL"
  }
}
```

### 2. 使用Token访问受保护的API

在请求头中添加Authorization字段：

```bash
GET /api/user/statistics
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 受保护的API接口

以下接口需要JWT认证：

### 用户相关
- `GET /api/user/statistics` - 获取用户统计信息
- `GET /api/user/month-progress` - 获取每月做题进度

### 错题本相关
- `POST /api/mistake/add` - 添加错题
- `GET /api/mistake/list` - 获取错题列表
- `POST /api/mistake/delete` - 删除错题
- `POST /api/mistake/clear` - 清空错题

### 收藏相关
- `POST /api/favorite/add` - 添加收藏
- `GET /api/favorite/list` - 获取收藏列表
- `POST /api/favorite/delete` - 取消收藏
- `POST /api/favorite/clear` - 清空收藏

### 考试相关
- `POST /api/exam/submit` - 提交考试结果

### 进度相关
- `POST /api/progress/finish-topic` - 记录完成题目

## Token说明

- **有效期**: 7天
- **算法**: HS256
- **密钥**: 配置在环境变量 `SECRET_KEY` 中
- **包含信息**: 
  - `user_id`: 用户ID
  - `openid`: 微信OpenID
  - `exp`: 过期时间

## 错误处理

### 401 未授权

当token缺失、过期或无效时，API会返回401错误：

```json
{
  "code": 401,
  "message": "缺少认证token"
}
```

或

```json
{
  "code": 401,
  "message": "Token已过期"
}
```

或

```json
{
  "code": 401,
  "message": "无效的token"
}
```

前端应该在收到401错误时：
1. 清除本地存储的token和用户信息
2. 提示用户重新登录
3. 跳转到登录页面

## 前端集成

### 使用封装的请求工具

前端已经提供了封装好的请求工具 `utils/request.js`，自动处理token和错误：

```javascript
const request = require('./utils/request.js')

// 需要认证的请求
request.post('/api/mistake/add', {
  topicId: 123
}, true).then(res => {
  console.log('成功:', res)
}).catch(err => {
  console.error('失败:', err)
})

// 不需要认证的请求
request.get('/api/topics', {
  page: 1,
  size: 10
}, false).then(res => {
  console.log('成功:', res)
})
```

### 手动添加Token

如果需要手动发送请求：

```javascript
const userInfo = wx.getStorageSync('USER_INFO')
const token = userInfo ? userInfo.token : null

wx.request({
  url: 'http://localhost:8000/api/user/statistics',
  method: 'GET',
  header: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  success: (res) => {
    if (res.statusCode === 401) {
      // Token过期，跳转到登录页
      wx.redirectTo({
        url: '/pages/index/index'
      })
    }
  }
})
```

## 调试模式

在开发环境中，可以启用调试模式跳过微信登录验证：

在 `.env` 文件中设置：
```
DEBUG_MODE=True
DEBUG_OPENID=test_openid_12345
```

这样登录接口会使用固定的openid，无需真实的微信code。

**注意**: 生产环境必须关闭调试模式！

## 安全建议

1. **SECRET_KEY**: 使用强随机字符串，不要使用默认值
2. **HTTPS**: 生产环境必须使用HTTPS传输token
3. **Token存储**: 小程序端使用 `wx.setStorageSync` 安全存储token
4. **定期更新**: 考虑实现token刷新机制
5. **日志记录**: 记录所有认证失败的尝试
