App({
  globalData: {
    hasLogin: false,
    userInfo: null,
    token: null,
    baseUrl: 'http://localhost:5000/api',
    storageKeys: {
      mistakes: 'MISTAKE_LIST',
      favorites: 'FAVORITE_LIST',
      records: 'EXAM_RECORDS'
    }
  },

  onLaunch: function() {
    // 初始化小程序
    this.checkLogin()
    
    // 获取系统信息，适配手机型号
    this.getSystemInfo()
  },
  
  onShow: function() {
    // 每次小程序启动或从后台进入前台时检查登录状态
    this.checkLoginStatusAndRedirect()
  },
  
  // 检查登录状态
  checkLogin: function() {
    try {
      const userInfo = wx.getStorageSync('USER_INFO')
      const token = wx.getStorageSync('TOKEN')
      
      if (userInfo && token) {
        this.globalData.hasLogin = true
        this.globalData.userInfo = userInfo
        this.globalData.token = token
      } else {
        this.globalData.hasLogin = false
        this.globalData.userInfo = null
        this.globalData.token = null
      }
    } catch (e) {
      console.error('检查登录状态失败', e)
    }
  },
  
  // 登录方法
  login: function(userInfo) {
    return new Promise((resolve, reject) => {
      // 模拟登录接口请求
      setTimeout(() => {
        try {
          // 保存用户信息
          wx.setStorageSync('USER_INFO', userInfo)
          
          this.globalData.hasLogin = true
          this.globalData.userInfo = userInfo
          
          // 登录成功后检查是否需要跳转到首页
          this.checkLoginStatusAndRedirect()
          
          resolve(userInfo)
        } catch (e) {
          console.error('登录失败', e)
          reject(e)
        }
      }, 1000)
    })
  },
  
  // 退出登录
  logout: function() {
    try {
      wx.removeStorageSync('USER_INFO')
      wx.removeStorageSync('TOKEN')
      this.globalData.hasLogin = false
      this.globalData.userInfo = null
      this.globalData.token = null
      
      // 退出登录后跳转到登录页
      wx.redirectTo({
        url: '/pages/index/index'
      })
      
      return true
    } catch (e) {
      console.error('退出登录失败', e)
      return false
    }
  },
  
  // 添加错题
  addMistake: function(topic) {
    if (!this.globalData.hasLogin || !this.globalData.userInfo) {
      console.log('用户未登录，无法添加错题')
      return false
    }
    
    console.log('添加错题，题目ID:', topic.id)
    
    // 使用封装的请求工具调用后端接口
    const request = require('./utils/request.js')
    request.post('/api/mistake/add', {
      topicId: topic.id
    }, true).then(res => {
      console.log('错题添加成功:', res)
    }).catch(err => {
      console.error('添加错题失败:', err)
    })
    
    return true
  },
  
  // 检查登录状态并根据需要重定向
  checkLoginStatusAndRedirect: function() {
    // 检查当前页面是否需要登录
    const pages = getCurrentPages()
    if (pages && pages.length > 0) {
      const currentPage = pages[pages.length - 1]
      if (currentPage) {
        const route = currentPage.route
        // 如果不是首页且用户未登录，则跳转到首页
        if (route !== 'pages/index/index' && !this.globalData.hasLogin) {
          wx.redirectTo({
            url: '/pages/index/index'
          })
        }
      }
    }
  },
  
  // 获取系统信息
  getSystemInfo: function() {
    try {
      // 使用新的API替代getSystemInfoSync
      const systemInfo = wx.getDeviceInfo()
      const windowInfo = wx.getWindowInfo()
      
      // 合并设备信息和窗口信息
      const fullSystemInfo = {
        ...systemInfo,
        ...windowInfo
      }
      
      this.globalData.systemInfo = fullSystemInfo
      
      // 判断是否是iPhone X以上的机型
      const isIPhoneX = fullSystemInfo.model.includes('iPhone X') || 
                        fullSystemInfo.model.includes('iPhone 11') || 
                        fullSystemInfo.model.includes('iPhone 12') || 
                        fullSystemInfo.model.includes('iPhone 13') || 
                        fullSystemInfo.model.includes('iPhone 14')
                        
      this.globalData.isIPhoneX = isIPhoneX
    } catch (e) {
      console.error('获取系统信息失败', e)
    }
  },
  
  // 移除错题
  removeMistake: function(topicId) {
    if (!this.globalData.hasLogin || !this.globalData.userInfo) {
      console.log('用户未登录，无法移除错题')
      return false
    }
    
    console.log('=== app.removeMistake 被调用 ===')
    console.log('题目ID:', topicId)
    console.log('题目ID类型:', typeof topicId)
    
    try {
      // 更新本地存储
      const key = this.globalData.storageKeys.mistakes
      let mistakes = wx.getStorageSync(key) || []
      
      const newMistakes = mistakes.filter(item => item.id !== topicId)
      wx.setStorageSync(key, newMistakes)
      console.log('本地存储已更新')
      
      // 使用封装的请求工具调用后端接口
      const request = require('./utils/request.js')
      console.log('准备调用后端 API，参数:', { topicId: topicId })
      
      request.post('/api/mistake/delete', {
        topicId: topicId
      }, true).then(res => {
        console.log('后端删除错题成功:', res)
        // 更新统计信息
        this.updateStatistics()
      }).catch(err => {
        console.error('后端删除错题失败:', err)
        console.error('错误详情:', JSON.stringify(err))
      })
    } catch (e) {
      console.error('移除错题失败', e)
      return false
    }
    
    return true
  },
  
  // 切换收藏状态
  toggleFavorite: function(topic) {
    // 检查用户是否已登录
    if (!this.globalData.hasLogin || !this.globalData.userInfo) {
      console.log('用户未登录，无法切换收藏状态')
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return false
    }
    
    const isFavorite = topic.isFavorite
    const topicId = topic.id
    console.log('切换收藏状态，题目ID:', topicId, '当前状态:', isFavorite)
    
    // 根据当前状态决定调用添加还是删除接口
    const url = isFavorite ? '/api/favorite/delete' : '/api/favorite/add'
    
    // 使用封装的请求工具调用后端接口
    const request = require('./utils/request.js')
    request.post(url, {
      topicId: topicId
    }, true).then(res => {
      console.log('收藏状态切换成功:', res)
      // 更新统计信息
      this.updateStatistics()
    }).catch(err => {
      console.error('切换收藏状态失败:', err)
    })
    
    return true
  },
  
  // 移除收藏
  removeFavorite: function(topicId) {
    if (!this.globalData.hasLogin || !this.globalData.userInfo) {
      console.log('用户未登录，无法移除收藏')
      return false
    }
    
    console.log('=== app.removeFavorite 被调用 ===')
    console.log('题目ID:', topicId)
    
    // 使用封装的请求工具调用后端接口
    const request = require('./utils/request.js')
    request.post('/api/favorite/delete', {
      topicId: topicId
    }, true).then(res => {
      console.log('移除收藏成功:', res)
      // 更新统计信息
      this.updateStatistics()
    }).catch(err => {
      console.error('移除收藏失败:', err)
    })
    
    return true
  },
  
  
  // 更新用户统计数据
  updateStatistics: function() {
    // 获取当前页面栈
    const pages = getCurrentPages();
    // 查找profile页面
    const profilePage = pages.find(page => page.route === 'pages/profile/profile');
    if (profilePage && typeof profilePage.loadStatistics === 'function') {
      profilePage.loadStatistics();
    }
  }
})