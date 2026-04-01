// pages/login/login.js
Page({
  onGetPhoneNumber(e) {
    if (e.detail.code) {
      wx.switchTab({ url: '/pages/index/index' })
    } else {
      wx.showToast({ title: '授权失败', icon: 'none' })
    }
  }
})