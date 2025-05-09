<script setup lang="ts">
import ChatAgent from './components/ChatAgent.vue';
import Live2D from './components/live2D.vue'; // 保持大寫開頭以符合組件命名慣例
</script>

<template>
    <div id="app-container">
        <Live2D class="live2d-panel"></Live2D>
        <ChatAgent class="chat-panel"></ChatAgent>
    </div>
</template>

<style scoped>
#app-container {
    display: flex;
    /* 使用 Flexbox 佈局 */
    width: 100vw;
    /* 佔滿整個視窗寬度 */
    height: 100vh;
    /* 佔滿整個視窗高度 */
    overflow: hidden;
    /* 防止內容溢出導致滾動條 */
    background-color: #2c3e50;
    /* 深色背景，類似圖片中的效果 */
}

.live2d-panel {
    flex: 1;
    /* Live2D 佔據可用空間的一份 */
    /* 您可以調整 flex-basis 或 width 來更精確控制寬度，例如 flex: 0 0 60%; */
    display: flex;
    /* 內部也使用 flex 以便於對齊 canvas */
    justify-content: center;
    align-items: center;
    position: relative;
    /* 確保 canvas 的 absolute 定位是相對於此容器 */
    /* background-color: #1e272e; */
    /* 左側面板的背景色 (可選) */
}

.chat-panel {
    flex: 1;
    /* 聊天界面佔據可用空間的一份 */
    /* 您可以調整 flex-basis 或 width 來更精確控制寬度，例如 flex: 0 0 40%; */
    display: flex;
    /* 確保 ChatAgent 組件能正確填充 */
    flex-direction: column;
    /* ChatAgent 內部是垂直排列的 */
    /* background-color: #34495e; */
    /* 右側面板的背景色 (可選) */
    padding: 20px;
    /* 給聊天面板一些內邊距 */
    box-sizing: border-box;
    /* 內邊距和邊框不會增加元素的總寬度和高度 */
}
</style>