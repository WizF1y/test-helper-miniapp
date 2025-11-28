Component({
  properties: {
    // 图片地址
    image: {
      type: String,
      value: ''
    },
    // 提示文字
    text: {
      type: String,
      value: ''
    },
    // 按钮文字，如果为空则不显示按钮
    btnText: {
      type: String,
      value: ''
    },
    // 上边距
    marginTop: {
      type: Number,
      value: 120
    }
  },
  
  methods: {
    // 按钮点击事件
    onActionTap: function() {
      this.triggerEvent('action')
    }
  }
}) 