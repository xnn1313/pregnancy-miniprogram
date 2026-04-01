<template>
  <view class="container">
    <!-- 孕周卡片 -->
    <view class="card">
      <view class="pregnancy-info">
        <text class="week">孕 {{ week }} 周</text>
        <text class="stage">{{ stage }}</text>
      </view>
      <view class="due-date">预产期：{{ dueDate }}</view>
    </view>

    <!-- 今日推荐 -->
    <view class="section">
      <text class="section-title">今日推荐</text>
      <view class="recipe-list">
        <view class="recipe-item card" v-for="item in recipes" :key="item.id">
          <text class="recipe-name">{{ item.name }}</text>
          <text class="recipe-benefit">{{ item.benefits[0] }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { api } from '@/utils/request.js'

export default {
  data() {
    return {
      week: 15,
      stage: '孕中期',
      dueDate: '2026-07-15',
      recipes: [],
      loading: true
    }
  },
  async onLoad() {
    try {
      const recommend = await api.getRecommend(15)  // 获取推荐
      const recipes = await api.getRecipes({ page_size: 3 })  // 获取食谱
      this.recipes = recipes.recipes || []
    } catch (e) {
      console.error('加载数据失败', e)
    } finally {
      this.loading = false
    }
  }
}
</script>

<style scoped>
.pregnancy-info {
  display: flex;
  align-items: baseline;
}
.week {
  font-size: 48rpx;
  font-weight: bold;
  color: #FF6B9D;
}
.stage {
  margin-left: 16rpx;
  color: #999;
}
.due-date {
  margin-top: 16rpx;
  color: #666;
}
.section-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
}
.recipe-name {
  font-weight: bold;
}
.recipe-benefit {
  display: block;
  margin-top: 8rpx;
  color: #999;
  font-size: 24rpx;
}
</style>