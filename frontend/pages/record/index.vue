<template>
  <view class="container">
    <view class="section">
      <!-- 日期选择 -->
      <view class="date-selector card">
        <view class="date-display" @click="showDatePicker = true">
          <text class="date-label">记录日期</text>
          <view class="date-value">
            <text class="date-text">{{ formatDisplayDate(selectedDate) }}</text>
            <text class="date-arrow">▼</text>
          </view>
        </view>
      </view>

      <!-- 日期选择器弹窗 -->
      <view class="date-picker-mask" v-if="showDatePicker" @click="showDatePicker = false">
        <view class="date-picker-popup" @click.stop>
          <view class="picker-header">
            <text class="picker-cancel" @click="showDatePicker = false">取消</text>
            <text class="picker-title">选择日期</text>
            <text class="picker-confirm" @click="confirmDate">确定</text>
          </view>
          <picker-view 
            class="picker-view" 
            :value="pickerValue" 
            @change="onPickerChange"
          >
            <picker-view-column>
              <view class="picker-item" v-for="year in years" :key="year">{{ year }}年</view>
            </picker-view-column>
            <picker-view-column>
              <view class="picker-item" v-for="month in months" :key="month">{{ month }}月</view>
            </picker-view-column>
            <picker-view-column>
              <view class="picker-item" v-for="day in days" :key="day">{{ day }}日</view>
            </picker-view-column>
          </picker-view>
        </view>
      </view>

      <text class="section-title">{{ isToday ? '今日记录' : '历史记录' }}</text>
      
      <!-- 体重 -->
      <view class="record-item card">
        <text class="label">体重 (kg)</text>
        <input type="digit" v-model="weight" placeholder="请输入" :disabled="loading" />
      </view>

      <!-- 症状 -->
      <view class="record-item card">
        <text class="label">症状</text>
        <view class="symptom-list">
          <view :class="['symptom', symptoms.includes(s) ? 'active' : '']" 
                v-for="s in symptomOptions" :key="s" @click="toggleSymptom(s)">
            {{ s }}
          </view>
        </view>
      </view>

      <!-- 情绪 -->
      <view class="record-item card">
        <text class="label">今日心情</text>
        <view class="mood-list">
          <view :class="['mood', mood === m.value ? 'active' : '']" 
                v-for="m in moods" :key="m.value" @click="mood = m.value">
            {{ m.emoji }}
          </view>
        </view>
      </view>

      <!-- 查看趋势按钮 -->
      <button class="trend-btn" @click="viewChart">查看趋势</button>
      
      <!-- 保存按钮 -->
      <button class="save-btn" @click="save" :disabled="saving">
        {{ saving ? '保存中...' : '保存记录' }}
      </button>
    </view>
  </view>
</template>

<script>
import api from '@/utils/request.js'

export default {
  data() {
    return {
      weight: '',
      symptoms: [],
      mood: 'good',
      symptomOptions: ['孕吐', '疲劳', '水肿', '便秘', '失眠', '食欲不振'],
      moods: [
        { value: 'great', emoji: '😊' },
        { value: 'good', emoji: '🙂' },
        { value: 'normal', emoji: '😐' },
        { value: 'bad', emoji: '😔' }
      ],
      selectedDate: new Date(),
      showDatePicker: false,
      pickerValue: [0, 0, 0],
      loading: false,
      saving: false
    }
  },
  computed: {
    // 判断是否是今天
    isToday() {
      const today = new Date()
      return this.selectedDate.toDateString() === today.toDateString()
    },
    // 年份列表（当前年份往前2年）
    years() {
      const currentYear = new Date().getFullYear()
      return Array.from({ length: 3 }, (_, i) => currentYear - i)
    },
    // 月份列表
    months() {
      return Array.from({ length: 12 }, (_, i) => i + 1)
    },
    // 天数列表（根据月份动态计算）
    days() {
      const year = this.years[this.pickerValue[0]] || new Date().getFullYear()
      const month = this.months[this.pickerValue[1]] || 1
      const daysInMonth = new Date(year, month, 0).getDate()
      return Array.from({ length: daysInMonth }, (_, i) => i + 1)
    }
  },
  onLoad() {
    this.initPickerValue()
    this.loadRecord()
  },
  methods: {
    // 初始化日期选择器的值
    initPickerValue() {
      const now = new Date()
      const yearIndex = this.years.indexOf(now.getFullYear())
      this.pickerValue = [
        yearIndex >= 0 ? yearIndex : 0,
        now.getMonth(),
        now.getDate() - 1
      ]
    },
    
    // 格式化显示日期
    formatDisplayDate(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
      const weekDay = weekDays[date.getDay()]
      return `${year}-${month}-${day} ${weekDay}`
    },
    
    // 格式化日期为 YYYY-MM-DD
    formatDate(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    
    // 日期选择器变化
    onPickerChange(e) {
      this.pickerValue = e.detail.value
    },
    
    // 确认选择日期
    confirmDate() {
      const year = this.years[this.pickerValue[0]]
      const month = this.months[this.pickerValue[1]] - 1
      const day = this.days[this.pickerValue[2]]
      this.selectedDate = new Date(year, month, day)
      this.showDatePicker = false
      this.loadRecord()
    },
    
    // 切换症状
    toggleSymptom(s) {
      const idx = this.symptoms.indexOf(s)
      if (idx > -1) {
        this.symptoms.splice(idx, 1)
      } else {
        this.symptoms.push(s)
      }
    },
    
    // 加载记录
    async loadRecord() {
      this.loading = true
      try {
        const res = await api.getTodayRecord()
        if (res) {
          this.weight = res.weight || ''
          this.symptoms = res.symptoms || []
          this.mood = res.mood || 'good'
        }
      } catch (error) {
        console.error('加载记录失败:', error)
        // 加载失败时保持默认值，不显示错误提示
      } finally {
        this.loading = false
      }
    },
    
    // 查看趋势
    viewChart() {
      uni.navigateTo({
        url: '/pages/record/chart'
      })
    },
    
    // 保存记录
    async save() {
      const record = {
        weight: this.weight,
        symptoms: this.symptoms,
        mood: this.mood
      }
      // 调用 API 保存（如果有的话）
      uni.showToast({ title: '保存成功', icon: 'success' })
    }
  }
}
</script>

<style scoped>
.container {
  padding: 20rpx;
  background: #f8f8f8;
  min-height: 100vh;
}

.section {
  padding: 0 10rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

/* 日期选择器样式 */
.date-selector {
  margin-bottom: 30rpx;
}

.date-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date-label {
  font-size: 28rpx;
  color: #666;
}

.date-value {
  display: flex;
  align-items: center;
}

.date-text {
  font-size: 30rpx;
  color: #FF6B9D;
  font-weight: 500;
}

.date-arrow {
  font-size: 24rpx;
  color: #FF6B9D;
  margin-left: 10rpx;
}

/* 日期选择器弹窗 */
.date-picker-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
}

.date-picker-popup {
  width: 100%;
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  overflow: hidden;
}

.picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 30rpx;
  border-bottom: 1rpx solid #eee;
}

.picker-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.picker-cancel {
  font-size: 28rpx;
  color: #999;
}

.picker-confirm {
  font-size: 28rpx;
  color: #FF6B9D;
  font-weight: 500;
}

.picker-view {
  height: 400rpx;
}

.picker-item {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  color: #333;
}

/* 记录项样式 */
.record-item {
  display: flex;
  flex-direction: column;
}

.label {
  font-weight: bold;
  margin-bottom: 16rpx;
  font-size: 28rpx;
  color: #333;
}

.record-item input {
  width: 100%;
  height: 80rpx;
  border: 2rpx solid #eee;
  border-radius: 12rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.symptom-list, .mood-list {
  display: flex;
  flex-wrap: wrap;
}

.symptom, .mood {
  padding: 12rpx 24rpx;
  margin: 8rpx;
  border-radius: 30rpx;
  background: #f5f5f5;
  font-size: 26rpx;
  transition: all 0.2s;
}

.symptom.active {
  background: #FF6B9D;
  color: #fff;
}

.mood.active {
  background: #FFE4E9;
  transform: scale(1.1);
}

.mood {
  font-size: 40rpx;
}

.trend-btn {
  margin-top: 20rpx;
  background: #fff;
  color: #FF6B9D;
  border: 2rpx solid #FF6B9D;
  border-radius: 40rpx;
  font-size: 28rpx;
}

.save-btn {
  margin-top: 20rpx;
  background: #FF6B9D;
  color: #fff;
  border-radius: 40rpx;
  font-size: 28rpx;
}

.save-btn[disabled] {
  background: #ccc;
}
</style>