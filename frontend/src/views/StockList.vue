<template>
  <div class="page-container">
    <div class="header-actions">
      <h2>My Watchlist</h2>
      <el-button type="primary" size="large" @click="addDialogVisible = true">
        <el-icon class="el-icon--left"><Plus /></el-icon> Add Stock
      </el-button>
    </div>

    <!-- Stock Cards Grid -->
    <div v-if="stocks.length > 0" class="stock-grid">
      <el-card v-for="stock in stocks" :key="stock.stock_code" class="stock-card" shadow="hover">
        <div class="card-header">
          <div class="stock-info">
            <span class="stock-name">{{ stock.stock_name }}</span>
            <div class="stock-meta">
              <el-tag size="small" :type="stock.stock_type === 'etf' ? 'warning' : 'info'" effect="plain" class="type-tag">
                {{ stock.stock_type === 'etf' ? 'ETF' : 'Stock' }}
              </el-tag>
              <span class="stock-code">{{ stock.stock_code }}</span>
            </div>
          </div>
          <div class="card-actions">
            <el-button circle size="small" @click="handleEdit(stock)">
              <el-icon><Setting /></el-icon>
            </el-button>
            <el-button circle size="small" type="danger" @click="handleDelete(stock)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="card-body">
          <!-- Placeholder for real-time data if available later -->
          <div class="status-indicator">
            <span class="dot"></span> Monitoring
          </div>
        </div>
      </el-card>
    </div>

    <el-empty v-else description="No stocks monitored yet" />

    <!-- Add Stock Dialog -->
    <el-dialog v-model="addDialogVisible" title="Add New Stock" width="400px">
      <el-form :model="form" label-position="top" @submit.prevent="onAdd">
        <el-form-item label="Type">
          <el-radio-group v-model="form.stock_type">
            <el-radio-button label="stock">Stock (A-Share)</el-radio-button>
            <el-radio-button label="etf">ETF / Fund</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Stock Code">
          <el-input v-model="form.stock_code" placeholder="e.g. 600519" autofocus />
        </el-form-item>
        <el-form-item label="Stock Name">
          <el-input v-model="form.stock_name" placeholder="e.g. Kweichow Moutai" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">Cancel</el-button>
          <el-button type="primary" @click="onAdd" :loading="loading">
            Add Stock
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Strategy Settings Dialog -->
    <el-dialog v-model="strategyDialogVisible" title="Strategy Settings" width="500px">
      <StrategySettings :stock-code="currentStock" @saved="strategyDialogVisible = false" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/stock'
import StrategySettings from './StrategySettings.vue'
import { ElMessage } from 'element-plus'
import { Plus, Setting, Delete } from '@element-plus/icons-vue'

const stocks = ref([])
const form = ref({ stock_code: '', stock_name: '', stock_type: 'stock' })
const addDialogVisible = ref(false)
const strategyDialogVisible = ref(false)
const currentStock = ref('')
const loading = ref(false)

const loadStocks = async () => {
  try {
    const res = await api.getStocks()
    stocks.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const onAdd = async () => {
  if (!form.value.stock_code || !form.value.stock_name) {
    ElMessage.warning('Please enter both stock code and name')
    return
  }
  loading.value = true
  try {
    await api.addStock(form.value)
    ElMessage.success('Stock added successfully')
    addDialogVisible.value = false
    form.value = { stock_code: '', stock_name: '', stock_type: 'stock' }
    loadStocks()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || 'Failed to add stock')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await api.deleteStock(row.stock_code)
    ElMessage.success('Stock deleted')
    loadStocks()
  } catch (e) {
    ElMessage.error('Failed to delete stock')
  }
}

const handleEdit = (row) => {
  currentStock.value = row.stock_code
  strategyDialogVisible.value = true
}

onMounted(loadStocks)
</script>

<style scoped>
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.stock-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.stock-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stock-info {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
}

.stock-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.type-tag {
  font-weight: bold;
}

.stock-code {
  font-size: 0.9rem;
  color: #888;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.card-body {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.status-indicator {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: #67c23a;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #67c23a;
  border-radius: 50%;
  margin-right: 8px;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.5);
}
</style>
