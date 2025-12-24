import axios from 'axios'

// Test script to verify API response format
async function testAPI() {
  try {
    const stockCode = '588200'
    const response = await axios.get(`http://localhost:8000/api/stock/kline-enhanced/${stockCode}`, {
      params: { period: 'daily' }
    })
    
    console.log('=== API Response Structure ===')
    console.log('Keys:', Object.keys(response.data))
    console.log('\n=== K-line Data ===')
    console.log('Count:', response.data.kline?.length)
    console.log('First item:', response.data.kline?.[0])
    console.log('Last item:', response.data.kline?.[response.data.kline.length - 1])
    
    console.log('\n=== RSI Data ===')
    console.log('Count:', response.data.rsi?.length)
    console.log('First item:', response.data.rsi?.[0])
    console.log('Last item:', response.data.rsi?.[response.data.rsi.length - 1])
    
    console.log('\n=== MA5 Data ===')
    console.log('Count:', response.data.ma5?.length)
    console.log('First item:', response.data.ma5?.[0])
    
    console.log('\n=== Volume Data ===')
    console.log('Count:', response.data.volume?.length)
    console.log('First item:', response.data.volume?.[0])
    
    console.log('\n=== MACD Data ===')
    console.log('MACD Count:', response.data.macd?.length)
    console.log('Signal Count:', response.data.macd_signal?.length)
    console.log('Histogram Count:', response.data.macd_histogram?.length)
    
    console.log('\n=== Markers ===')
    console.log('Count:', response.data.markers?.length)
    console.log('First marker:', response.data.markers?.[0])
    
  } catch (error) {
    console.error('API Error:', error.response?.data || error.message)
  }
}

testAPI()
