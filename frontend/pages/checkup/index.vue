<template>
  <view class="container">
    <!-- 加载状态 -->
    <view class="loading-container" v-if="loading">
      <view class="loading-spinner"></view>
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else>
      <!-- 顶部操作栏 -->
      <view class="header">
        <text class="section-title">产检时间线</text>
        <button class="add-btn" @tap="goToCreate">
          <text class="add-icon">+</text>
          <text>新建计划</text>
        </button>
      </view>

      <!-- 空状态 -->
      <view class="empty-state" v-if="checkups.length === 0">
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无产检计划</text>
        <button class="empty-btn" @tap="goToCreate">立即创建</button>
      </view>

      <!-- 时间线列表 -->
      <view class="timeline" v-else>
        <view 
          class="timeline-item" 
          v-for="item in checkups" 
          :key="item.id"
          @tap="goToDetail(item.id)"
        >
          <view class="timeline-line">
            <view class="dot" :class="item.status"></view>
          </view>
          <view class="content card">
            <view class="content-header">
              <text class="title">{{ item.title }}</text>
              <text class="status" :class="item.status">{{ statusText(item.status) }}</text>
            </view>
            <view class="content-info">
              <text class="date">📅 {{ item.date }}</text>
              <text class="weeks" v-if="item.weeks">孕{{ item.weeks}}周</text>
            </view>
            <view class="content-desc" v-if="item.description">
              <text>{{ item.description }}</text>
            </view>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script>
import { api } from '@/utils/request.js'

// 扩展 api 对象，添加产检相关方法
const checkupApi = {
  ...api,
  // 获取产检时间线
  getCheckupTimeline: () => api.request({ url: '/checkup/timeline' }),
  // 获取产检计划列表
  getCheckupPlans: () => api.request({ url: '/checkup/plans' }),
  // 创建产检计划
  createCheckupPlan: (data) => api.request({ url: '/checkup/plan', method: 'POST', data }),
  // 获取产检详情
  getCheckupDetail: (id) => api.request({ url: `/checkup/${id}` })
}

export default {
  data() {
    return {
      loading: false,
      checkups: []
    }
  },
  
  async onLoad() {
    // 模拟数据，后续对接 API
    this.checkups = [
      { id: 1, date: '2026-04-15', title: '唐筛', status: 'pending' },
      { id: 2, date: '2026-05-01', title: '四维', status: 'pending' }
    ]
  },

  onShow() {
    // 页面显示时保持现有数据
  },

  onPullDownRefresh() {
    uni.stopPullDownRefresh()
  },
  
  methods: {
    // 加载产检时间线
    async loadTimeline() {
      this.loading = true
      try {
        const res = await checkupApi.getCheckupTimeline()
        if (res && res.data) {
          this.checkups = res.data
        } else if (Array.isArray(res)) {
          this.checkups = res
        } else {
          // 如果后端暂无数据，使用模拟数据
          this.checkups = this.getMockData()
        }
      } catch (error) {
        console.error('加载产检时间线失败:', error)
        // 加载失败时使用模拟数据
        this.checkups = this.getMockData()
        uni.showToast({
          title: '加载失败，显示示例数据',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },
    
    // 模拟数据
    getMockData() {
      return [
        { id: 1, date: '2026-04-15', title: '孕中期唐筛', status: 'pending', weeks: 16, description: '空腹抽血检查' },
        { id: 2, date: '2026-05-01', title: '四维彩超', status: 'pending', weeks: 20, description: '大排畸检查' },
        { id: 3, date: '2026-06-01', title: '糖耐量测试', status: 'pending', weeks: 24, description: '妊娠期糖尿病筛查' }
      ]
    },
    
    // 状态文本转换
    statusText(status) {
      const map = { 
        pending: '待检', 
        done: '已完成', 
        abnormal: '需复查',
        cancelled: '已取消'
      }
      return map[status] || status
    },
    
    // 跳转到详情页
    goToDetail(id) {
      uni.navigateTo({
        url: `/pages/checkup/detail?id=${id}`
      })
    },
    
    // 跳转到创建页
    goToCreate() {
      uni.navigateTo({
        url: '/pages/checkup/create'
      })
    }
  }
}
</script>

<style scoped>
.container {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 0;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #e0e0e0;
  border-top-color: #FF6B6B;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 20rpx;
  color: #999;
  font-size: 28rpx;
}

/* 顶部操作栏 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
  padding: 0 10rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.add-btn {
  display: flex;
  align-items: center;
  padding: 12rpx 24rpx;
  background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
  border-radius: 40rpx;
  border: none;
  font-size: 26rpx;
  color: #fff;
  line-height: 1.2;
}

.add-btn::after {
  border: none;
}

.add-icon {
  font-size: 32rpx;
  margin-right: 8rpx;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 150rpx 0;
}

.empty-icon {
  font-size: 100rpx;
  margin-bottom: 30rpx;
}

.empty-text {
  color: #999;
  font-size: 30rpx;
  margin-bottom: 40rpx;
}

.empty-btn {
  background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
  color: #fff;
  font-size: 28rpx;
  padding: 20rpx 60rpx;
  border-radius: 40rpx;
  border: none;
}

.empty-btn::after {
  border: none;
}

/* 时间线 */
.timeline {
  padding-left: 10rpx;
}

.timeline-item {
  display: flex;
  margin-bottom: 24rpx;
}

.timeline-line {
  width: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 20rpx;
}

.dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background: #FF9800;
}

.dot.pending {
  background: #FF9800;
}

.dot.done {
  background: #4CAF50;
}

.dot.abnormal {
  background: #F44336;
}

.dot.cancelled {
  background: #9E9E9E;
}

.content {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.05);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.status {
  font-size: 24rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
}

.status.pending {
  background: #FFF3E0;
  color: #FF9800;
}

.status.done {
  background: #E8F5E9;
  color: #4CAF50;
}

.status.abnormal {
  background: #FFEBEE;
  color: #F44336;
}

.status.cancelled {
  background: #ECEFF1;
  color: #607D8B;
}

.content-info {
  display: flex;
  gap: 24rpx;
  margin-bottom: 12rpx;
}

.date, .weeks {
  font-size: 26rpx;
  color: #666;
}

.content-desc {
  font-size: 24rpx;
  color: #999;
  margin-top: 12rpx;
  padding-top: 12rpx;
  border-top: 1rpx solid #f0f0f0;
}

.card:active {
  transform: scale(0.98);
  transition: transform 0.1s;
}
</style>