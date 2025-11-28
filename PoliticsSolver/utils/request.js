/**
 * 封装的网络请求工具
 * 自动添加token到请求头，处理token过期等情况
 */

const ErrorHandler = require('./error-handler.js');
const API_BASE_URL = 'http://localhost:8000';

/**
 * 获取存储的token
 */
function getToken() {
  try {
    // 直接从 TOKEN 存储中获取
    const token = wx.getStorageSync('TOKEN');
    return token || null;
  } catch (e) {
    console.error('获取token失败', e);
    return null;
  }
}

/**
 * 处理token过期，跳转到登录页
 */
function handleTokenExpired() {
  console.log('Token已过期，跳转到登录页');
  
  // 清除本地存储的用户信息和token
  try {
    wx.removeStorageSync('USER_INFO');
    wx.removeStorageSync('TOKEN');
  } catch (e) {
    console.error('清除用户信息失败', e);
  }
  
  // 更新全局登录状态
  const app = getApp();
  if (app) {
    app.globalData.hasLogin = false;
    app.globalData.userInfo = null;
    app.globalData.token = null;
  }
  
  // 显示提示
  wx.showToast({
    title: '登录已过期，请重新登录',
    icon: 'none',
    duration: 2000
  });
  
  // 延迟跳转，让用户看到提示
  setTimeout(() => {
    wx.redirectTo({
      url: '/pages/index/index',
      fail: () => {
        // 如果当前已经在首页，则不跳转
        console.log('已在登录页');
      }
    });
  }, 2000);
}

/**
 * 封装的请求方法
 * @param {Object} options 请求配置
 * @param {String} options.url 请求路径（相对路径，会自动拼接baseUrl）
 * @param {String} options.method 请求方法，默认GET
 * @param {Object} options.data 请求数据
 * @param {Boolean} options.needAuth 是否需要认证，默认false
 * @param {Boolean} options.showLoading 是否显示加载动画，默认true
 * @returns {Promise}
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    needAuth = false,
    showLoading = true
  } = options;
  
  return new Promise((resolve, reject) => {
    // 如果需要认证，先检查登录状态
    if (needAuth && !ErrorHandler.checkLogin(false)) {
      ErrorHandler.showError('请先登录');
      setTimeout(() => {
        wx.reLaunch({
          url: '/pages/index/index'
        });
      }, 1500);
      reject(new Error('未登录'));
      return;
    }
    
    // 显示加载动画
    if (showLoading) {
      wx.showLoading({
        title: '加载中...',
        mask: true
      });
    }
    
    // 构建请求头
    const header = {
      'Content-Type': 'application/json'
    };
    
    // 如果需要认证，添加token
    if (needAuth) {
      const token = getToken();
      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      }
    }
    
    // 发起请求
    wx.request({
      url: `${API_BASE_URL}${url}`,
      method: method,
      data: data,
      header: header,
      success: (res) => {
        if (showLoading) {
          wx.hideLoading();
        }
        
        // 处理HTTP状态码
        if (res.statusCode === 401) {
          // Token过期或无效
          handleTokenExpired();
          reject(new Error('认证失败'));
          return;
        }
        
        if (res.statusCode !== 200) {
          ErrorHandler.handle({
            statusCode: res.statusCode,
            data: res.data
          });
          reject(new Error(`HTTP ${res.statusCode}`));
          return;
        }
        
        // 处理业务状态码
        if (res.data.code === 401) {
          // Token过期或无效
          handleTokenExpired();
          reject(new Error('认证失败'));
          return;
        }
        
        if (res.data.code !== 0) {
          ErrorHandler.showError(res.data.message || '操作失败');
          reject(new Error(res.data.message || '操作失败'));
          return;
        }
        
        // 请求成功
        resolve(res.data);
      },
      fail: (err) => {
        if (showLoading) {
          wx.hideLoading();
        }
        
        console.error('请求失败', err);
        ErrorHandler.handle(err);
        reject(err);
      }
    });
  });
}

/**
 * GET请求
 */
function get(url, data = {}, needAuth = false) {
  return request({
    url,
    method: 'GET',
    data,
    needAuth
  });
}

/**
 * POST请求
 */
function post(url, data = {}, needAuth = false) {
  return request({
    url,
    method: 'POST',
    data,
    needAuth
  });
}

module.exports = {
  request,
  get,
  post,
  getToken,
  API_BASE_URL,
  ErrorHandler
};
