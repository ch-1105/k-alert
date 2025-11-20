import { createRouter, createWebHistory } from 'vue-router'
import StockList from '../views/StockList.vue'
import NotificationSettings from '../views/NotificationSettings.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
