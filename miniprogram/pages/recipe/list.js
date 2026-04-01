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

  loadRecipes(trimester) {
    let url = app.globalData.baseUrl + '/recipes/list'
    if (trimester) url += '?trimester=' + trimester
    
    wx.request({
      url: url,
      method: 'GET',
      success: (res) => {
        console.log('食谱列表响应:', res)
        if (res.statusCode === 200 && res.data) {
          this.setData({ recipes: res.data.recipes || [] })
        } else {
          console.error('状态码异常:', res.statusCode)
          this.setData({ recipes: [] })
        }
      },
      fail: (err) => {
        console.error('请求失败:', err)
        wx.showToast({ title: '网络错误', icon: 'none' })
        this.setData({ recipes: [] })
      }
    })
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