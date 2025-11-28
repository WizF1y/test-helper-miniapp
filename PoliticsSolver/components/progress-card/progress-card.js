Component({
  properties: {
    // 月份
    month: {
      type: Number,
      value: 1
    },
    // 总题目数
    totalTopics: {
      type: Number,
      value: 0
    },
    // 已完成题目数
    completedTopics: {
      type: Number,
      value: 0
    },
    // 正确率
    correctRate: {
      type: Number,
      value: 0
    },
    // 学习时长（秒）
    timeSpent: {
      type: Number,
      value: 0
    }
  },
  
  data: {
    progressPercent: 0,
    formattedTime: '0分钟'
  },
  
  lifetimes: {
    attached: function() {
      this.calculateProgress();
      this.formatTime();
    }
  },
  
  observers: {
    'completedTopics, totalTopics': function() {
      this.calculateProgress();
    },
    'timeSpent': function() {
      this.formatTime();
    }
  },
  
  methods: {
    // 计算进度百分比
    calculateProgress: function() {
      const { completedTopics, totalTopics } = this.data;
      let percent = 0;
      
      if (totalTopics > 0) {
        percent = Math.round((completedTopics / totalTopics) * 100);
      }
      
      this.setData({
        progressPercent: percent
      });
    },
    
    // 格式化时间
    formatTime: function() {
      const seconds = this.data.timeSpent;
      let formatted = '0分钟';
      
      if (seconds < 60) {
        formatted = `${seconds}秒`;
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        formatted = `${minutes}分钟`;
      } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        formatted = `${hours}小时${minutes}分钟`;
      }
      
      this.setData({
        formattedTime: formatted
      });
    },
    
    // 点击卡片事件
    onCardTap: function() {
      this.triggerEvent('tap', {
        month: this.data.month
      });
    }
  }
})
