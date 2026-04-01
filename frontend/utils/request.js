// API 请求封装
// 生产环境使用服务器地址
const BASE_URL = 'http://47.108.129.71:8088/api/v1'

// 请求拦截
function request(options) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          uni.showToast({ title: '请求失败', icon: 'none' })
          reject(res)
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      }
    })
  })
}

// API 方法
export const api = {
  // 认证相关
  login: (data) => request({ url: '/auth/login', method: 'POST', data }),
  register: (data) => request({ url: '/auth/register', method: 'POST', data }),
  getMe: () => request({ url: '/auth/me' }),
  logout: () => request({ url: '/auth/logout', method: 'POST' }),
  
  // 家庭/孕周相关
  getArchive: () => request({ url: '/family/archive' }),
  createArchive: (data) => request({ url: '/family/archive', method: 'POST', data }),
  
  // 食谱相关
  getRecipes: (params) => request({ url: '/recipes/list', data: params }),
  getRecipeDetail: (id) => request({ url: `/recipes/${id}` }),
  searchRecipes: (query) => request({ url: '/recipes/search', data: { query } }),
  
  // 营养相关
  searchFood: (query) => request({ url: '/nutrition/search', data: { query } }),
  calculateNutrition: (data) => request({ url: '/nutrition/calculate', method: 'POST', data }),
  
  // 禁忌检查
  checkSafety: (data) => request({ url: '/recipes/safety-check', method: 'POST', data }),
  
  // 收藏相关
  addFavorite: (recipeId) => request({ url: '/recipes/favorite', method: 'POST', data: { recipe_id: recipeId } }),
  getFavorites: () => request({ url: '/recipes/favorites' }),
  removeFavorite: (recipeId) => request({ url: `/recipes/favorite/${recipeId}`, method: 'DELETE' }),
  
  // 推荐相关
  getTodayRecommend: (week) => request({ url: '/recommend/today', data: { week } }),
  
  // 记录相关
  saveRecord: (data) => request({ url: '/record/', method: 'POST', data }),
  getTodayRecord: () => request({ url: '/record/today' }),
  getRecordHistory: (page = 1) => request({ url: '/record/history', data: { page } })
}

export default api