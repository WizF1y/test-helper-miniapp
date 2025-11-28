// pages/random-settings/random-settings.js
Page({
  data: {
    months: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    startMonthIndex: 0,
    endMonthIndex: 11,
    questionCount: 20
  },

  onStartMonthChange(e) {
    this.setData({
      startMonthIndex: e.detail.value
    });
  },

  onEndMonthChange(e) {
    this.setData({
      endMonthIndex: e.detail.value
    });
  },

  onQuestionCountChange(e) {
    const counts = [10, 20, 30, 50];
    const selectedCount = counts[e.detail.value];
    this.setData({
      questionCount: selectedCount
    });
  },

  startRandomMode() {
    const startMonth = this.data.months[this.data.startMonthIndex];
    const endMonth = this.data.months[this.data.endMonthIndex];
    const count = this.data.questionCount;
    
    // 验证月份范围
    if (startMonth > endMonth) {
      wx.showToast({
        title: '起始月份不能大于结束月份',
        icon: 'none'
      });
      return;
    }
    
    wx.navigateTo({
      url: `/pages/random-practice/random-practice?startMonth=${startMonth}&endMonth=${endMonth}&count=${count}`
    });
  }
});