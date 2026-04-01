<template>
  <view class="container">
    <!-- 用户信息 -->
    <view class="user-card card">
      <image class="avatar" src="/static/avatar.png" mode="aspectFill" />
      <view class="info">
        <text class="name">{{ user.name || '未登录' }}</text>
        <text class="role">{{ user.role === 'owner' ? '孕妈妈' : '准爸爸' }}</text>
      </view>
    </view>

    <!-- 菜单 -->
    <view class="menu card">
      <view class="menu-item" @click="goArchive">
        <text>孕期档案</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="goMembers">
        <text>家庭成员</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="goSettings">
        <text>提醒设置</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="goAbout">
        <text>关于我们</text>
        <text class="arrow">›</text>
      </view>
    </view>

    <!-- 退出登录 -->
    <button v-if="isLoggedIn" class="logout-btn" @click="logout">退出登录</button>
  </view>
</template>

<script>
export default {
  data() {
    return {
      user: {
        name: '',
        role: 'owner'
      },
      isLoggedIn: false
    }
  },
  onShow() {
    this.checkLoginStatus()
  },
  methods: {
    checkLoginStatus() {
      const token = uni.getStorageSync('token')
      const userInfo = uni.getStorageSync('userInfo')
      this.isLoggedIn = !!token
      if (userInfo) {
        this.user = userInfo
      }
    },
    goArchive() { uni.showToast({ title: '开发中', icon: 'none' }) },
    goMembers() { uni.showToast({ title: '开发中', icon: 'none' }) },
    goSettings() { uni.showToast({ title: '开发中', icon: 'none' }) },
    goAbout() { uni.showToast({ title: '开发中', icon: 'none' }) },
    
    logout() {
      uni.showModal({
        title: '提示',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            // 清除登录状态
            uni.removeStorageSync('token')
            uni.removeStorageSync('userInfo')
            
            // 重置用户数据
            this.user = { name: '', role: 'owner' }
            this.isLoggedIn = false
            
            uni.showToast({ title: '已退出登录', icon: 'success' })
            
            // 跳转到登录页
            setTimeout(() => {
              uni.redirectTo({ url: '/pages/login/login' })
            }, 1000)
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.user-card {
  display: flex;
  align-items: center;
}
.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: #FFE4E9;
}
.info {
  margin-left: 24rpx;
}
.name {
  display: block;
  font-weight: bold;
  font-size: 32rpx;
}
.role {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #999;
}
.menu-item {
  display: flex;
  justify-content: space-between;
  padding: 24rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}
.menu-item:last-child {
  border-bottom: none;
}
.arrow {
  color: #ccc;
  font-size: 32rpx;
}

.logout-btn {
  width: 100%;
  height: 88rpx;
  background: #fff;
  border: 2rpx solid #FF6B9D;
  border-radius: 44rpx;
  color: #FF6B9D;
  font-size: 32rpx;
  margin-top: 60rpx;
}

.logout-btn::after {
  border: none;
}
</style>