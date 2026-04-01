<template>
  <view class="container">
    <!-- 加载状态 -->
    <view class="loading" v-if="loading">
      <text>加载中...</text>
    </view>

    <!-- 食谱详情 -->
    <view class="recipe-detail" v-if="!loading && recipe">
      <!-- 头部信息 -->
      <view class="header card">
        <text class="name">{{ recipe.name }}</text>
        <view class="meta">
          <text class="category">{{ recipe.category }}</text>
          <text class="trimester">{{ trimesterText }}</text>
          <text class="difficulty">{{ recipe.difficulty }}</text>
        </view>
        <view class="time-info">
          <text class="prep-time">准备时间：{{ recipe.prep_time }}分钟</text>
        </view>
      </view>

      <!-- 孕期益处 -->
      <view class="benefits card">
        <text class="section-title">孕期益处</text>
        <view class="benefit-tags">
          <text class="tag benefit" v-for="b in recipe.benefits" :key="b">{{ b }}</text>
        </view>
      </view>

      <!-- 关键营养亮点 -->
      <view class="nutrition card">
        <text class="section-title">关键营养亮点</text>
        <view class="nutrition-grid">
          <view class="nutrition-item" v-for="(value, key) in recipe.nutrition_highlight" :key="key">
            <text class="nutrition-name">{{ key }}</text>
            <text class="nutrition-value">{{ value }}{{ getUnit(key) }}</text>
          </view>
        </view>
      </view>

      <!-- 食材列表 -->
      <view class="ingredients card">
        <text class="section-title">食材清单</text>
        <view class="ingredient-list">
          <view class="ingredient-item" v-for="(item, index) in recipe.ingredients" :key="index">
            <text class="ingredient-name">{{ item.name }}</text>
            <text class="ingredient-amount">{{ item.amount }}{{ item.unit || 'g' }}</text>
          </view>
        </view>
      </view>

      <!-- 制作步骤 -->
      <view class="steps card">
        <text class="section-title">制作步骤</text>
        <view class="step-list">
          <view class="step-item" v-for="(step, index) in recipe.steps" :key="index">
            <text class="step-num">{{ index + 1 }}</text>
            <text class="step-content">{{ step }}</text>
          </view>
        </view>
      </view>

      <!-- 禁忌提示 -->
      <view class="warnings card" v-if="recipe.warnings && recipe.warnings.length > 0">
        <text class="section-title warning-title">⚠️ 注意事项</text>
        <view class="warning-list">
          <text class="warning-text" v-for="w in recipe.warnings" :key="w">{{ w }}</text>
        </view>
      </view>
    </view>

    <!-- 底部操作按钮 -->
    <view class="bottom-actions" v-if="!loading && recipe">
      <view class="action-btn" :class="{ done: isDone }" @click="toggleDone">
        <text class="action-icon">{{ isDone ? '✓' : '○' }}</text>
        <text class="action-text">{{ isDone ? '已做过' : '标记已做' }}</text>
      </view>
      <view class="action-btn" :class="{ favorite: isFavorite }" @click="toggleFavorite">
        <text class="action-icon">{{ isFavorite ? '♥' : '♡' }}</text>
        <text class="action-text">{{ isFavorite ? '已收藏' : '收藏' }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { api } from '@/utils/request.js'

export default {
  data() {
    return {
      loading: true,
      recipe: null,
      recipeId: '',
      isDone: false,
      isFavorite: false
    }
  },
  computed: {
    trimesterText() {
      if (!this.recipe) return ''
      const map = { 1: '孕早期', 2: '孕中期', 3: '孕晚期' }
      return map[this.recipe.trimester] || ''
    }
  },
  async onLoad(options) {
    this.recipeId = options.id
    await this.loadRecipeDetail()
    this.loadUserStatus()
  },
  methods: {
    async loadRecipeDetail() {
      try {
        this.loading = true
        const res = await api.getRecipeDetail(this.recipeId)
        this.recipe = res
      } catch (e) {
        uni.showToast({ title: '加载失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },
    async loadUserStatus() {
      // 从本地存储读取用户状态
      const doneList = uni.getStorageSync('recipe_done_list') || []
      const favoriteList = uni.getStorageSync('recipe_favorite_list') || []
      this.isDone = doneList.includes(this.recipeId)
      this.isFavorite = favoriteList.includes(this.recipeId)
      
      // 同时尝试从服务器获取收藏状态
      try {
        const favorites = await api.getFavorites()
        if (Array.isArray(favorites) && favorites.includes(this.recipeId)) {
          this.isFavorite = true
        }
      } catch (e) {
        // 服务器请求失败，使用本地状态
      }
    },
    getUnit(key) {
      // 根据营养素返回单位
      const units = {
        '叶酸': 'μg',
        '铁': 'mg',
        '钙': 'mg',
        '蛋白质': 'g',
        '膳食纤维': 'g',
        '维生素C': 'mg',
        '维生素A': 'μg',
        '维生素D': 'μg',
        'DHA': 'mg',
        '碘': 'μg',
        '热量': 'kcal'
      }
      return units[key] || 'g'
    },
    toggleDone() {
      let doneList = uni.getStorageSync('recipe_done_list') || []
      if (this.isDone) {
        doneList = doneList.filter(id => id !== this.recipeId)
        this.isDone = false
        uni.showToast({ title: '已取消标记', icon: 'none' })
      } else {
        doneList.push(this.recipeId)
        this.isDone = true
        uni.showToast({ title: '已标记完成', icon: 'success' })
      }
      uni.setStorageSync('recipe_done_list', doneList)
    },
    async toggleFavorite() {
      let favoriteList = uni.getStorageSync('recipe_favorite_list') || []
      if (this.isFavorite) {
        favoriteList = favoriteList.filter(id => id !== this.recipeId)
        this.isFavorite = false
        uni.showToast({ title: '已取消收藏', icon: 'none' })
        // 同步到服务器
        try {
          await api.removeFavorite(this.recipeId)
        } catch (e) {
          // 忽略服务器错误
        }
      } else {
        favoriteList.push(this.recipeId)
        this.isFavorite = true
        uni.showToast({ title: '已收藏', icon: 'success' })
        // 同步到服务器
        try {
          await api.addFavorite(this.recipeId)
        } catch (e) {
          // 忽略服务器错误
        }
      }
      uni.setStorageSync('recipe_favorite_list', favoriteList)
    }
  }
}
</script>

<style scoped>
.container {
  padding: 20rpx;
  padding-bottom: 120rpx;
}

.loading {
  padding: 100rpx;
  text-align: center;
  color: #999;
}

/* 头部信息 */
.header {
  padding: 30rpx;
}

.name {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.meta {
  display: flex;
  margin-top: 16rpx;
}

.meta text {
  margin-right: 16rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.category {
  background: #FFE4E1;
  color: #FF6B9D;
}

.trimester {
  background: #E8F5E9;
  color: #4CAF50;
}

.difficulty {
  background: #FFF3E0;
  color: #FF9800;
}

.time-info {
  margin-top: 12rpx;
  font-size: 26rpx;
  color: #666;
}

/* 通用卡片样式 */
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 16rpx;
}

/* 孕期益处 */
.benefit-tags {
  display: flex;
  flex-wrap: wrap;
}

.tag.benefit {
  display: inline-block;
  padding: 8rpx 16rpx;
  margin: 8rpx 8rpx 0 0;
  background: #FFF0F5;
  color: #FF6B9D;
  border-radius: 20rpx;
  font-size: 24rpx;
}

/* 关键营养亮点 */
.nutrition-grid {
  display: flex;
  flex-wrap: wrap;
}

.nutrition-item {
  width: 50%;
  padding: 16rpx;
  display: flex;
  justify-content: space-between;
  border-bottom: 1rpx solid #f0f0f0;
}

.nutrition-name {
  color: #666;
  font-size: 26rpx;
}

.nutrition-value {
  color: #FF6B9D;
  font-weight: bold;
  font-size: 26rpx;
}

/* 食材列表 */
.ingredient-list {
  border-radius: 12rpx;
}

.ingredient-item {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.ingredient-item:last-child {
  border-bottom: none;
}

.ingredient-name {
  color: #333;
  font-size: 28rpx;
}

.ingredient-amount {
  color: #FF6B9D;
  font-size: 26rpx;
}

/* 制作步骤 */
.step-list {
  padding: 0;
}

.step-item {
  display: flex;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.step-item:last-child {
  border-bottom: none;
}

.step-num {
  width: 40rpx;
  height: 40rpx;
  line-height: 40rpx;
  text-align: center;
  background: #FF6B9D;
  color: #fff;
  border-radius: 50%;
  font-size: 24rpx;
  margin-right: 16rpx;
}

.step-content {
  flex: 1;
  color: #333;
  font-size: 28rpx;
  line-height: 1.6;
}

/* 禁忌提示 */
.warnings {
  background: #FFF8E1;
  border: 1rpx solid #FFE082;
}

.warning-title {
  color: #FF8F00;
}

.warning-list {
  padding: 16rpx;
  background: #FFFDE7;
  border-radius: 12rpx;
}

.warning-text {
  color: #FF6F00;
  font-size: 26rpx;
  line-height: 1.6;
}

/* 底部操作按钮 */
.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  background: #fff;
  padding: 20rpx 30rpx;
  border-top: 1rpx solid #eee;
  box-shadow: 0 -4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx;
  margin: 0 10rpx;
  background: #f5f5f5;
  border-radius: 40rpx;
}

.action-btn.done {
  background: #E8F5E9;
}

.action-btn.favorite {
  background: #FFF0F5;
}

.action-icon {
  font-size: 32rpx;
  margin-right: 8rpx;
}

.action-btn.done .action-icon {
  color: #4CAF50;
}

.action-btn.favorite .action-icon {
  color: #FF6B9D;
}

.action-text {
  font-size: 28rpx;
  color: #333;
}
</style>