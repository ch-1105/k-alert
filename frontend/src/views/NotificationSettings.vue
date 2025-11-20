<template>
  <div class="notify-settings">
    <h2>Notification Settings</h2>
    <el-form :model="form" label-width="120px">
      <el-form-item label="Email">
        <el-input v-model="form.email" />
      </el-form-item>
      <el-form-item label="Telegram ID">
        <el-input v-model="form.telegram_id" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSave">Save</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/stock'
import { ElMessage } from 'element-plus'

const form = ref({
  email: '',
  telegram_id: ''
})

const loadSettings = async () => {
  try {
    const res = await api.getNotifySettings()
    if (res.data) {
      form.value = res.data
    }
  } catch (e) {
    console.error(e)
  }
}

const onSave = async () => {
  try {
    await api.updateNotifySettings(form.value)
    ElMessage.success('Settings updated')
  } catch (e) {
    ElMessage.error('Failed to update')
  }
}

onMounted(loadSettings)
</script>
