// pages/record/chart.js
Page({
  data: {
    weights: [],
    avgWeight: 0,
    maxWeight: 0,
    minWeight: 0
  },

  onLoad() {
    this.loadWeightData()
  },

  loadWeightData() {
    // 模拟数据（后续对接真实 API）
    const mockData = [
      { date: '03-20', weight: 58.5 },
      { date: '03-25', weight: 59.0 },
      { date: '03-30', weight: 59.5 },
      { date: '04-01', weight: 59.8 }
    ]
    
    const weights = mockData.map(d => d.weight)
    this.setData({
      weights: mockData,
      avgWeight: (weights.reduce((a, b) => a + b) / weights.length).toFixed(1),
      maxWeight: Math.max(...weights),
      minWeight: Math.min(...weights)
    })
  }
})