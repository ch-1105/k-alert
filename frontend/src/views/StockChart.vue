<template>
  <div class="chart-page">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" circle>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h2>{{ stockCode }} - {{ stockName }}</h2>
      </div>
      <div class="header-right">
        <div class="controls-group">
          <el-select v-model="period" placeholder="Period" style="width: 120px" @change="loadData">
            <el-option label="1分钟" value="1" />
            <el-option label="5分钟" value="5" />
            <el-option label="15分钟" value="15" />
            <el-option label="30分钟" value="30" />
            <el-option label="60分钟" value="60" />
            <el-option label="日线" value="daily" />
            <el-option label="周线" value="weekly" />
            <el-option label="月线" value="monthly" />
          </el-select>
          
          <el-divider direction="vertical" />
          
          <div class="indicator-toggles">
            <span class="toggle-label">指标:</span>
            <el-checkbox v-model="showMA" @change="toggleMA">MA</el-checkbox>
            <el-checkbox v-model="showBOLL" @change="toggleBOLL">BOLL</el-checkbox>
            <el-checkbox v-model="showVolume" @change="toggleVolume">成交量</el-checkbox>
            <el-checkbox v-model="showRSI" @change="toggleRSI">RSI</el-checkbox>
            <el-checkbox v-model="showMACD" @change="toggleMACD">MACD</el-checkbox>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-container" style="position: relative;">
      <!-- Floating Legend for OHLCV -->
      <div v-show="showLegend" class="chart-legend" :style="legendStyle">
        <div class="legend-time">{{ hoverData.time }}</div>
        <div class="legend-row">
          <span class="label">开:</span><span class="value">{{ formatValue(hoverData.open) }}</span>
          <span class="label">高:</span><span class="value up">{{ formatValue(hoverData.high) }}</span>
          <span class="label">低:</span><span class="value down">{{ formatValue(hoverData.low) }}</span>
          <span class="label">收:</span><span class="value" :class="getPriceClass(hoverData.close, hoverData.open)">{{ formatValue(hoverData.close) }}</span>
        </div>
        <div class="legend-row">
          <span class="label">量:</span><span class="value">{{ formatVolume(hoverData.volume) }}</span>
        </div>
      </div>

      <!-- Main Chart -->
      <div class="main-chart" ref="mainChartContainer"></div>
      
      <!-- Volume Chart -->
      <div v-show="showVolume" class="volume-chart" ref="volumeChartContainer"></div>
      
      <!-- RSI Chart -->
      <div v-show="showRSI" class="rsi-chart" ref="rsiChartContainer"></div>
      
      <!-- MACD Chart -->
      <div v-show="showMACD" class="macd-chart" ref="macdChartContainer"></div>
    </div>

    <div class="indicators-panel">
      <el-card style="margin-top: 20px;">
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>回测工具 (T+1)</span>
            <el-button type="primary" size="small" @click="runBacktest" :loading="backtestLoading">
              运行回测
            </el-button>
          </div>
        </template>
        <div class="backtest-controls">
          <el-form :inline="true">
            <el-form-item label="买入RSI">
              <el-input-number v-model="rsiLower" :min="1" :max="49" size="small" />
            </el-form-item>
            <el-form-item label="卖出RSI">
              <el-input-number v-model="rsiUpper" :min="51" :max="99" size="small" />
            </el-form-item>
          </el-form>
        </div>

        <div v-if="backtestResult" class="backtest-stats">
          <div class="stats-grid">
            <div class="stat-item">
              <span class="label">总收益率</span>
              <span class="value" :class="backtestResult.return_pct >= 0 ? 'up' : 'down'">
                {{ backtestResult.return_pct.toFixed(2) }}%
              </span>
            </div>
            <div class="stat-item">
              <span class="label">胜率</span>
              <span class="value">{{ backtestResult.win_rate.toFixed(2) }}%</span>
            </div>
            <div class="stat-item">
              <span class="label">最大回撤</span>
              <span class="value down">{{ backtestResult.max_drawdown.toFixed(2) }}%</span>
            </div>
            <div class="stat-item">
              <span class="label">交易次数</span>
              <span class="value">{{ backtestResult.total_trades }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createChart, CandlestickSeries, LineSeries, HistogramSeries, createSeriesMarkers } from 'lightweight-charts'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '../api/stock'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const stockCode = computed(() => route.params.stockCode)
const stockName = ref('')
const period = ref('daily')

// Tooltip/Legend state
const showLegend = ref(false)
const hoverData = ref({
  time: '',
  open: null,
  high: null,
  low: null,
  close: null,
  volume: null
})
const legendStyle = ref({
  position: 'absolute',
  left: '10px',
  top: '10px',
  zIndex: 10,
  pointerEvents: 'none'
})

let hoverTimer = null
const HOVER_DELAY = 100 // User's preferred small delay

const formatChartTime = (time) => {
  if (!time) return '--';
  
  if (typeof time === 'number') {
    // Intraday: format with Shanghai time
    return new Date(time * 1000).toLocaleString('zh-CN', {
      timeZone: 'Asia/Shanghai',
      hour12: false,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } else if (typeof time === 'object' && time.year) {
    // BusinessDay object: { year, month, day }
    return `${time.year}-${String(time.month).padStart(2, '0')}-${String(time.day).padStart(2, '0')}`;
  }
  
  // Already a string or other format
  return String(time);
};

const formatValue = (val) => val ? val.toFixed(2) : '--'
const formatVolume = (val) => {
  if (!val) return '--'
  if (val > 100000000) return (val / 100000000).toFixed(2) + '亿'
  if (val > 10000) return (val / 10000).toFixed(2) + '万'
  return val.toString()
}
const getPriceClass = (close, open) => {
  if (!close || !open) return ''
  return close >= open ? 'up' : 'down'
}

// Chart containers
const mainChartContainer = ref(null)
const volumeChartContainer = ref(null)
const rsiChartContainer = ref(null)
const macdChartContainer = ref(null)

// Chart instances
let mainChart = null
let volumeChart = null
let rsiChart = null
let macdChart = null

let candlestickSeries = null
let volumeSeries = null
let rsiSeries = null
let macdSeries = null
let macdSignalSeries = null
let macdHistogramSeries = null

// Markers primitive (v5 API)
let candlestickMarkers = null

// MA lines
let ma5Series = null
let ma10Series = null
let ma20Series = null
let ma60Series = null

// BOLL lines
let bollUpperSeries = null
let bollMidSeries = null
let bollLowerSeries = null

const currentIndicators = ref({
  rsi: null,
  ma5: null,
  ma10: null,
  ma20: null,
  ma60: null,
  boll_upper: null,
  boll_mid: null,
  boll_lower: null
})

// Indicator visibility toggles (RSI default on, others off)
const showMA = ref(false)
const showBOLL = ref(false)
const showVolume = ref(false)
const showRSI = ref(true)
const showMACD = ref(false)

const rsiLower = ref(30)
const rsiUpper = ref(70)
const backtestLoading = ref(false)
const backtestResult = ref(null)

let resizeObserver = null

const goBack = () => {
  router.push('/')
}

const getRsiClass = (rsi) => {
  if (!rsi) return ''
  if (rsi < 30) return 'rsi-low'
  if (rsi > 70) return 'rsi-high'
  return 'rsi-normal'
}

// Toggle functions
const toggleMA = () => {
  if (showMA.value) {
    // Show MA lines
    if (ma5Series) ma5Series.applyOptions({ visible: true })
    if (ma10Series) ma10Series.applyOptions({ visible: true })
    if (ma20Series) ma20Series.applyOptions({ visible: true })
    if (ma60Series) ma60Series.applyOptions({ visible: true })
  } else {
    // Hide MA lines
    if (ma5Series) ma5Series.applyOptions({ visible: false })
    if (ma10Series) ma10Series.applyOptions({ visible: false })
    if (ma20Series) ma20Series.applyOptions({ visible: false })
    if (ma60Series) ma60Series.applyOptions({ visible: false })
  }
}

const toggleBOLL = () => {
  if (showBOLL.value) {
    if (bollUpperSeries) bollUpperSeries.applyOptions({ visible: true })
    if (bollMidSeries) bollMidSeries.applyOptions({ visible: true })
    if (bollLowerSeries) bollLowerSeries.applyOptions({ visible: true })
  } else {
    if (bollUpperSeries) bollUpperSeries.applyOptions({ visible: false })
    if (bollMidSeries) bollMidSeries.applyOptions({ visible: false })
    if (bollLowerSeries) bollLowerSeries.applyOptions({ visible: false })
  }
}

const toggleVolume = () => {
  if (showVolume.value && volumeChart && volumeChartContainer.value) {
    volumeChart.applyOptions({ width: volumeChartContainer.value.clientWidth })
  }
  if (window.updateTimeScaleVisibility) window.updateTimeScaleVisibility()
}

const toggleRSI = () => {
  if (showRSI.value && rsiChart && rsiChartContainer.value) {
    rsiChart.applyOptions({ width: rsiChartContainer.value.clientWidth })
  }
  if (window.updateTimeScaleVisibility) window.updateTimeScaleVisibility()
}

const toggleMACD = () => {
  if (showMACD.value && macdChart && macdChartContainer.value) {
    macdChart.applyOptions({ width: macdChartContainer.value.clientWidth })
  }
  if (window.updateTimeScaleVisibility) window.updateTimeScaleVisibility()
}

const initCharts = () => {
  const commonOptions = {
    layout: {
      background: { color: '#1a1a1a' },
      textColor: '#DDD',
    },
    grid: {
      vertLines: { color: '#2B2B43' },
      horzLines: { color: '#2B2B43' },
    },
    timeScale: {
      borderColor: '#333',
    },
    rightPriceScale: {
      borderColor: '#333',
    },
    crosshair: {
      mode: 0, // CrosshairMode.Normal
    },
    localization: {
      locale: 'zh-CN',
      timeFormatter: formatChartTime
    }
  }

  // Create helper to define which charts are currently visible
  const visibleCharts = []

  // Main chart
  if (mainChartContainer.value) {
    mainChart = createChart(mainChartContainer.value, {
      ...commonOptions,
      width: mainChartContainer.value.clientWidth,
      height: 400,
      timeScale: {
        ...commonOptions.timeScale,
        visible: false, // Hide X axis for upper charts
      }
    })
    visibleCharts.push(mainChart)

    candlestickSeries = mainChart.addSeries(CandlestickSeries, {
      upColor: '#ef5350',
      downColor: '#26a69a',
      borderVisible: false,
      wickUpColor: '#ef5350',
      wickDownColor: '#26a69a',
    })

    // ... MA and BOLL series remain same ...
    // (keeping them for initialization)
    ma5Series = mainChart.addSeries(LineSeries, { color: '#FF6D00', lineWidth: 1, title: 'MA5', visible: false })
    ma10Series = mainChart.addSeries(LineSeries, { color: '#2196F3', lineWidth: 1, title: 'MA10', visible: false })
    ma20Series = mainChart.addSeries(LineSeries, { color: '#9C27B0', lineWidth: 1, title: 'MA20', visible: false })
    ma60Series = mainChart.addSeries(LineSeries, { color: '#00BCD4', lineWidth: 1, title: 'MA60', visible: false })
    bollUpperSeries = mainChart.addSeries(LineSeries, { color: '#FFC107', lineWidth: 1, lineStyle: 2, title: 'BOLL上', visible: false })
    bollMidSeries = mainChart.addSeries(LineSeries, { color: '#FFC107', lineWidth: 1, title: 'BOLL中', visible: false })
    bollLowerSeries = mainChart.addSeries(LineSeries, { color: '#FFC107', lineWidth: 1, lineStyle: 2, title: 'BOLL下', visible: false })
  }

  // Volume chart
  if (volumeChartContainer.value) {
    volumeChart = createChart(volumeChartContainer.value, {
      ...commonOptions,
      width: volumeChartContainer.value.clientWidth,
      height: 120,
      timeScale: {
        ...commonOptions.timeScale,
        visible: false,
      }
    })
    visibleCharts.push(volumeChart)

    volumeSeries = volumeChart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: { type: 'volume' },
    })
  }

  // RSI chart
  if (rsiChartContainer.value) {
    rsiChart = createChart(rsiChartContainer.value, {
      ...commonOptions,
      width: rsiChartContainer.value.clientWidth,
      height: 120,
      timeScale: {
        ...commonOptions.timeScale,
        visible: false,
      }
    })
    visibleCharts.push(rsiChart)

    rsiSeries = rsiChart.addSeries(LineSeries, {
      color: '#2196F3',
      lineWidth: 2,
    })
  }

  // MACD chart
  if (macdChartContainer.value) {
    macdChart = createChart(macdChartContainer.value, {
      ...commonOptions,
      width: macdChartContainer.value.clientWidth,
      height: 120,
      // MACD is at the bottom by default, but we should make sure the bottom-most visible chart has the timeScale visible
      // We will handle this dynamically in updateTimeScaleVisibility
    })
    visibleCharts.push(macdChart)

    macdHistogramSeries = macdChart.addSeries(HistogramSeries, { color: '#26a69a' })
    macdSeries = macdChart.addSeries(LineSeries, { color: '#2196F3', lineWidth: 1 })
    macdSignalSeries = macdChart.addSeries(LineSeries, { color: '#ef5350', lineWidth: 1 })
  }

  // Function to ensure only the bottom-most chart shows the time scale
  const updateTimeScaleVisibility = () => {
    // Collect all chart objects that correspond to visible containers
    const activeCharts = []
    if (mainChart) activeCharts.push({ chart: mainChart, visible: true }) // Main is always visible
    if (volumeChart) activeCharts.push({ chart: volumeChart, visible: showVolume.value })
    if (rsiChart) activeCharts.push({ chart: rsiChart, visible: showRSI.value })
    if (macdChart) activeCharts.push({ chart: macdChart, visible: showMACD.value })

    const lastVisible = activeCharts.filter(item => item.visible).pop()
    
    activeCharts.forEach(item => {
      item.chart.applyOptions({
        timeScale: { visible: item === lastVisible }
      })
    })
  }

  // Update visibility on initial load and toggles
  updateTimeScaleVisibility()

  // Export functions to use in toggles
  window.updateTimeScaleVisibility = updateTimeScaleVisibility


  // Synchronize all charts
  const charts = [mainChart, volumeChart, rsiChart, macdChart].filter(c => c !== null)
  let isSyncingHorizontal = false

  charts.forEach(chart => {
    // 1. Sync TimeScale (Scroll & Zoom) - Use Logical Range for better stability
    chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
      if (isSyncingHorizontal || !range) return
      
      isSyncingHorizontal = true
      charts.forEach(otherChart => {
        if (otherChart !== chart) {
          otherChart.timeScale().setVisibleLogicalRange(range)
        }
      })
      isSyncingHorizontal = false
    })

    // 2. Sync Crosshair & Tooltip
    chart.subscribeCrosshairMove(param => {
      // Clear existing timer on any move
      if (hoverTimer) {
        clearTimeout(hoverTimer)
        hoverTimer = null
      }

      if (isSyncingHorizontal) return
      
      if (param.time) {
        // Sync vertical line
        charts.forEach(otherChart => {
          if (otherChart !== chart) {
            otherChart.setCrosshairPosition(undefined, param.time, undefined)
          }
        })

        // Find data for tooltip
        const data = param.seriesData.get(candlestickSeries)
        const volData = param.seriesData.get(volumeSeries)
        
        if (data) {
          // Set up a timer to show the legend after HOVER_DELAY
          hoverTimer = setTimeout(() => {
            hoverData.value = {
              time: formatChartTime(param.time),
              open: data.open,
              high: data.high,
              low: data.low,
              close: data.close,
              volume: volData ? volData.value : null
            }
            showLegend.value = true
          }, HOVER_DELAY)
        } else {
          showLegend.value = false
        }
      } else {
        // Clear crosshair and hide legend
        showLegend.value = false
        charts.forEach(otherChart => {
          if (otherChart !== chart) {
            otherChart.clearCrosshairPosition()
          }
        })
      }
    })
  })

  // Setup resize observer
  setupResizeObserver()
}

const setupResizeObserver = () => {
  resizeObserver = new ResizeObserver(entries => {
    if (mainChart && mainChartContainer.value) {
      mainChart.applyOptions({ width: mainChartContainer.value.clientWidth })
    }
    if (volumeChart && volumeChartContainer.value) {
      volumeChart.applyOptions({ width: volumeChartContainer.value.clientWidth })
    }
    if (rsiChart && rsiChartContainer.value) {
      rsiChart.applyOptions({ width: rsiChartContainer.value.clientWidth })
    }
    if (macdChart && macdChartContainer.value) {
      macdChart.applyOptions({ width: macdChartContainer.value.clientWidth })
    }
  })

  if (mainChartContainer.value) resizeObserver.observe(mainChartContainer.value)
}

const loadData = async () => {
  if (!stockCode.value) return

  try {
    console.log('Loading data for:', stockCode.value, 'Period:', period.value)
    
    // Fetch enhanced kline data with indicators
    const res = await axios.get(`http://localhost:8000/api/stock/kline-enhanced/${stockCode.value}`, {
      params: { period: period.value }
    })

    console.log('API Response:', res.data)
    console.log('Kline count:', res.data.kline?.length)
    console.log('RSI count:', res.data.rsi?.length)
    console.log('MA5 count:', res.data.ma5?.length)
    console.log('Volume count:', res.data.volume?.length)

    const data = res.data

    // Update timeScale options based on period type
    const isIntraday = ['1', '5', '15', '30', '60'].includes(period.value)
    const timeScaleOptions = {
      timeVisible: isIntraday,
      secondsVisible: false
    }
    
    if (mainChart) {
      mainChart.applyOptions({
        timeScale: timeScaleOptions
      })
    }
    if (volumeChart) volumeChart.applyOptions({ timeScale: timeScaleOptions })
    if (rsiChart) rsiChart.applyOptions({ timeScale: timeScaleOptions })
    if (macdChart) macdChart.applyOptions({ timeScale: timeScaleOptions })

    // Set candlestick data
    if (candlestickSeries && data.kline) {
      const klineData = data.kline.sort((a, b) => {
        // For timestamps (intraday), compare numerically
        // For date strings, compare as dates
        if (typeof a.time === 'number') {
          return a.time - b.time
        }
        return new Date(a.time) - new Date(b.time)
      })
      
      console.log('Setting kline data, count:', klineData.length)
      console.log('First kline:', klineData[0])
      console.log('Last kline:', klineData[klineData.length - 1])
      candlestickSeries.setData(klineData)
      
      // v5 API: Use createSeriesMarkers instead of series.setMarkers
      if (data.markers && data.markers.length > 0) {
        console.log('Setting markers, count:', data.markers.length)
        if (candlestickMarkers) {
          // Update existing markers
          candlestickMarkers.setMarkers(data.markers)
        } else {
          // Create new markers primitive
          candlestickMarkers = createSeriesMarkers(candlestickSeries, data.markers)
        }
      } else if (candlestickMarkers) {
        // Clear markers if none
        candlestickMarkers.setMarkers([])
      }
      
      // Fit content after setting data
      if (mainChart) {
        mainChart.timeScale().fitContent()
      }
    }

    // Set MA data
    if (data.ma5 && ma5Series) {
      console.log('Setting MA5, count:', data.ma5.length)
      ma5Series.setData(data.ma5)
    }
    if (data.ma10 && ma10Series) {
      console.log('Setting MA10, count:', data.ma10.length)
      ma10Series.setData(data.ma10)
    }
    if (data.ma20 && ma20Series) ma20Series.setData(data.ma20)
    if (data.ma60 && ma60Series) ma60Series.setData(data.ma60)

    // Set BOLL data
    if (data.boll_upper && bollUpperSeries) bollUpperSeries.setData(data.boll_upper)
    if (data.boll_mid && bollMidSeries) bollMidSeries.setData(data.boll_mid)
    if (data.boll_lower && bollLowerSeries) bollLowerSeries.setData(data.boll_lower)

    // Set Volume data
    if (data.volume && volumeSeries) {
      console.log('Setting volume, count:', data.volume.length)
      console.log('First volume item:', data.volume[0])
      volumeSeries.setData(data.volume)
      if (volumeChart) {
        volumeChart.timeScale().fitContent()
      }
    }

    // Set RSI data
    if (data.rsi && rsiSeries) {
      console.log('Setting RSI, count:', data.rsi.length)
      console.log('First RSI item:', data.rsi[0])
      rsiSeries.setData(data.rsi)
      if (rsiChart) {
        rsiChart.timeScale().fitContent()
      }
    }

    // Set MACD data
    if (data.macd && macdSeries) {
      console.log('Setting MACD lines')
      macdSeries.setData(data.macd)
    }
    if (data.macd_signal && macdSignalSeries) macdSignalSeries.setData(data.macd_signal)
    if (data.macd_histogram && macdHistogramSeries) {
      console.log('Setting MACD histogram, count:', data.macd_histogram.length)
      macdHistogramSeries.setData(data.macd_histogram)
      if (macdChart) {
        macdChart.timeScale().fitContent()
      }
    }

    // Update current indicators (last values)
    if (data.rsi && data.rsi.length > 0) {
      const lastIdx = data.rsi.length - 1
      console.log('Updating current indicators, last index:', lastIdx)
      console.log('Last RSI value:', data.rsi[lastIdx])
      
      currentIndicators.value = {
        rsi: data.rsi[lastIdx]?.value || null,
        ma5: data.ma5 && data.ma5.length > 0 ? data.ma5[data.ma5.length - 1]?.value : null,
        ma10: data.ma10 && data.ma10.length > 0 ? data.ma10[data.ma10.length - 1]?.value : null,
        ma20: data.ma20 && data.ma20.length > 0 ? data.ma20[data.ma20.length - 1]?.value : null,
        ma60: data.ma60 && data.ma60.length > 0 ? data.ma60[data.ma60.length - 1]?.value : null,
        boll_upper: data.boll_upper && data.boll_upper.length > 0 ? data.boll_upper[data.boll_upper.length - 1]?.value : null,
        boll_mid: data.boll_mid && data.boll_mid.length > 0 ? data.boll_mid[data.boll_mid.length - 1]?.value : null,
        boll_lower: data.boll_lower && data.boll_lower.length > 0 ? data.boll_lower[data.boll_lower.length - 1]?.value : null,
      }
      console.log('Updated currentIndicators:', currentIndicators.value)
    }

  } catch (e) {
    console.error("Failed to load chart data", e)
    console.error("Error details:", e.response?.data)
  }
}

const runBacktest = async () => {
  backtestLoading.value = true
  try {
    const res = await api.runBacktest({
      stock_code: stockCode.value,
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

onMounted(async () => {
  // Fetch stock name
  try {
    const stocks = await api.getStocks()
    const stock = stocks.data.find(s => s.stock_code === stockCode.value)
    if (stock) {
      stockName.value = stock.stock_name
    }
  } catch (e) {
    console.error(e)
  }

  initCharts()
  loadData()
})

onUnmounted(() => {
  if (mainChart) mainChart.remove()
  if (volumeChart) volumeChart.remove()
  if (rsiChart) rsiChart.remove()
  if (macdChart) macdChart.remove()
  if (resizeObserver) resizeObserver.disconnect()
})

// Watch for period changes
watch(() => period.value, (newPeriod, oldPeriod) => {
  console.log(`Period changed from ${oldPeriod} to ${newPeriod}`)
  loadData()
})
</script>

<style scoped>
.chart-page {
  padding: 20px;
  background: #0a0a0a;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h2 {
  margin: 0;
  color: #fff;
}

.header-right {
  display: flex;
  align-items: center;
}

.controls-group {
  display: flex;
  align-items: center;
  gap: 15px;
}

.indicator-toggles {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-label {
  color: #888;
  font-size: 0.9rem;
  margin-right: 5px;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-bottom: 20px;
  background-color: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  overflow: hidden;
}

.main-chart,
.volume-chart,
.rsi-chart,
.macd-chart {
  border-bottom: 1px solid #2B2B43;
}

.main-chart:last-child,
.volume-chart:last-child,
.rsi-chart:last-child,
.macd-chart:last-child {
  border-bottom: none;
}

.indicators-panel {
  margin-top: 20px;
}

.indicator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.indicator-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.indicator-item .label {
  font-size: 0.85rem;
  color: #888;
}

.indicator-item .value {
  font-size: 1.1rem;
  font-weight: bold;
  color: #ddd;
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

.backtest-controls {
  margin-bottom: 20px;
}

.backtest-stats {
  margin-top: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-item .label {
  font-size: 0.85rem;
  color: #888;
}

.stat-item .value {
  font-size: 1.1rem;
  font-weight: bold;
  color: #ddd;
}

.up {
  color: #ef5350;
}

.down {
  color: #26a69a;
}

.chart-legend {
  padding: 8px 12px;
  background-color: rgba(30, 30, 30, 0.85);
  border: 1px solid #444;
  border-radius: 4px;
  color: #ddd;
  font-size: 0.85rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  min-width: 180px;
  backdrop-filter: blur(4px);
}

.legend-time {
  font-weight: bold;
  border-bottom: 1px solid #444;
  margin-bottom: 4px;
  padding-bottom: 2px;
  font-family: monospace;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  line-height: 1.6;
}

.legend-row .label {
  color: #888;
}

.legend-row .value {
  margin-right: 5px;
  font-family: 'Roboto Mono', monospace;
}
</style>
