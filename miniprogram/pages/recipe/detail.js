// pages/recipe/detail.js
const app = getApp()

Page({
  data: {
    recipe: null,
    loading: true
  },

  onLoad(options) {
    if (options.id) {
      this.loadRecipe(options.id)
    }
  },

  loadRecipe(id) {
    wx.request({
      url: app.globalData.baseUrl + '/recipes/' + id,
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200 && res.data) {
          this.setData({ recipe: res.data, loading: false })
        } else {
          wx.showToast({ title: '食谱不存在', icon: 'none' })
          setTimeout(() => wx.navigateBack(), 1500)
        }
      },
      fail: () => {
        wx.showToast({ title: '网络错误', icon: 'none' })
        this.setData({ loading: false })
      }
    })
  },

  markDone() {
    wx.showToast({ title: '已标记为已做', icon: 'success' })
  },

  toggleFavorite() {
    wx.showToast({ title: '已收藏', icon: 'success' })
  }
})