// pages/mine/index.js
const app = getApp()

Page({
  data: {
    user: { name: '孕妈妈', role: 'owner' },
    isLoggedIn: false
  },

  onShow() {
    this.checkLogin()
  },

  checkLogin() {
    const token = wx.getStorageSync('token')
    this.setData({ isLoggedIn: !!token })
    
    if (token) {
      this.loadUserInfo()
    }
  },

  loadUserInfo() {
    wx.request({
      url: app.globalData.baseUrl + '/auth/me',
      method: 'GET',
      header: { 'Authorization': 'Bearer ' + wx.getStorageSync('token') },
      success: (res) => {
        if (res.statusCode === 200) {
          this.setData({ user: res.data })
        }
      }
    })
  },

  goArchive() {
    wx.showModal({
      title: '孕期档案',
      content: '功能开发中，敬请期待',
      showCancel: false
    })
  },

  goMembers() {
    wx.showModal({
      title: '家庭成员',
      content: '功能开发中，敬请期待',
      showCancel: false
    })
  },

  goSettings() {
    wx.showModal({
      title: '提醒设置',
      content: '功能开发中，敬请期待',
      showCancel: false
    })
  },

  goFavorites() {
    wx.navigateTo({ url: '/pages/recipe/favorites' })
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出吗？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          this.setData({ isLoggedIn: false, user: { name: '未登录', role: 'owner' } })
          wx.showToast({ title: '已退出', icon: 'success' })
        }
      }
    })
  }
})