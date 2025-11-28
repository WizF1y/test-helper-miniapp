/**
 * 统一错误处理工具
 * 处理所有API请求错误和异常情况
 */

class ErrorHandler {
  /**
   * 处理错误并显示提示
   * @param {Object} error - 错误对象
   * @param {Boolean} showToast - 是否显示提示
   * @returns {String} 错误消息
   */
  static handle(error, showToast = true) {
    console.error('Error:', error);
    
    let message = '操作失败，请重试';
    let needLogin = false;
    
    // 处理不同类型的错误
    if (error.statusCode === 401) {
      message = '登录已过期，请重新登录';
      needLogin = true;
    } else if (error.statusCode === 403) {
      message = '没有权限访问';
    } else if (error.statusCode === 404) {
      message = '请求的资源不存在';
    } else if (error.statusCode >= 500) {
      message = '服务器错误，请稍后重试';
    } else if (error.data && error.data.message) {
      message = error.data.message;
    } else if (error.errMsg) {
      // 处理微信API错误
      if (error.errMsg.includes('request:fail')) {
        message = '网络连接失败，请检查网络设置';
      } else if (error.errMsg.includes('timeout')) {
        message = '请求超时，请重试';
      } else {
        message = error.errMsg;
      }
    }
    
    if (showToast) {
      wx.showToast({
        title: message,
        icon: 'none',
        duration: 2000
      });
    }
    
    // 如果需要登录，跳转到首页
    if (needLogin) {
      setTimeout(() => {
        wx.reLaunch({
          url: '/pages/index/index'
        });
      }, 2000);
    }
    
    return message;
  }
  
  /**
   * 封装wx.request，添加统一错误处理和加载动画
   * @param {Object} options - 请求配置
   * @returns {Promise} 请求Promise
   */
  static async request(options) {
    const {
      url,
      method = 'GET',
      data = {},
      header = {},
      showLoading = true,
      loadingText = '加载中...'
    } = options;
    
    // 显示加载动画
    if (showLoading) {
      wx.showLoading({ 
        title: loadingText,
        mask: true
      });
    }
    
    try {
      // 获取token
      const token = wx.getStorageSync('token');
      if (token) {
        header['Authorization'] = `Bearer ${token}`;
      }
      
      // 发起请求
      const res = await new Promise((resolve, reject) => {
        wx.request({
          url,
          method,
          data,
          header: {
            'content-type': 'application/json',
            ...header
          },
          success: resolve,
          fail: reject
        });
      });
      
      // 隐藏加载动画
      if (showLoading) {
        wx.hideLoading();
      }
      
      // 检查响应状态
      if (res.statusCode !== 200) {
        throw {
          statusCode: res.statusCode,
          data: res.data
        };
      }
      
      // 检查业务状态码
      if (res.data.code !== 0) {
        throw {
          statusCode: res.statusCode,
          data: res.data
        };
      }
      
      return res.data;
      
    } catch (error) {
      // 隐藏加载动画
      if (showLoading) {
        wx.hideLoading();
      }
      
      // 处理错误
      this.handle(error);
      throw error;
    }
  }
  
  /**
   * 检查用户登录状态
   * @param {Boolean} showTip - 是否显示提示
   * @returns {Boolean} 是否已登录
   */
  static checkLogin(showTip = true) {
    // 使用大写的 KEY 名称，与其他地方保持一致
    const token = wx.getStorageSync('TOKEN');
    const userInfo = wx.getStorageSync('USER_INFO');
    
    if (!token || !userInfo) {
      if (showTip) {
        wx.showModal({
          title: '提示',
          content: '请先登录后再使用此功能',
          confirmText: '去登录',
          success: (res) => {
            if (res.confirm) {
              wx.reLaunch({
                url: '/pages/index/index'
              });
            }
          }
        });
      }
      return false;
    }
    
    return true;
  }
  
  /**
   * 显示成功提示
   * @param {String} message - 提示消息
   */
  static showSuccess(message) {
    wx.showToast({
      title: message,
      icon: 'success',
      duration: 2000
    });
  }
  
  /**
   * 显示错误提示
   * @param {String} message - 错误消息
   */
  static showError(message) {
    wx.showToast({
      title: message,
      icon: 'none',
      duration: 2000
    });
  }
}

module.exports = ErrorHandler;
