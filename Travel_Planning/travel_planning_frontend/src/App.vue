<template>
  <div id="app-container">
    <header>
      <h1>🚄 智能旅行规划助手</h1>
      <p>您的 AI 旅行规划伙伴</p>
    </header>
    <main>
      <Chat />
    </main>
    <footer>
      © 2025 智能旅行规划系统
    </footer>
  </div>
</template>

<script setup>
import Chat from './components/Chat.vue';
</script>

<style scoped>
#app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f4f6f8;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
header {
  text-align: center;
  padding: 1rem;
  background-color: white;
  border-bottom: 1px solid #e0e0e0;
}
header h1 {
  margin: 0;
  color: #333;
}
header p {
  margin: 0.25rem 0 0;
  color: #666;
}
main {
  flex-grow: 1;
  overflow: hidden;
  display: flex;
  justify-content: center;
  padding: 1rem;
}
footer {
  text-align: center;
  padding: 0.5rem;
  font-size: 0.8rem;
  color: #999;
  background-color: white;
  border-top: 1px solid #e0e0e0;
}
</style>