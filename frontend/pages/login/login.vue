<template>
  <view class="login-container">
    <view class="login-header">
      <image class="logo" src="/static/logo.png" mode="aspectFit" />
      <text class="title">孕期记录</text>
      <text class="subtitle">陪伴您度过美好的孕期时光</text>
    </view>

    <!-- 微信授权登录 -->
    <button 
      class="wx-login-btn" 
      open-type="getPhoneNumber"
      @getphonenumber="onGetPhoneNumber"
    >
      <image class="wx-icon" src="/static/wechat.png" mode="aspectFit" />
      <text>微信一键登录</text>
    </button>

    <!-- 分割线 -->
    <view class="divider">
      <view class="line"></view>
      <text class="text">或</text>
      <view class="line"></view>
    </view>

    <!-- 手机号登录 -->
    <view class="phone-login">
      <input 
        class="phone-input" 
        type="number" 
        placeholder="请输入手机号" 
        v-model="phoneNumber"
        maxlength="11"
      />
      <view class="code-row">
        <input 
          class="code-input" 
          type="number" 
          placeholder="验证码" 
          v-model="verifyCode"
          maxlength="6"
        />
        <button 
          class="code-btn" 
          :disabled="countdown > 0"
          @click="sendCode"
        >
          {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
        </button>
      </view>
      <button class="login-btn" @click="phoneLogin">登录</button>
    </view>

    <!-- 协议 -->
    <view class="agreement">
      <text>登录即代表同意</text>
      <text class="link" @click="viewAgreement('user')">《用户协议》</text>
      <text>和</text>
      <text class="link" @click="viewAgreement('privacy')">《隐私政策》</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      phoneNumber: '',
      verifyCode: '',
      countdown: 0,
      timer: null
    }
  },
  methods: {
    // 微信获取手机号
    async onGetPhoneNumber(e) {
      if (e.detail.errMsg !== 'getPhoneNumber:ok') {
        uni.showToast({ title: '授权失败', icon: 'none' })
        return
      }
      
      uni.showLoading({ title: '登录中...' })
      
      try {
        // 调用后端接口，用 code 换取手机号和用户信息
        const res = await this.$http.post('/api/auth/wx-phone', {
          code: e.detail.code
        })
        
        // 存储用户信息
        uni.setStorageSync('token', res.data.token)
        uni.setStorageSync('userInfo', res.data.userInfo)
        
        uni.hideLoading()
        uni.showToast({ title: '登录成功', icon: 'success' })
        
        // 跳转首页
        setTimeout(() => {
          uni.switchTab({ url: '/pages/index/index' })
        }, 1000)
      } catch (err) {
        uni.hideLoading()
        uni.showToast({ title: err.message || '登录失败', icon: 'none' })
      }
    },
    
    // 发送验证码
    async sendCode() {
      if (!this.validatePhone()) {
        uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
        return
      }
      
      try {
        await this.$http.post('/api/auth/send-code', {
          phone: this.phoneNumber
        })
        
        uni.showToast({ title: '验证码已发送', icon: 'success' })
        
        // 开始倒计时
        this.countdown = 60
        this.timer = setInterval(() => {
          this.countdown--
          if (this.countdown <= 0) {
            clearInterval(this.timer)
          }
        }, 1000)
      } catch (err) {
        uni.showToast({ title: err.message || '发送失败', icon: 'none' })
      }
    },
    
    // 手机号登录
    async phoneLogin() {
      if (!this.validatePhone()) {
        uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
        return
      }
      
      if (!this.verifyCode || this.verifyCode.length !== 6) {
        uni.showToast({ title: '请输入6位验证码', icon: 'none' })
        return
      }
      
      uni.showLoading({ title: '登录中...' })
      
      try {
        const res = await this.$http.post('/api/auth/phone-login', {
          phone: this.phoneNumber,
          code: this.verifyCode
        })
        
        // 存储用户信息
        uni.setStorageSync('token', res.data.token)
        uni.setStorageSync('userInfo', res.data.userInfo)
        
        uni.hideLoading()
        uni.showToast({ title: '登录成功', icon: 'success' })
        
        // 跳转首页
        setTimeout(() => {
          uni.switchTab({ url: '/pages/index/index' })
        }, 1000)
      } catch (err) {
        uni.hideLoading()
        uni.showToast({ title: err.message || '登录失败', icon: 'none' })
      }
    },
    
    // 验证手机号
    validatePhone() {
      return /^1[3-9]\d{9}$/.test(this.phoneNumber)
    },
    
    // 查看协议
    viewAgreement(type) {
      uni.navigateTo({
        url: `/pages/webview/index?type=${type}`
      })
    }
  },
  
  onUnload() {
    if (this.timer) {
      clearInterval(this.timer)
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  padding: 120rpx 60rpx;
  background: linear-gradient(180deg, #FFE4E9 0%, #FFFFFF 40%);
}

.login-header {
  text-align: center;
  margin-bottom: 80rpx;
}

.logo {
  width: 160rpx;
  height: 160rpx;
  margin-bottom: 24rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #FF6B9D;
  margin-bottom: 12rpx;
}

.subtitle {
  display: block;
  font-size: 26rpx;
  color: #999;
}

/* 微信登录 */
.wx-login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 88rpx;
  background: #07C160;
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  border: none;
}

.wx-login-btn::after {
  border: none;
}

.wx-icon {
  width: 40rpx;
  height: 40rpx;
  margin-right: 16rpx;
}

/* 分割线 */
.divider {
  display: flex;
  align-items: center;
  margin: 48rpx 0;
}

.divider .line {
  flex: 1;
  height: 1rpx;
  background: #eee;
}

.divider .text {
  padding: 0 24rpx;
  font-size: 26rpx;
  color: #999;
}

/* 手机号登录 */
.phone-login {
  width: 100%;
}

.phone-input,
.code-input {
  width: 100%;
  height: 88rpx;
  padding: 0 32rpx;
  background: #f8f8f8;
  border-radius: 44rpx;
  font-size: 30rpx;
  box-sizing: border-box;
}

.code-row {
  display: flex;
  margin-top: 24rpx;
}

.code-input {
  flex: 1;
  margin-right: 20rpx;
}

.code-btn {
  width: 220rpx;
  height: 88rpx;
  background: #fff;
  border: 2rpx solid #FF6B9D;
  border-radius: 44rpx;
  color: #FF6B9D;
  font-size: 28rpx;
  padding: 0;
}

.code-btn[disabled] {
  border-color: #ccc;
  color: #ccc;
}

.login-btn {
  width: 100%;
  height: 88rpx;
  background: #FF6B9D;
  border-radius: 44rpx;
  color: #fff;
  font-size: 32rpx;
  margin-top: 32rpx;
  border: none;
}

.login-btn::after {
  border: none;
}

/* 协议 */
.agreement {
  position: fixed;
  bottom: 60rpx;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 24rpx;
  color: #999;
}

.agreement .link {
  color: #FF6B9D;
}
</style>