Page({
  data: {
    mistakeList: [], // 错题列表
    statistics: {
      totalCount: 0,
      byType: {},
      byMonth: {}
    }, // 错题统计信息
    monthKeys: [], // 月份键数组
    showFilterModal: false, // 显示筛选弹窗
    filterMonth: null, // 筛选月份
    filterType: null, // 筛选题型
    typeLabels: {
      1: '单选题',
      2: '多选题',
      3: '判断题'
    },
    // 分页相关
    page: 1,
    pageSize: 20,
    hasMore: true,
    loading: false
  },

  onLoad: function() {
    this.loadStatistics()
    this.loadMistakes()
  },
  
  onShow: function() {
    // 页面显示时刷新数据
    this.loadStatistics()
    this.loadMistakes()
  },
  
  // 加载错题统计
  loadStatistics: function() {
    const app = getApp()
    if (!app.globalData.hasLogin || !app.globalData.userInfo) {
      return
    }
    
    const that = this
    const request = require('../../utils/request.js')
    
    request.get('/api/mistake/statistics', {}, true).then(res => {
      console.log('错题统计数据:', res.data)
      
      // 计算月份键数组，用于 wx:for
      const monthKeys = res.data.byMonth ? Object.keys(res.data.byMonth) : []
      
      that.setData({
        statistics: res.data,
        monthKeys: monthKeys
      })
    }).catch(err => {
      console.error('获取错题统计失败:', err)
    })
  },
  
  // 加载错题列表
  loadMistakes: function(isRefresh = true) {
    // 检查用户是否已登录
    const app = getApp()
    if (!app.globalData.hasLogin || !app.globalData.userInfo) {
      console.log('用户未登录，无法加载错题列表')
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }
    
    // 如果正在加载，则不重复加载
    if (this.data.loading) {
      return
    }
    
    // 如果是刷新，重置分页
    if (isRefresh) {
      this.setData({
        page: 1,
        mistakeList: [],
        hasMore: true
      })
    }
    
    // 如果没有更多数据，则不加载
    if (!this.data.hasMore && !isRefresh) {
      return
    }
    
    this.setData({ loading: true })
    
    const userId = app.globalData.userInfo.userId
    console.log('开始加载用户错题列表，用户ID:', userId, '页码:', this.data.page)
    
    const that = this
    const request = require('../../utils/request.js')
    
    // 构建请求参数
    const params = {
      page: this.data.page,
      size: this.data.pageSize
    }
    if (this.data.filterMonth) {
      params.month = this.data.filterMonth
    }
    if (this.data.filterType) {
      params.type = this.data.filterType
    }
    
    // 从后端获取错题列表
    request.get('/api/mistake/list', params, true).then(res => {
      console.log('错题列表请求成功:', res)
      const newList = res.data.list || []
      const total = res.data.total || 0
      
      that.setData({
        mistakeList: isRefresh ? newList : [...that.data.mistakeList, ...newList],
        hasMore: that.data.mistakeList.length + newList.length < total,
        page: that.data.page + 1,
        loading: false
      })
      console.log('错题列表更新完成，当前' + that.data.mistakeList.length + '题，共' + total + '题')
    }).catch(err => {
      console.error('错题列表请求失败:', err)
      that.setData({ loading: false })
      wx.showToast({
        title: '网络请求失败',
        icon: 'none'
      })
    })
  },
  
  // 页面滚动到底部
  onReachBottom: function() {
    console.log('触发上拉加载')
    this.loadMistakes(false)
  },
  
  // 题目选择事件
  onTopicSelect: function(e) {
    console.log('选择了答案:', e.detail)
  },
  
  // 题目收藏事件
  onTopicFavorite: function(e) {
    console.log('收藏状态变化:', e.detail)
    // 在这里可以更新收藏状态，但不需要刷新错题列表
  },
  
  // 从错题本移除题目事件(刷新页面)处理
  onRemoveMistake: function(e) {
    console.log('=== onRemoveMistake 被调用 ===')
    console.log('事件详情:', e.detail)
    
    const { topicId } = e.detail
    console.log('要删除的题目ID:', topicId)
    console.log('当前错题列表:', this.data.mistakeList)
    
    const app = getApp()
    
    // 调用全局方法移除错题（会向后端发送请求）
    app.removeMistake(topicId)
    
    // 从当前列表中移除题目
    const newList = this.data.mistakeList.filter(item => {
      console.log('比较:', item.id, '!==', topicId, '结果:', item.id !== topicId)
      return item.id !== topicId
    })
    console.log("新的错题列表:",newList)
    console.log("原列表长度:", this.data.mistakeList.length, "新列表长度:", newList.length)
    
    this.setData({
      mistakeList: newList
    })
    
    // 刷新统计信息
    this.loadStatistics()
    
    wx.showToast({
      title: '已删除错题',
      icon: 'success'
    })
  },
  
  // 题目答对事件 - 提示是否移除
  onTopicCorrect: function(e) {
    const { topicId } = e.detail
    const that = this
    
    wx.showModal({
      title: '答对了',
      content: '恭喜答对！是否将此题从错题本中移除？',
      confirmText: '移除',
      cancelText: '保留',
      success: function(res) {
        if (res.confirm) {
          // 用户选择移除
          const app = getApp()
          app.removeMistake(topicId)
          
          // 从列表中移除
          const newList = that.data.mistakeList.filter(item => item.id !== topicId)
          that.setData({
            mistakeList: newList
          })
          
          // 刷新统计信息
          that.loadStatistics()
          
          wx.showToast({
            title: '已移除错题',
            icon: 'success'
          })
        }
      }
    })
  },
  
  // 下一题事件
  onNextTopic: function(e) {
    const currentIndex = e.currentTarget.dataset.index
    const nextSelector = `.mistake-item:nth-child(${currentIndex + 2})`
    
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
  

  // 导航到首页
  navigateToIndex: function() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  },
  
  // 显示筛选弹窗
  showFilter: function() {
    this.setData({
      showFilterModal: true
    })
  },
  
  // 取消筛选
  cancelFilter: function() {
    this.setData({
      showFilterModal: false
    })
  },
  
  // 选择筛选月份
  selectFilterMonth: function(e) {
    const month = e.currentTarget.dataset.month
    this.setData({
      filterMonth: this.data.filterMonth === month ? null : month
    })
  },
  
  // 选择筛选题型
  selectFilterType: function(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      filterType: this.data.filterType === type ? null : type
    })
  },
  
  // 应用筛选
  applyFilter: function() {
    this.setData({
      showFilterModal: false
    })
    this.loadMistakes()
  },
  
  // 重置筛选
  resetFilter: function() {
    this.setData({
      filterMonth: null,
      filterType: null,
      showFilterModal: false
    })
    this.loadMistakes()
  }
})