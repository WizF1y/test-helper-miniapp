Component({
  options: {
    multipleSlots: true // 启用多slot支持
  },
  
  properties: {
    // 题目数据
    topic: {
      type: Object,
      value: {}
    },
    // 在列表中的索引
    index: {
      type: Number,
      value: 0
    },
    // 是否显示操作按钮
    showActions: {
      type: Boolean,
      value: true
    },
    // 是否有下一题
    hasNext: {
      type: Boolean,
      value: true
    },
    
    // 列表类型 (normal, favorite, mistake)
    listType: {
      type: String,
      value: 'normal'
    },
    
    // 是否显示答案(新增外部控制属性)
    showAnswer: {
      type: Boolean,
      value: false,
      observer: function(newVal) {
        if (this.data.__debug__) {
          console.log('showAnswer changed to:', newVal);
        }
        
        // 如果是从 selectOption 触发的，不要重复处理
        if (this._fromSelectOption) {
          console.log('showAnswer 由 selectOption 设置，跳过 observer 处理');
          return;
        }
        
        // 如果是从 toggleAnswer 触发的，也不要重复处理
        if (this._fromToggleAnswer) {
          console.log('showAnswer 由 toggleAnswer 设置，跳过 observer 处理');
          return;
        }
        
        if (newVal) {
          // 当外部设置为显示答案时，检查正确性
          // 传入 skipEvent=true, skipAddMistake=true
          // 因为外部设置通常是页面刷新，不需要重复触发事件和添加错题
          // 只需要更新选项的显示状态（通过 updateOptionStatus）
          this.checkAnswerCorrectness(true, true);
        }
      }
    },
    // 调试模式
    __debug__: {
      type: Boolean,
      value: false
    }
  },
  
  data: {
    // 题目类型标签映射
    typeLabels: {
      1: '单选题',
      2: '多选题',
      3: '判断题',
      4: '填空题',
      5: '简答题'
    },
    // 改为对象存储多个选项
    selectedOptions: {},
    // 是否已收藏
    isFavorite: false,
    // 是否已答题（用于记录用户是否已完成该题）
    isAnswered: false,
    // 选项状态映射
    optionStatus: {},
    // 调试用的字符串化数据
    selectedOptionsStr: '{}',
    optionStatusStr: '{}'
  },
  
  observers: {
    // 监听相关数据变化，更新选项状态
    'showAnswer, selectedOptions, topic': function() {
      this.updateOptionStatus();
    },
    // 监听 topic 变化，重置组件状态
    'topic.id': function(newId, oldId) {
      if (newId && newId !== oldId) {
        console.log('=== topic 变化，重置组件状态 ===');
        console.log('旧 ID:', oldId, '新 ID:', newId);
        this.resetComponentState();
      }
    }
  },
  
  lifetimes: {
    attached: function() {
      console.log('=== topic-card attached ===')
      console.log('listType:', this.properties.listType)
      console.log('topic.id:', this.data.topic.id)
      
      // 如果在收藏列表中，直接设置为已收藏
      if (this.properties.listType === 'favorite') {
        console.log('在收藏列表中，设置 isFavorite = true')
        this.setData({ isFavorite: true })
      } else {
        // 其他情况检查收藏状态
        this.checkFavoriteStatus();
      }
      
      console.log('初始化后 isFavorite:', this.data.isFavorite)
      
      // 初始化选项状态
      this.updateOptionStatus();
    }
  },
  
  methods: {
    // 重置组件状态
    resetComponentState: function() {
      console.log('重置组件状态');
      this.setData({
        selectedOptions: {},
        selectedOptionsStr: '{}',
        showAnswer: false,
        isAnswered: false,
        optionStatus: {},
        optionStatusStr: '{}'
      });
      
      // 重新检查收藏状态
      if (this.properties.listType === 'favorite') {
        this.setData({ isFavorite: true });
      } else {
        this.checkFavoriteStatus();
      }
    },
    
    // 选择选项
    selectOption: function(e) {
      // 如果答案已显示，则不能再选择选项
      if (this.data.showAnswer) return;
      
      // 防止重复点击
      if (this._selecting) {
        console.log('正在处理选择，忽略重复点击');
        return;
      }
      this._selecting = true;
      
      const key = e.currentTarget.dataset.key;
      const option = this.data.topic.options.find(opt => opt.key === key);
      
      if (!option) return;
      
      let selectedOptions = Object.assign({}, this.data.selectedOptions);
      
      if (this.data.topic.type === 2) { // 多选题
        // 切换选项的选中状态
        if (selectedOptions[key]) {
          delete selectedOptions[key];
        } else {
          selectedOptions[key] = option;
        }
      } else { // 单选题
        // 单选题：只能选中一个选项，直接替换
        selectedOptions = {};
        selectedOptions[key] = option;
      }
      
      // 更新选中状态
      this.setData({
        selectedOptions: selectedOptions,
        selectedOptionsStr: JSON.stringify(selectedOptions)
      });
      
      // 检查答案正确性（skipEvent=true 避免重复触发事件，skipAddMistake=true 避免重复添加错题）
      const isCorrect = this.checkAnswerCorrectness(true, true);
      
      this.triggerEvent('select', {
        index: this.data.index,
        selectedOptions: selectedOptions,
        isCorrect: isCorrect
      })
      
      // 如果是单选题，选择后立即显示答案
      // 设置标志，让 observer 知道这是从 selectOption 触发的，不要重复处理
      if (this.data.topic.type === 1) {
        this._fromSelectOption = true
        this.setData({
          showAnswer: true
        }, () => {
          // 在 setData 完成后再重置标志
          this._fromSelectOption = false
          console.log('showAnswer 设置完成，重置 _fromSelectOption 标志')
        });
      }
      
      // 如果选错了，且不在错题列表中，自动加入错题本
      // 注意：这里统一处理添加错题，checkAnswerCorrectness 中传入 skipAddMistake=true 避免重复
      if (!isCorrect && this.properties.listType !== 'mistake') {
        this.addToMistakes();
      }
      
      // 重置选择标志
      this._selecting = false;
      
      return isCorrect;
    },
    
    // 更新选项状态
    updateOptionStatus: function() {
      const topic = this.data.topic;
      const showAnswer = this.data.showAnswer;
      const selectedOptions = this.data.selectedOptions;
      const answer = topic.answer || '';
      
      if (!topic.options) return;
      
      // 创建选项状态映射
      const optionStatus = {};
      
      topic.options.forEach(option => {
        const key = option.key;
        if (showAnswer) {
          // 答案已显示，根据正确性判断
          if (answer.includes(key)) {
            optionStatus[key] = 'correct';
          } else if (selectedOptions[key]) {
            optionStatus[key] = 'wrong';
          } else {
            optionStatus[key] = '';
          }
        } else {
          // 答案未显示，根据选择状态判断
          if (selectedOptions[key]) {
            optionStatus[key] = 'selected';
          } else {
            optionStatus[key] = '';
          }
        }
      });
      
      if (this.data.__debug__) {
        console.log('Update option status:', {showAnswer, selectedOptions, answer, optionStatus});
      }
      
      this.setData({
        optionStatus: optionStatus,
        optionStatusStr: JSON.stringify(optionStatus)
      });
    },
    
    // 检查选项是否正确
    isOptionCorrect: function(key) {
      const answer = this.data.topic.answer || '';
      
      // 调试输出
      if (this.data.__debug__) {
        console.log('Checking option key:', key, 'against answer:', answer, 'includes:', answer.includes(key));
      }
      
      const result = answer.includes(key);
      
      if (this.data.__debug__) {
        console.log('isOptionCorrect result for', key, ':', result);
      }
      
      return result;
    },
    
    // 判断是否有选项被选中
    hasSelection: function() {
      const count = Object.keys(this.data.selectedOptions).length;
      if (this.data.__debug__) {
        console.log('Has selection:', count > 0, 'Count:', count);
      }
      return count > 0;
    },
    
    // 检查答案正确性
    checkAnswerCorrectness: function(skipEvent, skipAddMistake) {
      // 获取所有选中的选项
      const selectedKeys = Object.keys(this.data.selectedOptions);
      if (selectedKeys.length === 0) {
        if (this.data.__debug__) {
          console.log('No selected options, skipping answer correctness check');
        }
        return;
      }
      
      const answer = this.data.topic.answer || '';
      let isCorrect = false;
      
      if (this.data.topic.type === 2) { // 多选题
        // 检查所选项是否与答案完全一致
        if (selectedKeys.length === answer.length) {
          isCorrect = selectedKeys.every(key => answer.includes(key)) && 
                      answer.split('').every(key => selectedKeys.includes(key));
        }
      } else { // 单选题
        isCorrect = selectedKeys.length === 1 && selectedKeys[0] === answer;
      }
      
      if (this.data.__debug__) {
        console.log('Check answer correctness:', {selectedKeys, answer, isCorrect});
      }
      
      // 如果skipEvent为true，则不触发select事件
      if (!skipEvent) {
        // console.log('=== checkAnswerCorrectness 触发 select 事件 ===')
        // console.log('题目ID:', this.data.topic.id)
        // console.log('skipEvent:', skipEvent)
        // console.log('skipAddMistake:', skipAddMistake)
        // console.log('调用栈:', new Error().stack)
        
        // 触发选择事件
        this.triggerEvent('select', {
          topicId: this.data.topic.id,
          selectedOptions: this.data.selectedOptions,
          isCorrect: isCorrect,
          index: this.properties.index,
          // source: 'checkanswer'
        });
      }
      
      // 如果在错题列表中答对了，触发correct事件
      if (isCorrect && this.properties.listType === 'mistake') {
        this.triggerEvent('correct', {
          topicId: this.data.topic.id
        });
      }
      
      // 如果选错了，且不在错题列表和收藏列表中，自动加入错题本
      // skipAddMistake 为 true 时跳过（避免重复添加）
      // 注意：当前所有调用都传入 skipAddMistake=true，由调用方统一处理添加错题
      // 这样设计是为了灵活性，未来可能有其他调用场景需要在这里添加错题
      if (!skipAddMistake && !isCorrect && this.properties.listType !== 'mistake' && this.properties.listType !== 'favorite') {
        this.addToMistakes();
      }
      
      return isCorrect;
    },
    
    // 切换收藏状态
    toggleFavorite: function() {
      console.log('=== toggleFavorite 被调用 ===')
      console.log('当前 isFavorite:', this.data.isFavorite)
      console.log('listType:', this.properties.listType)
      
      // 先更新本地状态
      const newFavoriteState = !this.data.isFavorite
      console.log('新的 isFavorite:', newFavoriteState)
      
      this.setData({
        isFavorite: newFavoriteState
      })
      
      // 触发收藏事件，由父组件处理业务逻辑
      this.triggerEvent('favorite', {
        topicId: this.data.topic.id,
        isFavorite: newFavoriteState
      })
      
      console.log('触发 favorite 事件:', {topicId: this.data.topic.id, isFavorite: newFavoriteState})

      // 触发刷新事件，通知父组件刷新数据
      this.triggerEvent('refresh');
    },
    
    // 从错题本中移除
    removeMistake: function() {
      console.log('=== removeMistake 被调用 ===')
      console.log('题目ID:', this.data.topic.id)
      console.log('题目数据:', this.data.topic)
      
      // 只触发事件，由父组件处理业务逻辑
      this.triggerEvent('removeMistake', {
        topicId: this.data.topic.id
      })
      
      console.log('removeMistake 事件已触发')
    },
    
    // 切换显示答案
    toggleAnswer: function() {
      // 只有多选题可以切换答案显示，且必须至少选择一个选项
      if (this.data.topic.type !== 2) return;
      
      // 如果没有选择任何选项，则不执行操作
      if (!this.hasSelection()) {
        wx.showToast({
          title: '请至少选择一个选项',
          icon: 'none'
        });
        return;
      }
      
      // 如果之前未答题，现在查看答案则标记为已答题
      if (!this.data.isAnswered && !this.data.showAnswer) {
        this.setData({
          isAnswered: true
        });
        
        // 向父组件发送答题事件
        this.triggerEvent('answer', {
          topicId: this.data.topic.id,
          selectedOptions: this.data.selectedOptions,
          index: this.properties.index
        });
      }
      
      // 设置标志，让 observer 知道这是从 toggleAnswer 触发的
      this._fromToggleAnswer = true
      this.setData({
        showAnswer: !this.data.showAnswer
      }, () => {
        // 在 setData 完成后再重置标志
        this._fromToggleAnswer = false
        console.log('showAnswer 切换完成，重置 _fromToggleAnswer 标志')
      });
    },
    
    // 下一题
    nextTopic: function() {
      this.triggerEvent('next')
      
      // 重置组件状态
      this.setData({
        selectedOptions: {},
        selectedOptionsStr: '{}',
        showAnswer: false
      })
    },
    
    // 检查收藏状态
    checkFavoriteStatus: function(e) {
      try {
        const app = getApp()
        const key = app.globalData.storageKeys.favorites
        const favorites = wx.getStorageSync(key) || []
        
        const isFavorite = favorites.some(item => item.id === this.data.topic.id)
        this.setData({ isFavorite })
      } catch (e) {
        console.error('检查收藏状态失败', e)
      }
    },
    
    // 加入错题本
    addToMistakes: function() {
      // 触发添加错题事件，由父组件处理业务逻辑
      this.triggerEvent('addMistake', {
        topicId: this.data.topic.id,
        topic: this.data.topic
      })
      
      wx.showToast({
        title: '已加入错题本',
        icon: 'none'
      })
    }
  },
  
})