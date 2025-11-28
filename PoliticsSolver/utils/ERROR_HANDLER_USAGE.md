# 错误处理工具使用指南

## 概述

`error-handler.js` 提供了统一的错误处理和用户体验优化功能，包括：
- 统一的错误提示
- 自动处理登录过期
- 带加载动画的请求封装
- 登录状态检查

## 使用方法

### 1. 在页面中引入

```javascript
const ErrorHandler = require('../../utils/error-handler.js');
// 或者从 request.js 中引入
const { ErrorHandler } = require('../../utils/request.js');
```

### 2. 使用封装的请求方法

推荐使用 `ErrorHandler.request()` 方法，它会自动处理加载动画和错误：

```javascript
// 基本用法
try {
  const result = await ErrorHandler.request({
    url: 'http://localhost:8000/api/topics',
    method: 'GET',
    data: { page: 1, size: 10 },
    showLoading: true,  // 是否显示加载动画，默认true
    loadingText: '加载中...'  // 加载提示文字
  });
  
  // 处理成功结果
  console.log(result.data);
  
} catch (error) {
  // 错误已经被自动处理和显示
  console.error('请求失败', error);
}
```

### 3. 检查登录状态

在需要登录的功能中，先检查登录状态：

```javascript
onLoad: function() {
  // 检查登录状态，如果未登录会自动显示提示并跳转
  if (!ErrorHandler.checkLogin()) {
    return;
  }
  
  // 继续执行需要登录的逻辑
  this.loadUserData();
}
```

### 4. 手动处理错误

如果需要自定义错误处理：

```javascript
try {
  // 某些操作
  throw new Error('自定义错误');
} catch (error) {
  // 显示错误提示
  ErrorHandler.handle(error, true);  // 第二个参数控制是否显示toast
}
```

### 5. 显示成功/错误提示

```javascript
// 显示成功提示
ErrorHandler.showSuccess('操作成功');

// 显示错误提示
ErrorHandler.showError('操作失败，请重试');
```

## 完整示例

### 示例1：获取题目列表

```javascript
Page({
  data: {
    topics: []
  },
  
  async onLoad() {
    await this.loadTopics();
  },
  
  async loadTopics() {
    try {
      const result = await ErrorHandler.request({
        url: 'http://localhost:8000/api/topics',
        method: 'GET',
        data: {
          page: 1,
          size: 20
        }
      });
      
      this.setData({
        topics: result.data.list
      });
      
    } catch (error) {
      // 错误已自动处理
      console.error('加载题目失败', error);
    }
  }
});
```

### 示例2：提交答题结果（需要登录）

```javascript
Page({
  async submitAnswer() {
    // 先检查登录状态
    if (!ErrorHandler.checkLogin()) {
      return;
    }
    
    try {
      const token = wx.getStorageSync('token');
      
      const result = await ErrorHandler.request({
        url: 'http://localhost:8000/api/exam/submit',
        method: 'POST',
        data: {
          score: 85,
          totalQuestions: 20,
          correctCount: 17
        },
        header: {
          'Authorization': `Bearer ${token}`
        },
        loadingText: '提交中...'
      });
      
      ErrorHandler.showSuccess('提交成功');
      
      // 跳转到结果页
      wx.navigateTo({
        url: `/pages/result/result?recordId=${result.data.recordId}`
      });
      
    } catch (error) {
      // 错误已自动处理
    }
  }
});
```

### 示例3：使用现有的 request.js

如果你已经在使用 `utils/request.js`，它已经集成了 ErrorHandler：

```javascript
const { get, post, ErrorHandler } = require('../../utils/request.js');

Page({
  async loadData() {
    try {
      // 使用封装的 get 方法
      const result = await get('/api/topics', { page: 1 }, true);  // 第三个参数表示需要认证
      
      this.setData({
        topics: result.data.list
      });
      
    } catch (error) {
      // 错误已自动处理
    }
  },
  
  async submitData() {
    // 先检查登录
    if (!ErrorHandler.checkLogin()) {
      return;
    }
    
    try {
      // 使用封装的 post 方法
      const result = await post('/api/exam/submit', {
        score: 90
      }, true);  // 需要认证
      
      ErrorHandler.showSuccess('提交成功');
      
    } catch (error) {
      // 错误已自动处理
    }
  }
});
```

## 错误类型处理

ErrorHandler 会自动处理以下错误类型：

- **401 未授权**: 自动清除token并跳转到登录页
- **403 禁止访问**: 显示"没有权限访问"
- **404 未找到**: 显示"请求的资源不存在"
- **500+ 服务器错误**: 显示"服务器错误，请稍后重试"
- **网络错误**: 显示"网络连接失败，请检查网络设置"
- **超时错误**: 显示"请求超时，请重试"

## 注意事项

1. 所有需要认证的接口都应该先调用 `ErrorHandler.checkLogin()` 检查登录状态
2. 使用 `ErrorHandler.request()` 时，错误会自动显示toast提示，无需手动处理
3. 如果不想显示加载动画，设置 `showLoading: false`
4. 登录过期时会自动跳转到首页，无需手动处理
