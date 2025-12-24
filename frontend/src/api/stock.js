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
    return apiClient.get(`/strategies/${stockCode}`);
  },
  updateStrategy(strategy) {
    return apiClient.post('/strategies/update', strategy);
  },
  getNotifySettings() {
    return apiClient.get('/notifications/settings');
  },
  updateNotifySettings(settings) {
    return apiClient.post('/notifications/update', settings);
  },
  getStockMetrics(stockCode) {
    return apiClient.get(`/stock/metrics/${stockCode}`);
  },
  getKline(stockCode, period) {
    return apiClient.get(`/stock/kline/${stockCode}`, { params: { period } });
  },
  runBacktest(data) {
    return apiClient.post('/stock/backtest', data);
  }
};
