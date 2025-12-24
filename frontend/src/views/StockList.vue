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
      <el-card
        v-for="stock in stocks"
        :key="stock.stock_code"
        class="stock-card"
        shadow="hover"
      >
        <div class="card-header">
          <div class="stock-info">
            <span class="stock-name">{{ stock.stock_name }}</span>
            <div class="stock-meta">
              <el-tag
                size="small"
                :type="stock.stock_type === 'etf' ? 'warning' : 'info'"
                effect="plain"
                class="type-tag"
              >
                {{ stock.stock_type === "etf" ? "ETF" : "Stock" }}
              </el-tag>
              <span class="stock-code">{{ stock.stock_code }}</span>
            </div>
          </div>
          <div class="card-actions">
            <el-button circle size="small" @click="handleChart(stock)">
              <el-icon><TrendCharts /></el-icon>
            </el-button>
            <el-button circle size="small" @click="handleEdit(stock)">
              <el-icon><Setting /></el-icon>
            </el-button>
            <el-button
              circle
              size="small"
              type="danger"
              @click="handleDelete(stock)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="card-body">
          <div v-if="metricsLoading[stock.stock_code]" class="metrics-loading">
            <el-icon class="is-loading"><Loading /></el-icon> Loading metrics...
          </div>
          <div v-else-if="metrics[stock.stock_code]" class="metrics-container">
            <div class="price-row">
              <span
                class="price"
                :class="getPriceClass(metrics[stock.stock_code].change_percent)"
              >
                ¥{{ metrics[stock.stock_code].price.toFixed(4) }}
              </span>
              <span
                class="change"
                :class="
                  getChangeClass(metrics[stock.stock_code].change_percent)
                "
              >
                {{ formatChange(metrics[stock.stock_code].change_percent) }}
              </span>
            </div>
            <div v-if="metrics[stock.stock_code].rsi !== null" class="rsi-row">
              <span class="rsi-label"
                >RSI({{ metrics[stock.stock_code].rsi_length }})</span
              >
              <span
                class="rsi-value"
                :class="getRsiClass(metrics[stock.stock_code].rsi)"
              >
                {{ metrics[stock.stock_code].rsi.toFixed(2) }}
              </span>
              <div class="rsi-bar">
                <div
                  class="rsi-fill"
                  :style="{
                    width: metrics[stock.stock_code].rsi + '%',
                    backgroundColor: getRsiColor(metrics[stock.stock_code].rsi),
                  }"
                ></div>
              </div>
            </div>
          </div>
          <div v-else class="metrics-error">
            <el-icon><WarningFilled /></el-icon> Unable to load metrics
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
          <el-input
            v-model="form.stock_code"
            placeholder="e.g. 600519"
            autofocus
          />
        </el-form-item>
        <el-form-item label="Stock Name">
          <el-input
            v-model="form.stock_name"
            placeholder="e.g. Kweichow Moutai"
          />
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
    <el-dialog
      v-model="strategyDialogVisible"
      title="Strategy Settings"
      width="500px"
    >
      <StrategySettings
        :stock-code="currentStock"
        @saved="strategyDialogVisible = false"
      />
    </el-dialog>

    <!-- Chart Analysis Dialog -->
    <el-dialog
      v-model="chartDialogVisible"
      :title="`Analysis: ${currentStock}`"
      width="1000px"
      top="5vh"
    >
      <StockKLine v-if="chartDialogVisible" :stock-code="currentStock" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import api from "../api/stock";
import StrategySettings from "./StrategySettings.vue";
import StockKLine from "../components/StockKLine.vue";
import { ElMessage } from "element-plus";
import {
  Plus,
  Setting,
  Delete,
  Loading,
  WarningFilled,
  TrendCharts,
} from "@element-plus/icons-vue";

const stocks = ref([]);
const form = ref({ stock_code: "", stock_name: "", stock_type: "stock" });
const addDialogVisible = ref(false);
const strategyDialogVisible = ref(false);
const chartDialogVisible = ref(false);
const currentStock = ref("");
const loading = ref(false);
const metrics = ref({}); // Store metrics for each stock
const metricsLoading = ref({}); // Track loading state for each stock

const loadStocks = async () => {
  try {
    const res = await api.getStocks();
    stocks.value = res.data;
    // Load metrics for each stock
    loadAllMetrics();
  } catch (e) {
    console.error(e);
  }
};

const loadAllMetrics = async () => {
  for (const stock of stocks.value) {
    loadMetrics(stock.stock_code);
  }
};

const loadMetrics = async (stockCode) => {
  metricsLoading.value[stockCode] = true;
  try {
    const res = await api.getStockMetrics(stockCode);
    metrics.value[stockCode] = res.data;
  } catch (e) {
    console.error(`Failed to load metrics for ${stockCode}:`, e);
    metrics.value[stockCode] = null;
  } finally {
    metricsLoading.value[stockCode] = false;
  }
};

const getPriceClass = (changePercent) => {
  if (changePercent > 0) return "price-up";
  if (changePercent < 0) return "price-down";
  return "";
};

const getChangeClass = (changePercent) => {
  if (changePercent > 0) return "change-up";
  if (changePercent < 0) return "change-down";
  return "";
};

const formatChange = (changePercent) => {
  const sign = changePercent >= 0 ? "↑" : "↓";
  return `${sign}${Math.abs(changePercent).toFixed(2)}%`;
};

const getRsiClass = (rsi) => {
  if (rsi < 30) return "rsi-low";
  if (rsi > 70) return "rsi-high";
  return "rsi-normal";
};

const getRsiColor = (rsi) => {
  if (rsi < 30) return "#67c23a"; // Green for oversold
  if (rsi > 70) return "#f56c6c"; // Red for overbought
  return "#909399"; // Gray for neutral
};

const onAdd = async () => {
  if (!form.value.stock_code || !form.value.stock_name) {
    ElMessage.warning("Please enter both stock code and name");
    return;
  }
  loading.value = true;
  try {
    await api.addStock(form.value);
    ElMessage.success("Stock added successfully");
    addDialogVisible.value = false;
    form.value = { stock_code: "", stock_name: "", stock_type: "stock" };
    await loadStocks();
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || "Failed to add stock");
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (row) => {
  try {
    await api.deleteStock(row.stock_code);
    ElMessage.success("Stock deleted");
    loadStocks();
  } catch (e) {
    ElMessage.error("Failed to delete stock");
  }
};

const handleEdit = (row) => {
  currentStock.value = row.stock_code;
  strategyDialogVisible.value = true;
};

const handleChart = (row) => {
  currentStock.value = row.stock_code;
  chartDialogVisible.value = true;
};

onMounted(loadStocks);
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

/* Metrics Styles */
.metrics-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metrics-loading,
.metrics-error {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 0.9rem;
}

.price-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.price {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-color);
}

.price-up {
  color: #67c23a;
}

.price-down {
  color: #f56c6c;
}

.change {
  font-size: 1rem;
  font-weight: 500;
}

.change-up {
  color: #67c23a;
}

.change-down {
  color: #f56c6c;
}

.rsi-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rsi-label {
  font-size: 0.85rem;
  color: #909399;
  font-weight: 500;
}

.rsi-value {
  font-size: 1.1rem;
  font-weight: 600;
}

.rsi-low {
  color: #67c23a;
}

.rsi-high {
  color: #f56c6c;
}

.rsi-normal {
  color: #909399;
}

.rsi-bar {
  width: 100%;
  height: 6px;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
  overflow: hidden;
}

.rsi-fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
  border-radius: 3px;
}
</style>
