<template>
  <el-form :model="form" label-width="120px">
    <el-form-item label="RSI Low">
      <el-input-number v-model="form.rsi_low" :min="0" :max="100" />
    </el-form-item>
    <el-form-item label="RSI High">
      <el-input-number v-model="form.rsi_high" :min="0" :max="100" />
    </el-form-item>
    <el-form-item label="RSI Period">
      <el-select v-model="form.rsi_period" placeholder="Select Period">
        <el-option label="30 Minutes" value="30" />
        <el-option label="60 Minutes" value="60" />
        <el-option label="Daily" value="daily" />
      </el-select>
    </el-form-item>
    <el-form-item label="RSI Length">
      <el-input-number v-model="form.rsi_length" :min="2" :max="100" />
    </el-form-item>
    <el-form-item label="Enable Push">
      <el-switch v-model="form.enable_push" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="onSave">Save</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import api from '../api/stock'
import { ElMessage } from 'element-plus'

const props = defineProps(['stockCode'])
const emit = defineEmits(['saved'])

const form = ref({
  stock_code: '',
  rsi_low: 30,
  rsi_high: 70,
  rsi_period: 'daily',
  rsi_length: 14,
  enable_push: true
})

const loadStrategy = async () => {
  if (!props.stockCode) return
  try {
    const res = await api.getStrategy(props.stockCode)
    form.value = { ...res.data, stock_code: props.stockCode }
  } catch (e) {
    console.error(e)
  }
}

const onSave = async () => {
  try {
    await api.updateStrategy(form.value)
    ElMessage.success('Strategy updated')
    emit('saved')
  } catch (e) {
    ElMessage.error('Failed to update')
  }
}

watch(() => props.stockCode, loadStrategy)
onMounted(loadStrategy)
</script>
