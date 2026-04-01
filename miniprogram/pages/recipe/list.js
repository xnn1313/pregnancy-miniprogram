// pages/recipe/list.js
const app = getApp()

Page({
  data: {
    keyword: '',
    activeTab: 0,
    recipes: []
  },

  onLoad() {
    this.loadRecipes()
  },

  async loadRecipes(trimester) {
    let url = app.globalData.baseUrl + '/recipes/list'
    if (trimester) url += '?trimester=' + trimester
    
    try {
      const res = await wx.request({ url, method: 'GET' })
      this.setData({ recipes: res.data.recipes || [] })
    } catch (e) {
      console.error(e)
    }
  },

  filter(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
    this.loadRecipes(tab || null)
  },

  goDetail(e) {
    wx.navigateTo({
      url: '/pages/recipe/detail?id=' + e.currentTarget.dataset.id
    })
  }
})