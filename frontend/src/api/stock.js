import apiClient from './client';

export default {
  getStocks() {
    return apiClient.get('/stock/list');
  },
  addStock(stock) {
    return apiClient.post('/stock/add', stock);
  },
  deleteStock(stockCode) {
    return apiClient.delete(`/stock/delete/${stockCode}`);
  },
  getStrategy(stockCode) {
    return apiClient.get(`/strategy/${stockCode}`);
  },
  updateStrategy(strategy) {
    return apiClient.post('/strategy/update', strategy);
  },
  getNotifySettings() {
    return apiClient.get('/user/notify/');
  },
  updateNotifySettings(settings) {
    return apiClient.post('/user/notify/update', settings);
  }
};
