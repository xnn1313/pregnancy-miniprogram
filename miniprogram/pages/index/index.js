// pages/index/index.js
const app = getApp()

Page({
  data: {
    week: 15,
    stage: '孕中期',
    dueDate: '2026-07-15',
    recipes: []
  },

  onLoad() {
    this.loadRecipes()
  },

  loadRecipes() {
    wx.request({
      url: app.globalData.baseUrl + '/recipes/list?page_size=3',
      method: 'GET',
      success: (res) => {
        console.log('API响应:', res)
        if (res.statusCode === 200 && res.data) {
          this.setData({ recipes: res.data.recipes || [] })
        } else {
          console.error('状态码异常:', res.statusCode)
        }
      },
      fail: (err) => {
        console.error('请求失败:', err)
        wx.showToast({ title: '网络错误', icon: 'none' })
      }
    })
  },

  goRecipe(e) {
    wx.navigateTo({
      url: '/pages/recipe/detail?id=' + e.currentTarget.dataset.id
    })
  }
})