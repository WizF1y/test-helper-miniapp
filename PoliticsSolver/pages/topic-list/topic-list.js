Page({
  data: {
    type: '',     // 分类类型：month(月份) 或 region(地区)
    value: '',    // 对应的值（月份数字或地区名称）
    topicList: [], // 题目列表
    pageNum: 1,   // 当前页码
    pageSize: 10, // 每页数量
    hasMore: true, // 是否有更多数据
    showAllAnswers: false, // 是否显示所有答案
    userAnswers: {}, // 用户的答题记录 {题目索引: 选项}
    userId: null  // 用户ID
  },

  onLoad: function(options) {
    const { type, value } = options
    
    this.setData({
      type,
      value
    })
    
    wx.setNavigationBarTitle({
      title: type === 'month' ? `${value}月题库` : `${value}地区题库`
    })
    
    // 检查登录状态
    this.checkLoginStatus();
    
    this.loadTopics()
  },
  
  onShow: function() {
    // 页面显示时检查登录状态
    this.checkLoginStatus();
  },
  
  // 检查登录状态
  checkLoginStatus: function() {
    try {
      const userInfo = wx.getStorageSync('USER_INFO')
      if (userInfo && userInfo.userId) {
        this.setData({
          userId: userInfo.userId
        })
      } else {
        // 如果没有用户信息，尝试从全局获取
        const app = getApp();
        if (app.globalData.hasLogin && app.globalData.userInfo && app.globalData.userInfo.userId) {
          this.setData({
            userId: app.globalData.userInfo.userId
          })
        }
      }
    } catch (e) {
      console.error('获取用户信息失败', e)
    }
  },
  
  // 滚动到底部
  onReachBottom: function() {
    if (this.data.hasMore) {
      this.loadMoreTopics()
    }
  },
  
  // 初始加载题目
  loadTopics: function() {
    wx.showLoading({
      title: '加载中...'
    })
    
    // 后端API请求参数
    const params = {
      page: 1,
      size: this.data.pageSize
    }
    
    // 根据类型添加过滤条件
    if (this.data.type === 'month') {
      params.month = parseInt(this.data.value)
    } else if (this.data.type === 'region') {
      params.region = this.data.value
    }
    
    // 添加用户ID和排除已答题参数
    if (this.data.userId) {
      params.userId = this.data.userId
      params.excludeAnswered = true
    }
    
    const that = this
    const request = require('../../utils/request.js')
    
    // 发起后端请求（题目列表不需要认证）
    request.get('/api/topics', params, false).then(res => {
      const topics = res.data.list || []
      
      that.setData({
        topicList: topics,
        pageNum: 1,
        hasMore: topics.length >= that.data.pageSize
      })
    }).catch(err => {
      console.error('获取题目失败', err)
      wx.showToast({
        title: '获取题目失败',
        icon: 'none'
      })
    }).finally(() => {
      wx.hideLoading()
    })
  },
  
  // 加载更多题目
  loadMoreTopics: function() {
    if (!this.data.hasMore) return
    
    wx.showLoading({
      title: '加载更多...'
    })
    
    this.setData({
      pageNum: this.data.pageNum + 1
    })
    
    // 后端API请求参数
    const params = {
      page: this.data.pageNum,
      size: this.data.pageSize
    }
    
    // 根据类型添加过滤条件
    if (this.data.type === 'month') {
      params.month = parseInt(this.data.value)
    } else if (this.data.type === 'region') {
      params.region = this.data.value
    }
    
    // 添加用户ID和排除已答题参数
    if (this.data.userId) {
      params.userId = this.data.userId
      params.excludeAnswered = true
    }
    
    const that = this
    const request = require('../../utils/request.js')
    
    // 发起后端请求（题目列表不需要认证）
    request.get('/api/topics', params, false).then(res => {
      const newTopics = res.data.list || []
      
      that.setData({
        topicList: [...that.data.topicList, ...newTopics],
        hasMore: newTopics.length >= that.data.pageSize
      })
    }).catch(err => {
      console.error('加载更多题目失败', err)
      wx.showToast({
        title: '加载更多失败',
        icon: 'none'
      })
    }).finally(() => {
      wx.hideLoading()
    })
  },
  
  // 题目选择事件
  onTopicSelect: function(e) {
    const { selectedOptions, index } = e.detail
    // console.log('事件来源', e.detail.source)
    // 防止重复处理同一题目
    const topicId = this.data.topicList[index]?.id
    if (!topicId) return
    
    // 使用题目ID作为键来防止重复处理
    if (!this._processingTopics) {
      this._processingTopics = {}
    }
    
    if (this._processingTopics[topicId]) {
      console.log('题目正在处理中，忽略重复事件:', topicId)
      return
    }
    
    this._processingTopics[topicId] = true
    console.log('开始处理题目选择:', topicId)
    
    // 记录用户选择
    let userAnswers = { ...this.data.userAnswers }
    userAnswers[index] = selectedOptions
    
    this.setData({
      userAnswers
    })

    // 获取题目信息
    const topic = this.data.topicList[index]
    
    // 如果是单选题，立即显示答案和解析
    if (topic && topic.type === 1) {
      // 更新题目列表，标记该题已回答并显示答案
      const topicList = [...this.data.topicList]
      topicList[index].isAnswered = true
      topicList[index].userAnswer = selectedOptions
      
      this.setData({
        topicList
      })
    }
    
    // 注意：添加错题的逻辑已经在 topic-card 组件中处理，这里不需要重复调用
    
    // 更新题目进度到后端
    const app = getApp();
    
    // 检查是否已登录
    if (app.globalData.hasLogin && app.globalData.userInfo) {
      const requestData = {
        topicId: topic.id,
        month: this.data.type === 'month' ? parseInt(this.data.value) : null
      };
      
      console.log('发送完成题目请求：', requestData);
      
      const request = require('../../utils/request.js')
      const that = this
      request.post('/api/progress/finish-topic', requestData, true).then(res => {
        console.log('题目进度更新成功', res)
        // 更新个人中心的统计数据
        if (app.updateStatistics) {
          console.log('调用全局updateStatistics方法更新统计数据');
          app.updateStatistics();
        }
      }).catch(err => {
        console.error('题目进度更新失败', err)
        console.error('请求数据:', requestData);
        wx.showToast({
          title: '进度更新失败',
          icon: 'none'
        })
      }).finally(() => {
        // 重置处理标志
        if (that._processingTopics && topicId) {
          delete that._processingTopics[topicId]
          console.log('完成处理题目:', topicId)
        }
      })
    } else {
      console.warn('无法更新题目进度：用户未登录');
      // 即使未登录也要重置标志
      if (this._processingTopics && topicId) {
        delete this._processingTopics[topicId]
      }
    }
  },
  
  // 提交所有答案（考试模式新增）
  submitAllAnswers: function() {
    const { topicList, userAnswers } = this.data
    
    // 检查是否有题目未作答
    const answeredCount = Object.keys(userAnswers).length
    if (answeredCount < topicList.length) {
      wx.showModal({
        title: '提示',
        content: `您还有${topicList.length - answeredCount}道题未作答，确定要提交吗？`,
        success: (res) => {
          if (res.confirm) {
            this.showAllResults()
          }
        }
      })
    } else {
      this.showAllResults()
    }
  },
  
  // 显示所有结果（新增）
  showAllResults: function() {
    // 显示所有答案
    this.setData({
      showAllAnswers: true
    })
    
    // 滚动到顶部
    wx.pageScrollTo({
      scrollTop: 0,
      duration: 300
    })
    
    // 计算正确率
    const { topicList, userAnswers } = this.data
    let correctCount = 0
    let wrongCount = 0
    
    topicList.forEach((topic, index) => {
      const userAnswer = userAnswers[index]
      if (userAnswer) {
        // 简单比较用户答案和正确答案
        if (JSON.stringify(Object.keys(userAnswer).sort()) === topic.answer.split('').sort().join('')) {
          correctCount++
        } else {
          wrongCount++
        }
      }
    })
    
    // 显示结果统计
    wx.showModal({
      title: '答题结果',
      content: `答对: ${correctCount}题\n答错: ${wrongCount}题\n正确率: ${topicList.length ? Math.round(correctCount / topicList.length * 100) : 0}%`,
      showCancel: false
    })
  },
  
  // 题目收藏事件
  onTopicFavorite: function(e) {
    console.log('收藏状态变化:', e.detail)
    
    const { topicId, isFavorite } = e.detail
    const request = require('../../utils/request.js')
    
    // 向后端更新收藏状态
    const endpoint = isFavorite ? '/api/favorite/add' : '/api/favorite/delete'
    
    request.post(endpoint, {
      topicId: topicId
    }, true).then(res => {
      console.log('收藏操作成功:', res)
      wx.showToast({
        title: isFavorite ? '收藏成功' : '取消收藏',
        icon: 'success',
        duration: 1500
      })
    }).catch(err => {
      console.error('收藏操作失败:', err)
      wx.showToast({
        title: '操作失败',
        icon: 'none'
      })
    })
  },
  
  // 下一题事件
  onNextTopic: function(e) {
    const currentIndex = e.currentTarget.dataset.index
    const nextSelector = `.topic-item:nth-child(${currentIndex + 2}}`
    
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

  // 添加错题事件
  onAddMistake: function(e) {
    const { topicId, topic } = e.detail
    const app = getApp()
    
    // 调用全局方法添加错题
    app.addMistake(topic)
  },
  
  // 返回首页
  navigateBack: function() {
    wx.navigateBack()
  },
  
  // 跳转到个人中心页面
  navigateToProfile: function() {
    wx.switchTab({
      url: '/pages/profile/profile'
    })
  }
})