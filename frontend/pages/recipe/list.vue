<template>
  <view class="container">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <input v-model="keyword" placeholder="搜索食谱或食材" @confirm="search" />
    </view>

    <!-- 筛选 -->
    <view class="filter">
      <view :class="['filter-item', activeTrimester === 0 ? 'active' : '']" @click="filterByTrimester(0)">全部</view>
      <view :class="['filter-item', activeTrimester === 1 ? 'active' : '']" @click="filterByTrimester(1)">孕早期</view>
      <view :class="['filter-item', activeTrimester === 2 ? 'active' : '']" @click="filterByTrimester(2)">孕中期</view>
      <view :class="['filter-item', activeTrimester === 3 ? 'active' : '']" @click="filterByTrimester(3)">孕晚期</view>
    </view>

    <!-- 食谱列表 -->
    <view class="recipe-list">
      <view class="recipe-card card" v-for="item in recipes" :key="item.id" @click="goDetail(item.id)">
        <text class="name">{{ item.name }}</text>
        <view class="tags">
          <text class="tag" v-for="b in item.benefits.slice(0,2)" :key="b">{{ b }}</text>
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
      keyword: '',
      activeTrimester: 0,
      recipes: []
    }
  },
  async onLoad() {
    await this.loadRecipes()
  },
  methods: {
    async loadRecipes() {
      const params = {}
      if (this.activeTrimester > 0) params.trimester = this.activeTrimester
      const res = await api.getRecipes(params)
      this.recipes = res.recipes || []
    },
    async search() {
      if (this.keyword) {
        const res = await api.searchRecipes(this.keyword)
        this.recipes = res.recipes || []
      } else {
        await this.loadRecipes()
      }
    },
    async filterByTrimester(t) {
      this.activeTrimester = t
      await this.loadRecipes()
    },
    goDetail(id) {
      uni.navigateTo({ url: `/pages/recipe/detail?id=${id}` })
    }
  }
}
</script>

<style scoped>
.search-bar input {
  background: #fff;
  padding: 20rpx;
  border-radius: 16rpx;
}
.filter {
  display: flex;
  margin: 20rpx 0;
}
.filter-item {
  padding: 10rpx 20rpx;
  margin-right: 16rpx;
  border-radius: 30rpx;
  background: #fff;
  font-size: 26rpx;
}
.filter-item.active {
  background: #FF6B9D;
  color: #fff;
}
.name {
  font-weight: bold;
  font-size: 30rpx;
}
.tags {
  margin-top: 12rpx;
}
.tag {
  display: inline-block;
  padding: 4rpx 12rpx;
  margin-right: 8rpx;
  background: #FFF0F5;
  color: #FF6B9D;
  border-radius: 8rpx;
  font-size: 22rpx;
}
</style>