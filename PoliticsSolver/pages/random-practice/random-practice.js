// pages/random-practice/random-practice.js
const app = getApp()

Page({
  data: {
    questions: [],
    currentIndex: 0,
    months: [], // 选中的月份数组
    count: 20,
    userAnswers: {},
    showResult: false,
    correctCount: 0,
    wrongCount: 0,
    accuracy: '0.0',
    loading: true
  },

  onLoad: function(options) {
    console.log('=== random-practice onLoad ===');
    console.log('接收到的参数:', options);
    
    // 获取参数
    let months = [];
    if (options.months) {
      // 从逗号分隔的字符串转换为数组
      months = options.months.split(',').map(m => parseInt(m));
    } else if (options.startMonth && options.endMonth) {
      // 兼容旧的范围参数
      const startMonth = parseInt(options.startMonth);
      const endMonth = parseInt(options.endMonth);
      for (let i = startMonth; i <= endMonth; i++) {
        months.push(i);
      }
    } else {
      // 默认所有月份
      months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    }
    
    const count = parseInt(options.count) || 20;

    console.log('解析后的月份:', months);
    console.log('题目数量:', count);

    this.setData({
      months: months,
      count: count
    })

    // 加载题目
    this.loadQuestions()
  },

  // 加载题目
  loadQuestions: function() {
    const that = this
    const request = require('../../utils/request.js');

    wx.showLoading({
      title: '加载题目中...'
    })

    console.log('请求参数:', {
      months: this.data.months.join(','),
      count: this.data.count
    });

    request.get('/api/topics/random', {
      months: this.data.months.join(','), // 传递月份数组
      count: this.data.count
    }, false).then(res => {
      wx.hideLoading();
      
      const questions = res.data || [];
      
      if (questions.length === 0) {
        wx.showModal({
          title: '提示',
          content: '该月份范围内暂无题目',
          showCancel: false,
          success: function() {
            wx.navigateBack();
          }
        });
        return;
      }

      that.setData({
        questions: questions,
        loading: false
      });
    }).catch(err => {
      wx.hideLoading();
      console.error('加载题目失败:', err);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    });
  },

  // 处理选择事件
  onSelectOption: function(e) {
    const { index, selectedOptions, isCorrect } = e.detail
    const topicId = this.data.questions[index].id
    const month = this.data.questions[index].month

    // 记录用户答案
    const userAnswers = this.data.userAnswers
    userAnswers[topicId] = {
      selectedOptions: selectedOptions,
      isCorrect: isCorrect
    }

    this.setData({
      userAnswers: userAnswers
    })

    // 记录答题进度
    this.recordProgress(topicId, month)
  },

  // 记录答题进度
  recordProgress: function(topicId, month) {
    const userInfo = app.globalData.userInfo
    if (!userInfo) {
      console.log('用户未登录，跳过进度记录');
      return;
    }

    const request = require('../../utils/request.js');
    
    request.post('/api/progress/finish-topic', {
      topicId: topicId,
      month: month
    }, true).then(res => {
      console.log('进度记录成功:', res);
    }).catch(err => {
      console.error('记录进度失败:', err);
    });
  },

  // 下一题
  onNextTopic: function() {
    const nextIndex = this.data.currentIndex + 1
    
    if (nextIndex < this.data.questions.length) {
      this.setData({
        currentIndex: nextIndex
      })
    } else {
      // 所有题目已完成，显示结果
      this.showResults()
    }
  },

  // 显示结果
  showResults: function() {
    const userAnswers = this.data.userAnswers
    let correctCount = 0
    let wrongCount = 0

    // 统计正确和错误数量
    Object.keys(userAnswers).forEach(topicId => {
      if (userAnswers[topicId].isCorrect) {
        correctCount++
      } else {
        wrongCount++
      }
    })

    // 计算正确率
    const accuracy = this.data.questions.length > 0 
      ? (correctCount / this.data.questions.length * 100).toFixed(1)
      : '0.0'

    this.setData({
      showResult: true,
      correctCount: correctCount,
      wrongCount: wrongCount,
      accuracy: accuracy
    })
  },

  // 返回首页
  backToHome: function() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  },

  // 再来一次
  retryPractice: function() {
    this.setData({
      currentIndex: 0,
      userAnswers: {},
      showResult: false,
      correctCount: 0,
      wrongCount: 0,
      loading: true
    })
    this.loadQuestions()
  }
})
