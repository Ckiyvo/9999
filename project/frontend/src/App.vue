<template>
  <div id="app">
    <!-- 顶部固定栏 -->
    <div class="top-bar">
      <h1>面向行业大模型的数据治理系统</h1>
      <div class="top-nav">
        <router-link to="/">首页</router-link>
        <router-link to="/project">项目管理</router-link>
        <router-link to="/user-management">用户管理</router-link>
      </div>
    </div>
    <!-- 右侧内容区域 -->
    <div class="content">
      <router-view :key="$route.fullPath"></router-view>
    </div>
  </div>
</template>

<script>
import HomePage from './components/HomePage.vue'
import ProjectManagement from './components/ProjectManagement.vue'
import UserManagement from './components/UserManagement.vue'

export default {
  name: 'App',
  components: {
    HomePage,
    ProjectManagement,
    UserManagement
  },
  data() {
    return {
      currentPage: 'HomePage'
    }
  }
}
</script>

<style scoped>
#app {
  display: flex;
  height: 100vh;
  margin: 0;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 50px;
  background-color: #f0f9ff;
  color: #333;
  display: flex;
  align-items: center;
  padding: 0 15px;
  z-index: 1;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.top-bar h1 {
  font-size: 14px;
  margin: 0;
  flex: 1;
  text-align: left;
}

.top-nav {
  display: flex;
  gap: 20px;
}

.content {
  margin-top: 50px;
  padding: 0px;
  width: 100%;
}
</style>