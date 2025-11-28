Component({
  properties: {
    // 倒计时总秒数
    seconds: {
      type: Number,
      value: 1800, // 默认30分钟
      observer(newVal, oldVal) {
        if (newVal !== oldVal) {
          this.initCountdown()
        }
      }
    },
    // 剩余时间低于多少秒进入警告状态
    warningSeconds: {
      type: Number,
      value: 300 // 默认5分钟
    },
    // 自动开始倒计时
    autoStart: {
      type: Boolean,
      value: true
    }
  },
  
  data: {
    hours: '00',
    minutes: '00',
    seconds: '00',
    isWarning: false,
    remainingSeconds: 0,
    countdownInterval: null
  },
  
  lifetimes: {
    attached: function() {
      this.initCountdown()
      
      // 自动开始倒计时
      if (this.data.autoStart) {
        this.startCountdown()
      }
    },
    detached: function() {
      this.clearCountdown()
    }
  },
  
  methods: {
    // 初始化倒计时
    initCountdown: function() {
      this.setData({ 
        remainingSeconds: this.properties.seconds
      })
      this.updateTimeDisplay()
    },
    
    // 开始倒计时
    startCountdown: function() {
      // 清除可能存在的倒计时
      this.clearCountdown()
      
      // 设置定时器
      const countdownInterval = setInterval(() => {
        let { remainingSeconds } = this.data
        
        if (remainingSeconds <= 0) {
          this.clearCountdown()
          this.triggerEvent('finish')
          return
        }
        
        // 减少剩余时间
        remainingSeconds -= 1
        
        // 更新状态
        this.setData({
          remainingSeconds,
          isWarning: remainingSeconds <= this.properties.warningSeconds
        })
        
        // 更新显示
        this.updateTimeDisplay()
        
        // 触发倒计时事件
        this.triggerEvent('tick', { remainingSeconds })
      }, 1000)
      
      this.setData({ countdownInterval })
    },
    
    // 暂停倒计时
    pauseCountdown: function() {
      this.clearCountdown()
    },
    
    // 重置倒计时
    resetCountdown: function() {
      this.clearCountdown()
      this.initCountdown()
    },
    
    // 清除倒计时定时器
    clearCountdown: function() {
      const { countdownInterval } = this.data
      if (countdownInterval) {
        clearInterval(countdownInterval)
        this.setData({ countdownInterval: null })
      }
    },
    
    // 更新时间显示
    updateTimeDisplay: function() {
      const { remainingSeconds } = this.data
      
      // 计算时分秒
      const hours = Math.floor(remainingSeconds / 3600)
      const minutes = Math.floor((remainingSeconds % 3600) / 60)
      const seconds = remainingSeconds % 60
      
      // 更新显示
      this.setData({
        hours: hours.toString().padStart(2, '0'),
        minutes: minutes.toString().padStart(2, '0'),
        seconds: seconds.toString().padStart(2, '0')
      })
    }
  }
}) 