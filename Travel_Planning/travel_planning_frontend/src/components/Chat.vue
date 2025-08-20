<template>
  <div class="chat-container">
    <div class="chat-history" ref="chatHistory">
      <div v-for="(message, index) in messages" :key="index" :class="['message-wrapper', message.role]">
        <div class="message-bubble">
          <p v-html="formatMessage(message.content)"></p>
        </div>
      </div>
      <div v-if="isLoading" class="message-wrapper assistant">
        <div class="message-bubble loading-bubble">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-input-area">
      <textarea
        v-model="userInput"
        @keydown.enter.prevent="sendMessage"
        placeholder="例如: 我现在在湖南长沙，需要去黄山，给我推荐一下怎么去以及旅游方案"
      ></textarea>
      <button @click="sendMessage" :disabled="isLoading || !userInput.trim()">
        <i class="mdi mdi-send"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';

const messages = ref([]);
const userInput = ref('');
const isLoading = ref(false);
const chatHistory = ref(null);

const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
    }
  });
};

const formatMessage = (content) => {
  // 简单的 markdown 格式化，将换行符替换为 <br>
  return content.replace(/\n/g, '<br>');
};

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  const query = userInput.value;
  messages.value.push({ role: 'user', content: query });
  userInput.value = '';
  isLoading.value = true;
  scrollToBottom();

  const assistantMessage = { role: 'assistant', content: '' };
  messages.value.push(assistantMessage);

  try {
    const response = await fetch('http://127.0.0.1:8000/api/plan/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (!response.body) {
      throw new Error("Response body is null");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      assistantMessage.content += chunk;
      scrollToBottom();
    }

  } catch (error) {
    console.error('Error fetching stream:', error);
    assistantMessage.content = '抱歉，连接服务器时出错，请稍后再试。';
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};
</script>

<style scoped>
/* (样式代码见下一部分) */
</style>