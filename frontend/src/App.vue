<template>
  <div class="common-layout">
    <el-container>
      <el-header height="60px">
        <div class="nav-container">
          <div class="logo">
            <span class="logo-icon">📈</span>
            <span class="logo-text">K-Alert</span>
          </div>
          <el-menu
            :default-active="activeIndex"
            mode="horizontal"
            router
            :ellipsis="false"
          >
            <el-menu-item index="/">Dashboard</el-menu-item>
            <el-menu-item index="/notify">Settings</el-menu-item>
          </el-menu>
        </div>
      </el-header>
      <el-main>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = ref(route.path)

watch(() => route.path, (newPath) => {
  activeIndex.value = newPath
})
</script>

<style scoped>
.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  margin-right: 40px;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-color);
  user-select: none;
}

.logo-icon {
  margin-right: 10px;
}

.logo-text {
  background: linear-gradient(45deg, #409eff, #36cfc9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.el-menu {
  flex-grow: 1;
  border-bottom: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
