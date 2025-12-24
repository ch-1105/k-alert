import { createRouter, createWebHistory } from 'vue-router'
import StockList from '../views/StockList.vue'
import NotificationSettings from '../views/NotificationSettings.vue'
import StockChart from '../views/StockChart.vue'

const routes = [
  {
    path: '/',
    name: 'StockList',
    component: StockList
  },
  {
    path: '/notify',
    name: 'NotificationSettings',
    component: NotificationSettings
  },
  {
    path: '/chart/:stockCode',
    name: 'StockChart',
    component: StockChart
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
