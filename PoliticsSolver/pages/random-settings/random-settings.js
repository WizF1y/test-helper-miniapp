Page({
  data: {
    months: [], // 近6个月
    selectedMonths: [], // 选中的月份
    questionCount: 20, // 题目数量
    questionCounts: [10, 20, 30] // 可选的题目数量
  },

  onLoad: function(options) {
    // 生成近6个月
    const currentMonth = new Date().getMonth() + 1;
    const recentMonths = [];
    for (let i = 0; i < 6; i++) {
      const month = currentMonth - i > 0 ? currentMonth - i : 12 + (currentMonth - i);
      recentMonths.push(month);
    }
    
    console.log('近6个月:', recentMonths);
    console.log('默认选中:', [currentMonth]);
    
    this.setData({
      months: recentMonths,
      selectedMonths: [currentMonth]
    });
  },

  // 切换月份选择（多选）
  toggleMonth: function(e) {
    // 确保 month 是数字类型
    const month = parseInt(e.currentTarget.dataset.month);
    console.log('=== 点击月份 ===');
    console.log('点击的月份:', month);
    console.log('点击前 selectedMonths:', JSON.stringify(this.data.selectedMonths));
    
    let selectedMonths = [...this.data.selectedMonths];
    
    const index = selectedMonths.indexOf(month);
    console.log('indexOf 结果:', index);
    
    if (index > -1) {
      // 已选中，取消选择
      selectedMonths.splice(index, 1);
      console.log('执行取消选择');
    } else {
      // 未选中，添加选择
      selectedMonths.push(month);
      console.log('执行添加选择');
    }
    
    // 排序
    selectedMonths.sort((a, b) => a - b);
    console.log('排序后 selectedMonths:', JSON.stringify(selectedMonths));
    
    this.setData({
      selectedMonths: selectedMonths
    }, () => {
      console.log('setData 完成后 selectedMonths:', JSON.stringify(this.data.selectedMonths));
    });
  },

  // 选择题目数量
  selectQuestionCount: function(e) {
    // 确保 count 是数字类型
    const count = parseInt(e.currentTarget.dataset.count);
    this.setData({
      questionCount: count
    });
  },

  // 开始练习
  startPractice: function() {
    if (this.data.selectedMonths.length === 0) {
      wx.showToast({
        title: '请至少选择一个月份',
        icon: 'none'
      });
      return;
    }

    // 跳转到随机练习页面
    wx.navigateTo({
      url: `/pages/random-practice/random-practice?months=${this.data.selectedMonths.join(',')}&count=${this.data.questionCount}`
    });
  }
})