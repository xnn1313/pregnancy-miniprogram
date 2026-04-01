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

  async loadRecipes() {
    try {
      const res = await wx.request({
        url: app.globalData.baseUrl + '/recipes/list?page_size=3',
        method: 'GET'
      })
      this.setData({ recipes: res.data.recipes || [] })
    } catch (e) {
      console.error('加载失败', e)
    }
  },

  goRecipe(e) {
    wx.navigateTo({
      url: '/pages/recipe/detail?id=' + e.currentTarget.dataset.id
    })
  }
})