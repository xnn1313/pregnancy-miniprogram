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
    
    // 只有 1/2/3 才是有效的 trimester 值
    if (trimester && trimester > 0) {
      url += '?trimester=' + trimester
    }
    
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
    // tab=0 表示"全部"，不传 trimester 参数
    this.loadRecipes(tab > 0 ? tab : null)
  },

  goDetail(e) {
    wx.navigateTo({
      url: '/pages/recipe/detail?id=' + e.currentTarget.dataset.id
    })
  }
})