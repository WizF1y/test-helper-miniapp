Page({
  data: {
    bannerList: [],
    monthlyTopics: [],
    modeTypes: [],
    regionTopics: [],
    showBackTop: false,
    pageNum: 1,
    pageSize: 10,
    hasLogin: false
  },

  onLoad: function() {
    this.checkLoginStatus();
    this.loadBanners()
    this.loadMonthlyTopics()
    // this.loadModeTypes()
    this.loadRegionTopics()
  },

  onShow: function() {
    // 每次页面显示时检查登录状态
    this.checkLoginStatus();
    
    // 如果已登录，加载统计数据
    if (this.data.hasLogin) {
      this.loadMonthlyTopics();
    }
  },

  // 检查登录状态
  checkLoginStatus: function() {
    const app = getApp();
    this.setData({
      hasLogin: app.globalData.hasLogin
    });
    
    // 如果已经登录，可以执行其他初始化操作
    if (app.globalData.hasLogin) {
      // 可以在这里添加登录后需要执行的操作
    }
  },

  // 登录按钮点击事件
  onLogin: function() {
    // 使用微信登录
    this.userLogin();
  },

  // 获取用户信息
  // getUserProfile: function() {
  //   // 使用微信登录替代getUserProfile
  //   // this.userLogin();
  // },

  // 用户登录
  userLogin: function() {
    const that = this;
    
    // 使用微信登录
    wx.login({
      success: function(loginRes) {
        if (loginRes.code) {
          // 调用后端登录接口
          wx.request({
            url: 'http://localhost:8000/api/login',
            method: 'POST',
            data: {
              code: loginRes.code
            },
            success: function(res) {
              if (res.data.code === 0) {
                // 登录成功，保存用户信息和token到本地
                const userInfo = {
                  userId: res.data.data.userId,
                  nickname: res.data.data.nickname || '用户' + res.data.data.userId,
                  avatarUrl: res.data.data.avatarUrl || ''
                };
                const token = res.data.data.token;
                
                // 保存到本地存储
                wx.setStorageSync('USER_INFO', userInfo);
                wx.setStorageSync('TOKEN', token);
                
                // 更新全局数据
                const app = getApp();
                app.globalData.userInfo = userInfo;
                app.globalData.token = token;
                app.globalData.hasLogin = true;
                
                // 登录成功更新页面状态
                that.setData({
                  hasLogin: true,
                  userInfo: userInfo
                });
                
                wx.showToast({
                  title: '登录成功',
                  icon: 'success'
                });
                
                // 跳转到首页
                wx.switchTab({
                  url: '/pages/index/index'
                });
              } else {
                console.error('后端登录失败:', res);
                wx.showToast({
                  title: res.data.message || '登录失败',
                  icon: 'none'
                });
              }
            },
            fail: function(err) {
              console.error('登录请求失败:', err);
              wx.showToast({
                title: '登录失败',
                icon: 'none'
              });
            }
          });
        } else {
          console.error('登录失败！' + loginRes.errMsg);
          wx.showToast({
            title: '登录失败',
            icon: 'none'
          });
        }
      },
      fail: function(err) {
        console.error('微信登录失败:', err);
        wx.showToast({
          title: '微信登录失败',
          icon: 'none'
        });
      }
    });
  },

  onPageScroll: function(e) {
    // 控制返回顶部按钮显示
    this.setData({
      showBackTop: e.scrollTop > 300
    })
  },

  // 下拉刷新
  onPullDownRefresh: function() {
    // 检查登录状态
    this.checkLoginStatus();
    
    // 重置页码
    this.setData({
      pageNum: 1
    })

    // 重新加载数据
    Promise.all([
      this.loadBanners(),
      this.loadMonthlyTopics(),
      this.loadRegionTopics()
    ]).then(() => {
      // 停止下拉刷新动画
      wx.stopPullDownRefresh()
    }).catch(err => {
      console.error('刷新数据失败', err)
      wx.stopPullDownRefresh()
    })
  },

  // 加载轮播图数据
  loadBanners: function() {
    // 模拟API请求
    return new Promise((resolve) => {
      setTimeout(() => {
        this.setData({
          bannerList: [
            { id: 1, imageUrl: 'https://picsum.photos/750/320?random=1' },
            { id: 2, imageUrl: 'https://picsum.photos/750/320?random=2' },
            { id: 3, imageUrl: 'https://picsum.photos/750/320?random=3' }
          ]
        })
        resolve()
      }, 500)
    })
  },

  // 加载月份题目数据和学习模式
  loadMonthlyTopics: function() {
    const that = this;
    const request = require('../../utils/request.js');
    
    // 显示加载中
    wx.showLoading({
      title: '加载中',
    });
    
    const currentMonth = new Date().getMonth() + 1;
    const monthsArray = [];

    for (let i = 0; i < 6; i++) {
      const month = currentMonth - i > 0 ? currentMonth - i : 12 + (currentMonth - i);
      monthsArray.push(month);
    }
    
    const monthsParam = monthsArray.join(',');
    
    // 同时请求总题数和已完成题数
    Promise.all([
      // 获取每月总题数
      request.get('/api/topics/count-by-month', {
        months: monthsParam
      }, false),
      // 获取用户每月完成题数（需要登录）
      request.get('/api/user/month-progress', {
        months: monthsParam
      }, true).catch(() => ({ data: [] })) // 如果未登录，返回空数据
    ]).then(([totalRes, progressRes]) => {
      const monthlyData = [];
      
      // 遍历月份，构建数据
      for (let i = 0; i < 6; i++) {
        const month = currentMonth - i > 0 ? currentMonth - i : 12 + (currentMonth - i);
        
        // 查找该月的总题数
        const totalItem = totalRes.data.find(item => item.month === month) || { count: 0 };
        const totalCount = totalItem.count;
        
        // 查找该月的已完成题数
        const progressItem = progressRes.data.find(item => item.month === month) || { completedCount: 0 };
        const completedCount = progressItem.completedCount;
        
        // 计算未完成题数
        const uncompletedCount = totalCount - completedCount;
        
        monthlyData.push({
          month: month,
          totalCount: totalCount,
          completedCount: completedCount,
          uncompletedCount: uncompletedCount,
          isNew: i === 0 // 最新月份标记为新
        });
      }
      
      that.setData({
        monthlyTopics: monthlyData
      });
      
      wx.hideLoading();
    }).catch(err => {
      console.error('加载月度数据失败:', err);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      
      // 使用模拟数据作为备用
      that.setFallbackMonthlyData();
      wx.hideLoading();
    });
  },

  // 设置备用月度数据（当请求失败时使用）
  setFallbackMonthlyData: function() {
    const currentMonth = new Date().getMonth() + 1;
    
    // 生成最近6个月的数据
    const monthlyData = [];
    for (let i = 0; i < 6; i++) {
      const month = currentMonth - i > 0 ? currentMonth - i : 12 + (currentMonth - i);
      monthlyData.push({
        month,
        count: Math.floor(Math.random() * 100) + 50, // 仅作为备用的随机数
        isNew: i === 0 // 最新月份标记为新
      });
    }
    
    this.setData({
      monthlyTopics: monthlyData
    });
  },

  // 加载地区题目数据
  loadRegionTopics: function() {
    // 模拟API请求
    return new Promise((resolve) => {
      setTimeout(() => {
        this.setData({
          regionTopics: [
            { region: '北京', count: 128, imageUrl: 'https://picsum.photos/120/80?random=10' },
            { region: '上海', count: 105, imageUrl: 'https://picsum.photos/120/80?random=11' },
            { region: '广东', count: 97, imageUrl: 'https://picsum.photos/120/80?random=12' },
            { region: '江苏', count: 86, imageUrl: 'https://picsum.photos/120/80?random=13' },
            { region: '浙江', count: 78, imageUrl: 'https://picsum.photos/120/80?random=14' },
            { region: '山东', count: 92, imageUrl: 'https://picsum.photos/120/80?random=15' }
          ]
        })
        resolve()
      }, 700)
    })
  },
  
  // 轮播图点击
  onBannerTap: function(e) {
    const id = e.currentTarget.dataset.id
    console.log('点击了轮播图:', id)
    // 可以跳转到相应的页面
  },

// 跳转到随机练习设置页面
  navigateToRandomPractice: function() {
    // 检查登录状态
    if (!this.data.hasLogin) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: '/pages/random-settings/random-settings'
    })
  },

  // 跳转到错题记录
  navigateToMistakes: function() {
    // 检查登录状态
    if (!this.data.hasLogin) {
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

  // 跳转到收藏夹
  navigateToFavorites: function() {
    // 检查登录状态
    if (!this.data.hasLogin) {
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

  // 跳转到关于我们
  navigateToAbout: function() {
    wx.navigateTo({
      url: '/pages/about/about'
    })
  },

  // 跳转到题目列表
  navigateToTopicList: function(e) {
    // 检查登录状态
    if (!this.data.hasLogin) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      return;
    }
    
    const { type, value } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/topic-list/topic-list?type=${type}&value=${value}`
    })
  },

  // 返回顶部
  scrollToTop: function() {
    wx.pageScrollTo({
      scrollTop: 0,
      duration: 300
    })
  }
})