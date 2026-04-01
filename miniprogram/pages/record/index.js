// pages/record/index.js
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
    ]
  },

  onLoad() {
    const d = new Date()
    this.setData({
      today: `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`
    })
  },

  onWeight(e) {
    this.setData({ weight: e.detail.value })
  },

  toggleSymptom(e) {
    const s = e.currentTarget.dataset.symptom
    const symptoms = [...this.data.symptoms]
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
    wx.showToast({ title: '保存成功', icon: 'success' })
  }
})