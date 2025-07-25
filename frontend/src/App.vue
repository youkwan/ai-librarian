<script setup lang="ts">
import { ref } from 'vue';
import ChatAgent from './components/ChatAgent.vue';
import Live2D from './components/live2D.vue';

// 定義當前 Live2D 模型的狀態，預設為 'Hiyori'
const currentLive2DModel = ref('Hiyori');
</script>

<template>
    <div id="app-container">
        <!-- 將 currentLive2DModel 作為 prop 傳遞給 Live2D -->
        <Live2D class="live2d-panel" :model-name="currentLive2DModel">
        </Live2D>

        <!-- 傳遞 prop 並監聽來自 ChatAgent 的更新事件 -->
        <ChatAgent class="chat-panel" :current-live2D-model="currentLive2DModel"
            @update:live2d-model="newModel => currentLive2DModel = newModel">
        </ChatAgent>
    </div>
</template>

<style scoped>
#app-container {
    display: flex;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    background-color: #2c3e50;
}

.live2d-panel {
    flex-shrink: 0;
    width: 60vw;
    display: flex;
    /* 將內容靠左對齊 */
    justify-content: flex-start;
    align-items: center;
    position: relative;
}

.chat-panel {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    padding: 20px;
    box-sizing: border-box;
}
</style>
