Page({
  data: {
    questions: [],       // 题目列表
    currentIndex: 0,     // 当前题目索引
    totalQuestions: 20,  // 总题数
    examTime: 1800,      // 考试时间（秒），默认30分钟
    usedTime: 0,         // 已用时间
    usedTimeText: '00:00:00', // 已用时间文本
    swiperHeight: 500,   // 滑块高度
    showSubmitModal: false, // 是否显示提交确认弹窗
    showResult: false,   // 是否显示结果页面
    answeredCount: 0,    // 已答题数量
    correctCount: 0,     // 正确题目数量
    wrongCount: 0,       // 错误题目数量
    score: 0,            // 考试得分
    accuracy: '0.0',     // 正确率
    answers: {},         // 用户答案记录 {题目ID: {selectedOption, isCorrect}}
    startTime: 0,        // 开始时间戳
    endTime: 0,          // 结束时间戳
    examRecordId: null,  // 考试记录ID
    examDetails: []      // 考试详情数据
  },

  onLoad: function() {
    // 从后端获取随机题目
    this.loadRandomQuestions()
    
    // 获取系统信息设置滑块高度
    wx.getSystemInfo({
      success: (res) => {
        this.setData({
          swiperHeight: res.windowHeight - 200 // 减去头部和底部高度
        })
      }
    })
    
    // 记录开始时间
    this.setData({
      startTime: Date.now()
    })
  },
  
  // 从后端加载随机题目
  loadRandomQuestions: function() {
    wx.showLoading({
      title: '正在出题...'
    })
    
    const app = getApp()
    const baseUrl = app.globalData.baseUrl
    
    wx.request({
      url: `${baseUrl}/api/exam/random`,
      method: 'GET',
      data: {
        count: this.data.totalQuestions
      },
      success: (res) => {
        wx.hideLoading()
        
        if (res.data.code === 0) {
          this.setData({ 
            questions: res.data.data 
          })
        } else {
          wx.showToast({
            title: res.data.message || '获取题目失败',
            icon: 'none'
          })
        }
      },
      fail: (err) => {
        wx.hideLoading()
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        console.error('Load questions error:', err)
      }
    })
  },
  
  // 滑块切换事件
  onSwiperChange: function(e) {
    this.setData({
      currentIndex: e.detail.current
    })
  },
  
  // 题目选择事件
  onTopicSelect: function(e) {
    const { topicId, selectedOption, isCorrect } = e.detail
    
    // 更新答题记录
    const answers = { ...this.data.answers }
    answers[topicId] = { selectedOption, isCorrect }
    
    // 统计已答题数和正确/错误数
    const answeredCount = Object.keys(answers).length
    let correctCount = 0
    let wrongCount = 0
    
    for (const key in answers) {
      if (answers[key].isCorrect) {
        correctCount++
      } else {
        wrongCount++
      }
    }
    
    this.setData({
      answers,
      answeredCount,
      correctCount,
      wrongCount
    })
  },
  
  // 题目收藏事件
  onTopicFavorite: function(e) {
    console.log('收藏状态变化:', e.detail)
  },
  
  // 上一题
  onPrevTopic: function() {
    if (this.data.currentIndex > 0) {
      this.setData({
        currentIndex: this.data.currentIndex - 1
      })
    }
  },
  
  // 下一题
  onNextTopic: function() {
    if (this.data.currentIndex < this.data.totalQuestions - 1) {
      this.setData({
        currentIndex: this.data.currentIndex + 1
      })
    }
  },
  
  // 时间结束事件
  onTimeFinish: function() {
    wx.showModal({
      title: '提示',
      content: '考试时间已到，系统将自动交卷',
      showCancel: false,
      success: () => {
        this.confirmSubmit()
      }
    })
  },
  
  // 提交试卷
  submitExam: function() {
    this.setData({
      showSubmitModal: true
    })
  },
  
  // 取消提交
  cancelSubmit: function() {
    this.setData({
      showSubmitModal: false
    })
  },
  
  // 确认提交
  confirmSubmit: function() {
    // 计算用时
    const endTime = Date.now()
    const usedTimeMs = endTime - this.data.startTime
    const usedTime = Math.floor(usedTimeMs / 1000)
    
    // 格式化用时
    const hours = Math.floor(usedTime / 3600)
    const minutes = Math.floor((usedTime % 3600) / 60)
    const seconds = usedTime % 60
    const usedTimeText = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    
    // 计算得分
    const score = Math.round((this.data.correctCount / this.data.totalQuestions) * 100)
    
    // 暂停倒计时
    const countdown = this.selectComponent('#countdown')
    if (countdown) {
      countdown.pauseCountdown()
    }
    
    // 准备答题详情数据
    const details = []
    this.data.questions.forEach(question => {
      const answer = this.data.answers[question.id]
      if (answer) {
        details.push({
          topicId: question.id,
          userAnswer: answer.selectedOption,
          isCorrect: answer.isCorrect
        })
      }
    })
    
    // 提交考试结果到后端
    this.submitExamToBackend(score, usedTime, details, usedTimeText)
  },
  
  // 提交考试结果到后端
  submitExamToBackend: function(score, usedTime, details, usedTimeText) {
    const app = getApp()
    const baseUrl = app.globalData.baseUrl
    const userId = app.globalData.userId
    
    if (!userId) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }
    
    wx.showLoading({
      title: '提交中...'
    })
    
    wx.request({
      url: `${baseUrl}/api/exam/submit`,
      method: 'POST',
      data: {
        userId: userId,
        score: score,
        totalQuestions: this.data.totalQuestions,
        correctCount: this.data.correctCount,
        wrongCount: this.data.wrongCount,
        usedTime: usedTime,
        details: details
      },
      success: (res) => {
        wx.hideLoading()
        
        if (res.data.code === 0) {
          // 计算正确率
          const accuracy = (this.data.correctCount / this.data.totalQuestions * 100).toFixed(1)
          
          // 保存考试记录ID
          this.setData({
            showSubmitModal: false,
            showResult: true,
            endTime: Date.now(),
            usedTime: usedTime,
            usedTimeText: usedTimeText,
            score: score,
            accuracy: accuracy,
            examRecordId: res.data.data.recordId
          })
        } else {
          wx.showToast({
            title: res.data.message || '提交失败',
            icon: 'none'
          })
        }
      },
      fail: (err) => {
        wx.hideLoading()
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        console.error('Submit exam error:', err)
      }
    })
  },
  
  // 查看解析
  reviewExam: function() {
    const examRecordId = this.data.examRecordId
    
    if (examRecordId) {
      // 从后端加载详细的答题分析
      this.loadExamDetail(examRecordId)
    } else {
      // 如果没有记录ID，直接显示题目
      this.setData({
        showResult: false,
        currentIndex: 0
      })
    }
  },
  
  // 加载考试详情
  loadExamDetail: function(recordId) {
    wx.showLoading({
      title: '加载中...'
    })
    
    const app = getApp()
    const baseUrl = app.globalData.baseUrl
    
    wx.request({
      url: `${baseUrl}/api/exam/detail/${recordId}`,
      method: 'GET',
      success: (res) => {
        wx.hideLoading()
        
        if (res.data.code === 0) {
          const examData = res.data.data
          
          // 更新题目数据，添加用户答案和正确性标记
          const updatedQuestions = this.data.questions.map(question => {
            const detail = examData.details.find(d => d.topicId === question.id)
            if (detail) {
              return {
                ...question,
                userAnswer: detail.userAnswer,
                isCorrect: detail.isCorrect,
                showAnalysis: true  // 显示解析
              }
            }
            return question
          })
          
          this.setData({
            showResult: false,
            currentIndex: 0,
            questions: updatedQuestions,
            examDetails: examData.details
          })
        } else {
          wx.showToast({
            title: res.data.message || '加载失败',
            icon: 'none'
          })
          // 即使加载失败，也显示题目
          this.setData({
            showResult: false,
            currentIndex: 0
          })
        }
      },
      fail: (err) => {
        wx.hideLoading()
        wx.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        console.error('Load exam detail error:', err)
        // 即使加载失败，也显示题目
        this.setData({
          showResult: false,
          currentIndex: 0
        })
      }
    })
  },
  
  // 返回首页
  returnToHome: function() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  }
}) 