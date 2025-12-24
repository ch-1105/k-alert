<template>
  <div class="kline-container">
    <div class="toolbar">
      <el-select v-model="period" placeholder="Period" style="width: 100px" @change="loadData">
        <el-option label="Daily" value="daily" />
        <el-option label="Weekly" value="weekly" />
        <el-option label="Monthly" value="monthly" />
      </el-select>
      
      <div class="backtest-controls">
        <el-input-number v-model="rsiLower" :min="1" :max="49" label="RSI Buy" size="small" />
        <span class="separator">-</span>
        <el-input-number v-model="rsiUpper" :min="51" :max="99" label="RSI Sell" size="small" />
        <el-button type="primary" size="small" @click="runBacktest" :loading="backtestLoading">
          Run Backtest (T+1)
        </el-button>
      </div>
    </div>

    <div class="chart-wrapper" ref="chartContainer"></div>

    <div v-if="backtestResult" class="backtest-stats">
      <h3>Backtest Results (A-Share T+1 Rules)</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="label">Total Return</span>
          <span class="value" :class="backtestResult.return_pct >= 0 ? 'up' : 'down'">
            {{ backtestResult.return_pct.toFixed(2) }}%
          </span>
        </div>
        <div class="stat-item">
          <span class="label">Win Rate</span>
          <span class="value">{{ backtestResult.win_rate.toFixed(2) }}%</span>
        </div>
        <div class="stat-item">
          <span class="label">Max Drawdown</span>
          <span class="value down">{{ backtestResult.max_drawdown.toFixed(2) }}%</span>
        </div>
        <div class="stat-item">
          <span class="label">Total Trades</span>
          <span class="value">{{ backtestResult.total_trades }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { createChart, CandlestickSeries } from 'lightweight-charts'
import api from '../api/stock'

const props = defineProps({
  stockCode: String
})

const period = ref('daily')
const chartContainer = ref(null)
// Use plain variables for chart instances to avoid Vue Proxy issues
let chart = null
let candlestickSeries = null

const rsiLower = ref(30)
const rsiUpper = ref(70)
const backtestLoading = ref(false)
const backtestResult = ref(null)

// Resize observer
let resizeObserver = null

const initChart = () => {
  if (!chartContainer.value) return

  chart = createChart(chartContainer.value, {
    layout: {
      background: { color: '#1a1a1a' },
      textColor: '#DDD',
    },
    grid: {
      vertLines: { color: '#2B2B43' },
      horzLines: { color: '#2B2B43' },
    },
    width: chartContainer.value.clientWidth,
    height: 400,
  })

  // v5 API: use addSeries with CandlestickSeries type
  candlestickSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#ef5350', // Red for China Up
    downColor: '#26a69a', // Green for China Down
    borderVisible: false,
    wickUpColor: '#ef5350',
    wickDownColor: '#26a69a',
  })
  
  resizeObserver = new ResizeObserver(entries => {
    if (entries.length === 0 || entries[0].target !== chartContainer.value) { return }
    const newRect = entries[0].contentRect
    chart.applyOptions({ width: newRect.width })
  })
  resizeObserver.observe(chartContainer.value)
}

const loadData = async () => {
  if (!props.stockCode) return
  
  try {
    const res = await api.getKline(props.stockCode, period.value)
    
    // Response format: { kline: [...], markers: [...] }
    const klineData = res.data.kline.sort((a, b) => new Date(a.time) - new Date(b.time))
    const markers = res.data.markers
    
    if (candlestickSeries) {
        candlestickSeries.setData(klineData)
        if (markers && markers.length > 0) {
            candlestickSeries.setMarkers(markers)
        } else {
            candlestickSeries.setMarkers([])
        }
    }
  } catch (e) {
    console.error("Failed to load chart data", e)
  }
}

const runBacktest = async () => {
    backtestLoading.value = true
    try {
        const res = await api.runBacktest({
            stock_code: props.stockCode,
            rsi_lower: rsiLower.value,
            rsi_upper: rsiUpper.value,
            period: period.value
        })
        backtestResult.value = res.data
    } catch (e) {
        console.error(e)
    } finally {
        backtestLoading.value = false
    }
}

onMounted(() => {
    initChart()
    loadData()
})

onUnmounted(() => {
    if (chart) {
        chart.remove()
    }
    if (resizeObserver) {
        resizeObserver.disconnect()
    }
})

watch(() => props.stockCode, () => {
    backtestResult.value = null
    loadData()
})
</script>

<style scoped>
.kline-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  height: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.backtest-controls {
    display: flex;
    align-items: center;
    gap: 8px;
}

.separator {
    color: #888;
}

.chart-wrapper {
    width: 100%;
    height: 400px; /* fixed height for now */
    border: 1px solid #333;
}

.backtest-stats {
    background: #1e1e1e;
    padding: 15px;
    border-radius: 8px;
}

.backtest-stats h3 {
    margin-top: 0;
    margin-bottom: 15px;
    font-size: 1rem;
    color: #ddd;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 15px;
}

.stat-item {
    display: flex;
    flex-direction: column;
}

.label {
    font-size: 0.8rem;
    color: #888;
}

.value {
    font-size: 1.1rem;
    font-weight: bold;
    color: #ddd;
}

.up { color: #ef5350; }
.down { color: #26a69a; }
</style>
