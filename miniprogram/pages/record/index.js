// pages/record/index.js
const app = getApp()

Page({
  data: {
    today: '',
    weight: '',
    symptoms: [],
    mood: 'good',
    symptomOptions: ['孕吐', '疲劳', '水肿', '便秘', '失眠', '食欲不振'],
    moods: [
      {value: 'great', emoji: '😊'},
      {value: 'good', emoji: '🙂'},
      {value: 'normal', emoji: '😐'},
      {value: 'bad', emoji: '😔'}
    ],
    saved: false
  },

  onLoad() {
    const d = new Date()
    this.setData({
      today: `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`
    })
    this.loadTodayRecord()
  },

  loadTodayRecord() {
    wx.request({
      url: app.globalData.baseUrl + '/record/today',
      method: 'GET',
      success: (res) => {
        if (res.statusCode === 200 && res.data) {
          this.setData({
            weight: res.data.weight || '',
            symptoms: res.data.symptoms || [],
            mood: res.data.mood || 'good'
          })
        }
      }
    })
  },

  onWeight(e) {
    this.setData({ weight: e.detail.value })
  },

  toggleSymptom(e) {
    const s = e.currentTarget.dataset.symptom
    let symptoms = [...this.data.symptoms]
    const idx = symptoms.indexOf(s)
    if (idx > -1) {
      symptoms.splice(idx, 1)
    } else {
      symptoms.push(s)
    }
    this.setData({ symptoms })
  },

  setMood(e) {
    this.setData({ mood: e.currentTarget.dataset.mood })
  },

  save() {
    const data = {
      weight: parseFloat(this.data.weight) || 0,
      symptoms: this.data.symptoms,
      mood: this.data.mood,
      date: new Date().toISOString().split('T')[0]
    }

    wx.request({
      url: app.globalData.baseUrl + '/record/',
      method: 'POST',
      data: data,
      success: (res) => {
        if (res.statusCode === 200) {
          wx.showToast({ title: '保存成功', icon: 'success' })
          this.setData({ saved: true })
        } else {
          wx.showToast({ title: '保存失败', icon: 'none' })
        }
      },
      fail: () => {
        wx.showToast({ title: '网络错误', icon: 'none' })
      }
    })
  },

  goChart() {
    wx.navigateTo({ url: '/pages/record/chart' })
  }
})