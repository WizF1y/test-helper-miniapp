const { get, post, ErrorHandler } = require('../../utils/request.js');

Page({
  data: {
    favoriteList: [], // 收藏列表
    showClearModal: false, // 显示清空确认弹窗
    // 分页相关
    page: 1,
    pageSize: 20,
    hasMore: true,
    loading: false
  },

  onLoad: function() {
    this.loadFavorites()
  },
  
  onShow: function() {
    // 页面显示时刷新数据
    this.loadFavorites()
  },
  
  // 加载收藏列表
  async loadFavorites(isRefresh = true) {
    // 检查用户是否已登录
    if (!ErrorHandler.checkLogin()) {
      return;
    }
    
    // 如果正在加载，则不重复加载
    if (this.data.loading) {
      return;
    }
    
    // 如果是刷新，重置分页
    if (isRefresh) {
      this.setData({
        page: 1,
        favoriteList: [],
        hasMore: true
      });
    }
    
    // 如果没有更多数据，则不加载
    if (!this.data.hasMore && !isRefresh) {
      return;
    }
    
    this.setData({ loading: true });
    
    try {
      const result = await get('/api/favorite/list', {
        page: this.data.page,
        size: this.data.pageSize
      }, true);
      
      const newList = result.data.list || [];
      const total = result.data.total || 0;
      
      this.setData({
        favoriteList: isRefresh ? newList : [...this.data.favoriteList, ...newList],
        hasMore: this.data.favoriteList.length + newList.length < total,
        page: this.data.page + 1,
        loading: false
      });
      
      console.log('收藏列表加载成功，当前' + this.data.favoriteList.length + '题，共' + total + '题');
      
    } catch (error) {
      this.setData({ loading: false });
      console.error('加载收藏列表失败:', error);
    }
  },
  
  // 页面滚动到底部
  onReachBottom: function() {
    console.log('触发上拉加载');
    this.loadFavorites(false);
  },
  
  // 题目选择事件
  onTopicSelect: function(e) {
    console.log('选择了答案:', e.detail)
  },
  
  // 题目收藏事件
  onTopicFavorite: function(e) {
    console.log('=== onTopicFavorite 被调用 ===')
    console.log('事件详情:', e.detail)
    
    const { topicId, isFavorite } = e.detail
    const app = getApp()
    
    // 在收藏列表中，只会有取消收藏的操作
    // isFavorite 为 false 表示取消收藏
    if (!isFavorite) {
      // 调用后端 API 取消收藏
      const request = require('../../utils/request.js')
      request.post('/api/favorite/delete', {
        topicId: topicId
      }, true).then(res => {
        console.log('取消收藏成功:', res)
        
        // 从当前列表中移除题目
        const newList = this.data.favoriteList.filter(item => item.id !== topicId)
        console.log('过滤后的列表:', newList)
        
        this.setData({
          favoriteList: newList
        })
        
        wx.showToast({
          title: '已取消收藏',
          icon: 'success'
        })
      }).catch(err => {
        console.error('取消收藏失败:', err)
        wx.showToast({
          title: '操作失败',
          icon: 'none'
        })
      })
    }
  },

  // 从收藏列表移除题目事件(刷新页面)处理
  onRemoveFavorite: function(e) {
    const { topicId } = e.detail
    const app = getApp()
    
    // 调用全局方法移除收藏（会向后端发送请求）
    app.removeFavorite(topicId)
    
    // 从当前列表中移除题目
    const newList = this.data.favoriteList.filter(item => item.id !== topicId)
    console.log("新的收藏列表:",newList)
    this.setData({
      favoriteList: newList
    })
    
    wx.showToast({
      title: '已取消收藏',
      icon: 'success'
    })
  },
  
  // 下一题事件
  onNextTopic: function(e) {
    const currentIndex = e.currentTarget.dataset.index
    const nextSelector = `.favorite-item:nth-child(${currentIndex + 2})`
    
    wx.createSelectorQuery()
      .select(nextSelector)
      .boundingClientRect(rect => {
        if (rect) {
          const windowInfo = wx.getWindowInfo()
          wx.pageScrollTo({
            scrollTop: rect.top + windowInfo.windowScrollTop - 20,
            duration: 300
          })
        }
      })
      .exec()
  },
  
  // 显示清空确认弹窗
  showClearConfirm: function() {
    this.setData({
      showClearModal: true
    })
  },
  
  // 取消清空
  cancelClear: function() {
    this.setData({
      showClearModal: false
    })
  },
  
  // 确认清空
  async confirmClear() {
    // 检查登录状态
    if (!ErrorHandler.checkLogin()) {
      return;
    }
    
    try {
      await post('/api/favorite/clear', {}, true);
      
      this.setData({
        favoriteList: [],
        showClearModal: false
      });
      
      ErrorHandler.showSuccess('已清空收藏');
      
      // 更新个人中心的统计数据
      const profilePage = getCurrentPages().find(page => page.route === 'pages/profile/profile');
      if (profilePage && typeof profilePage.loadStatistics === 'function') {
        profilePage.loadStatistics();
      }
      
    } catch (error) {
      // 错误已自动处理
      console.error('清空收藏失败:', error);
    }
  },
  
  // 导航到首页
  navigateToIndex: function() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  }
}) 