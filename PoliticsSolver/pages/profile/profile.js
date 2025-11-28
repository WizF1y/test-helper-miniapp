Page({
  data: {
    hasUserInfo: false,
    userInfo: null,
    userId: null,
    statistics: {
      doneCount: 0,
      mistakeCount: 0,
      favoriteCount: 0,
      daysCount: 0
    },
    showDonationModal: false,
    selectedDonation: 10,
    showLoginBtn: false
  },

  onLoad: function() {
    // 检查是否已有用户信息
    this.checkUserInfo()
  },
  
  onShow: function() {
    // 每次页面显示时检查用户信息，确保登录状态同步
    // checkUserInfo 内部会调用 loadStatistics，所以不需要重复调用
    this.checkUserInfo()
  },

  // 检查用户信息
  checkUserInfo: function() {
    try {
      const app = getApp()
      const userInfo = wx.getStorageSync('USER_INFO')
      const token = wx.getStorageSync('TOKEN')
      
      if (userInfo && token) {
        // 确保全局数据已更新
        app.globalData.userInfo = userInfo
        app.globalData.token = token
        app.globalData.hasLogin = true
        
        this.setData({
          hasUserInfo: true,
          userInfo: userInfo,
          userId: userInfo.userId
        })
        
        // 加载统计数据
        this.loadStatistics()
      } else {
        // 如果没有用户信息或token，确保状态为未登录
        app.globalData.hasLogin = false
        app.globalData.userInfo = null
        app.globalData.token = null
        
        this.setData({
          hasUserInfo: false,
          userInfo: null,
          userId: null
        })
      }
    } catch (e) {
      console.error('获取用户信息失败:', e)
    }
  },
  
  // 获取用户信息
  onGetUserInfo: function(e) {
    if (e.detail.userInfo) {
      this.handleUserInfo(e.detail);
      // 隐藏登录按钮
      this.setData({
        showLoginBtn: false
      });
    } else {
      wx.showToast({
        title: '您取消了授权',
        icon: 'none'
      });
    }
  },
  
  // 加载统计数据
  loadStatistics: function() {
    const app = getApp()
    if (!app.globalData.hasLogin || !app.globalData.userInfo) {
      return
    }
    
    const that = this
    const request = require('../../utils/request.js')
    
    request.get('/api/user/statistics', {}, true).then(res => {
      console.log('统计数据请求成功:', res);
      if (res.code === 0) {
        console.log('统计数据:', res.data);
        that.setData({
          'statistics.mistakeCount': res.data.mistakeCount || 0,
          'statistics.favoriteCount': res.data.favoriteCount || 0,
          'statistics.doneCount': res.data.doneCount || 0,
          'statistics.daysCount': res.data.daysCount || 0
        })
      } else {
        console.error('获取统计数据失败:', res.message)
      }
    }).catch(err => {
      console.error('统计数据请求失败:', err)
    })
  },
  
  // 导航到错题记录
  navigateToMistakes: function() {
    // 检查登录状态
    if (!this.data.hasUserInfo) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: '/pages/mistake-record/mistake-record'
    })
  },
  
  // 导航到收藏夹
  navigateToFavorites: function() {
    // 检查登录状态
    if (!this.data.hasUserInfo) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: '/pages/collection/collection'
    })
  },
  
  // 导航到关于我们
  navigateToAbout: function() {
    wx.navigateTo({
      url: '/pages/about/about'
    })
  },
  
  // 显示打赏弹窗
  showDonation: function() {
    this.setData({
      showDonationModal: true
    })
  },
  
  // 关闭打赏弹窗
  closeDonation: function() {
    this.setData({
      showDonationModal: false
    })
  },
  
  // 选择打赏金额
  selectDonation: function(e) {
    const amount = parseInt(e.currentTarget.dataset.amount)
    this.setData({
      selectedDonation: amount
    })
  },
  
  // 确认打赏
  confirmDonation: function() {
    const amount = this.data.selectedDonation
    const that = this
    const request = require('../../utils/request.js')
    
    // 请求服务器获取支付参数
    request.post('/api/payment/create', {
      amount: amount
    }, true).then(res => {
      if (res.code === 0) {
        // 使用服务器返回的参数调用支付接口
        const payParams = res.data
        
        wx.requestPayment({
          timeStamp: payParams.timeStamp,
          nonceStr: payParams.nonceStr,
          package: payParams.package,
          signType: payParams.signType,
          paySign: payParams.paySign,
          success: function() {
            wx.showToast({
              title: '感谢您的支持！',
              icon: 'success'
            })
            that.closeDonation()
          },
          fail: function(err) {
            console.error('支付失败:', err)
            wx.showToast({
              title: '支付失败，请重试',
              icon: 'none'
            })
          }
        })
      } else {
        wx.showToast({
          title: res.message || '创建支付失败',
          icon: 'none'
        })
      }
    }).catch(err => {
      console.error('请求支付参数失败:', err)
      wx.showToast({
        title: '网络请求失败',
        icon: 'none'
      })
    })
  },
  
  // 退出登录
  logout: function() {
    try {
      wx.removeStorageSync('USER_INFO')
      
      this.setData({
        hasUserInfo: false,
        userInfo: null,
        userId: null,
        'statistics.mistakeCount': 0,
        'statistics.favoriteCount': 0,
        'statistics.doneCount': 0,
        'statistics.daysCount': 0
      })
      
      wx.showToast({
        title: '已退出登录',
        icon: 'success'
      })
    } catch (e) {
      console.error('退出登录失败:', e)
      wx.showToast({
        title: '操作失败',
        icon: 'none'
      })
    }
  },

  // 触发登录操作
  triggerLogin: function() {
    const that = this;
    
    // 显示加载提示
    wx.showLoading({
      title: '准备登录...'
    });
    
    // 使用getUserProfile获取用户信息
    wx.getUserProfile({
      desc: '用于完善用户资料', // 声明获取用户个人信息后的用途
      success: (res) => {
        wx.hideLoading(); // 获取成功，隐藏加载提示
        that.handleUserInfo(res);
      },
      fail: (err) => {
        wx.hideLoading(); // 获取失败，隐藏加载提示
        console.error('获取用户信息失败:', err);
        
        // 如果getUserProfile失败，尝试使用button的开放能力
        wx.showToast({
          title: '请点击授权按钮',
          icon: 'none',
          duration: 2000
        });
        
        // 延迟显示登录按钮
        setTimeout(() => {
          that.setData({
            showLoginBtn: true
          });
        }, 500);
      }
    });
  },

  // 处理用户信息
  handleUserInfo: function(res) {
    if (!res.userInfo) {
      wx.showToast({
        title: '获取用户信息失败',
        icon: 'none'
      });
      return;
    }
    
    const that = this;
    
    // 显示加载提示
    wx.showLoading({
      title: '登录中...'
    });
    
    // 调用微信登录接口获取code
    const app = getApp()
    
    wx.login({
      success: function(loginRes) {
        if (loginRes.code) {
          // 将code和用户信息发送到服务器
          wx.request({
            url: app.globalData.baseUrl + '/login',
            method: 'POST',
            data: {
              code: loginRes.code,
              userInfo: res.userInfo
            },
            success: function(res) {
              if (res.data.code === 0) {
                // 登录成功，保存用户信息和token到本地
                const userInfo = {
                  userId: res.data.data.userId,
                  nickname: res.data.data.nickname,
                  avatarUrl: res.data.data.avatarUrl
                };
                const token = res.data.data.token;
                
                wx.setStorageSync('USER_INFO', userInfo);
                wx.setStorageSync('TOKEN', token);
                
                // 更新全局数据
                app.globalData.userInfo = userInfo;
                app.globalData.token = token;
                app.globalData.hasLogin = true;
                
                that.setData({
                  hasUserInfo: true,
                  userInfo: userInfo,
                  userId: userInfo.userId
                });
                
                // 登录成功后更新统计数据
                that.loadStatistics();
                
                wx.showToast({
                  title: '登录成功',
                  icon: 'success'
                });
              } else {
                wx.showToast({
                  title: res.data.message || '登录失败',
                  icon: 'none'
                });
              }
            },
            fail: function(err) {
              console.error('登录请求失败:', err);
              // 添加模拟登录，用于测试
              wx.showToast({
                title: '使用模拟登录',
                icon: 'none'
              });
              
              // 模拟登录数据
              const mockUserInfo = {
                userId: 999999,
                nickname: '测试用户',
                avatarUrl: ''
              };
              
              wx.setStorageSync('USER_INFO', mockUserInfo);
              
              that.setData({
                hasUserInfo: true,
                userInfo: mockUserInfo,
                userId: mockUserInfo.userId
              });
              
              // 登录成功后更新统计数据
              that.loadStatistics();
            },
            complete: function() {
              // 无论成功失败，都隐藏加载提示
              wx.hideLoading();
            }
          });
        } else {
          // 获取code失败时隐藏加载提示
          wx.hideLoading();
          wx.showToast({
            title: '获取微信登录凭证失败',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        // 登录失败时隐藏加载提示
        wx.hideLoading();
        console.error('微信登录失败:', err);
        wx.showToast({
          title: '微信登录失败',
          icon: 'none'
        });
      }
    });
  }
}) 