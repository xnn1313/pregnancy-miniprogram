// app.js
App({
  onLaunch() {
    console.log('小程序启动')
  },
  globalData: {
    userInfo: null,
    baseUrl: 'http://47.108.129.71:8088/api/v1'
  }
})