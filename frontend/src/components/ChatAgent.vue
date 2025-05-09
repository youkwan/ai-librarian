<template>
  <div id="gemini-chat-container">
    <div class="chat-header">
      <div class="header-title">AI 助理</div>
      <div class="status-indicators">
        <span :style="{ color: healthColor, marginRight: '10px', fontSize: '0.85em' }">
          {{ healthStatusText }}
        </span>
        <span class="mode-indicator" @click="toggleAgentMode" :title="`點擊切換到 ${useStreamAgent ? '呼叫模式' : '串流模式'}`">
          {{ agentStatusTextShort }}
        </span>
      </div>
    </div>

    <div id="chatBox" ref="chatBoxRef">
      <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="`message-row-${msg.role}`">
        <div class="message-bubble" :class="`message-bubble-${msg.role}`">
          <div class="message-content">
            <div v-if="msg.role !== 'user' && msg.role !== 'tool'" class="role-name">{{ getRoleDisplayName(msg.role) }}
            </div>
            <div class="text-content" v-html="formatMessageContent(msg.content)"></div>
            <div v-if="msg.role === 'tool'" class="tool-output-indicator">工具執行結果</div>
          </div>
        </div>
      </div>
      <div v-if="isThinking || (currentAssistantMessage && currentAssistantMessage.trim() !== '')"
        class="message-row message-row-assistant">
        <div class="message-bubble message-bubble-assistant">
          <div class="message-content">
            <div class="role-name">{{ getRoleDisplayName('assistant') }}</div>
            <div class="text-content"
              v-html="currentAssistantMessage ? formatMessageContent(currentAssistantMessage) : thinkingDots"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area-container">
      <div class="input-wrapper">
        <textarea ref="userInputRef" v-model="userInput" placeholder="在這裡輸入訊息..." @keydown.enter="handleEnterKey"
          :disabled="isThinking" class="user-input" rows="1" @input="autoGrowTextarea"></textarea>
        <button @click="sendMessage" :disabled="isThinking || !userInput.trim()" class="send-button" title="送出訊息">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue';

const healthStatus = ref('Checking...');
const healthCheckInterval = ref(null);
const messages = ref([]);
const userInput = ref('');
const threadId = ref(null);
const useStreamAgent = ref(true);
const isThinking = ref(false);
const currentAssistantMessage = ref(null);
const chatBoxRef = ref(null);
const userInputRef = ref(null);

const thinkingDots = ref('<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>');
let thinkingInterval;

// 加入工具訊息追蹤
const toolMessageMap = new Map(); // key: tool_name, value: index in messages



// 移除了 onAvatarError，因為不再需要頭像

const formatMessageContent = (content) => {
  if (typeof content !== 'string') return '';
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>');
};

const healthStatusText = computed(() => {
  if (healthStatus.value === 'ok') return '連線狀態：良好';
  if (healthStatus.value === 'error') return '連線狀態：異常';
  return '連線狀態：檢查中';
});

const healthColor = computed(() => {
  if (healthStatus.value === 'ok') return '#1e8e3e';
  if (healthStatus.value === 'error') return '#d93025';
  return '#70757a';
});

const agentStatusTextShort = computed(() => (useStreamAgent.value ? '串流' : '呼叫'));

async function checkHealth() {
  try {
    const res = await fetch("http://localhost:8000/v1/sys/health");
    if (!res.ok) {
      console.warn(`健康檢查失敗，狀態碼: ${res.status}`);
      healthStatus.value = 'error';
      return;
    }
    const data = await res.json();
    healthStatus.value = data.status === "ok" ? 'ok' : 'error';
  } catch (err) {
    console.error("健康檢查請求失敗:", err);
    healthStatus.value = 'error';
  }
}

function getRoleDisplayName(role) {
  switch (role) {
    case 'user': return '您';
    case 'assistant': return 'AI 助理';
    case 'tool': return '工具';
    default: return role.charAt(0).toUpperCase() + role.slice(1);
  }
}

function appendMessage(role, content) {
  if (role === 'assistant' && content.trim() === '' && !currentAssistantMessage.value) {
    return;
  }
  messages.value.push({ role, content });
  scrollToBottom();
}

async function scrollToBottom() {
  await nextTick();
  const chatBox = chatBoxRef.value;
  if (chatBox) {
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

function toggleAgentMode() {
  if (isThinking.value) return;
  useStreamAgent.value = !useStreamAgent.value;
}

const autoGrowTextarea = () => {
  const textarea = userInputRef.value;
  if (textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
  }
};

const handleEnterKey = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isThinking.value) return;

  if (!threadId.value) {
    threadId.value = `thread-${self.crypto.randomUUID()}`;
  }

  appendMessage('user', text);
  userInput.value = '';
  if (userInputRef.value) {
    userInputRef.value.style.height = 'auto';
  }
  isThinking.value = true;
  currentAssistantMessage.value = '';

  let dotCount = 0;
  clearInterval(thinkingInterval);
  thinkingInterval = setInterval(() => {
    dotCount = (dotCount + 1) % 4;
    let dots = '';
    for (let i = 0; i < dotCount; i++) {
      dots += '<span class="dot animate">.</span>';
    }
    if (!currentAssistantMessage.value) {
      thinkingDots.value = dots || '<span class="dot thinking-placeholder-dot">.</span>';
    }
  }, 500);

  const payload = {
    thread_id: threadId.value,
    messages: [
      { role: "system", content: "You are a helpful, creative, and friendly AI assistant, in the style of Gemini." },
      ...messages.value.filter(m => m.role === 'user' || m.role === 'assistant').slice(-10),
      { role: "user", content: text }
    ],
    llm_config: {
      model: "openai:gpt-4o-mini",
      temperature: 0.7,
      max_tokens: 2000,
    }
  };

  try {
    if (useStreamAgent.value) {
      await streamAgentRequest(payload);
    } else {
      await invokeAgentRequest(payload);
    }
  } catch (error) {
    console.error("發送訊息時捕獲到未處理的錯誤:", error);
    appendMessage('assistant', `❌ 糟糕，似乎發生了一些問題：${error.message}`);
  } finally {
    isThinking.value = false;
    clearInterval(thinkingInterval);
    thinkingDots.value = '';
    scrollToBottom();
  }
}

async function invokeAgentRequest(payload) {
  currentAssistantMessage.value = null;
  try {
    const res = await fetch("http://localhost:8000/v1/agents/invoke", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`伺服器錯誤 ${res.status}: ${errorText || res.statusText}`);
    }

    const data = await res.json();
    const assistantMessages = data.messages?.filter(msg => msg.role === "assistant" && msg.content);
    if (assistantMessages && assistantMessages.length > 0) {
      assistantMessages.forEach(msg => appendMessage('assistant', msg.content));
    } else {
      appendMessage('assistant', '(AI 沒有提供回應)');
    }

    if (Array.isArray(data.tools_used)) {
      data.tools_used.forEach(tool => {
        if (tool.name) {
          appendMessage('tool', `工具 '${tool.name}' 已執行。輸出: ${JSON.stringify(tool.tool_output) || '(無輸出)'}`);
        }
      });
    }
  } catch (err) {
    console.error("呼叫 (Invoke) Agent 時出錯:", err);
    appendMessage('assistant', `❌ 呼叫 AI 時發生錯誤： ${err.message}`);
  } finally {
    isThinking.value = false;
    clearInterval(thinkingInterval);
    currentAssistantMessage.value = null;
  }
}

async function streamAgentRequest(payload) {
  let accumulatedAssistantReply = "";

  try {
    const response = await fetch("http://localhost:8000/v1/agents/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`伺服器錯誤 ${response.status}: ${errorText || response.statusText}`);
    }
    if (!response.body) {
      throw new Error("回應 body 為空，無法讀取串流。");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const eventBlock = buffer.substring(0, boundary);
        buffer = buffer.substring(boundary + 2);

        let eventType = "message";
        let eventDataLines = [];

        eventBlock.split("\n").forEach(line => {
          if (line.startsWith("event:")) {
            eventType = line.substring(6).trim();
          } else if (line.startsWith("data:")) {
            eventDataLines.push(line.substring(5).trim());
          }
        });

        const eventData = eventDataLines.join("\n");

        if (eventData) {
          try {
            const jsonData = JSON.parse(eventData);
            processStreamEvent(eventType, jsonData, (delta) => {
              if (isThinking.value && !currentAssistantMessage.value && delta) {
                clearInterval(thinkingInterval);
              }
              currentAssistantMessage.value += delta;
              accumulatedAssistantReply += delta;
              scrollToBottom();
            });
          } catch (err) {
            console.error("❌ JSON 解析錯誤於 data:", eventData, "錯誤:", err, "事件類型:", eventType);
          }
        }
        boundary = buffer.indexOf("\n\n");
      }
    }

    if (accumulatedAssistantReply.trim()) {
      appendMessage('assistant', accumulatedAssistantReply);
    } else if (!messages.value.some(m => m.role === 'assistant' && m.content.trim() !== '')) {
      appendMessage('assistant', '(AI 沒有提供回應)');
    }

  } catch (err) {
    console.error("串流 Agent 請求錯誤:", err);
    appendMessage('assistant', `❌ 串流處理時發生錯誤: ${err.message}`);
  } finally {
    isThinking.value = false;
    clearInterval(thinkingInterval);
    currentAssistantMessage.value = null;
  }
}

function processStreamEvent(eventType, data, onDelta) {
  switch (eventType) {
    case "stream.tool_call.start": {
      const content = `🔧 工具 '${data.tool_name}' 執行中...\n`;
      const msg = { role: "tool", content };
      messages.value.push(msg);
      toolMessageMap.set(data.tool_name, messages.value.length - 1);
      scrollToBottom();
      break;
    }

    case "stream.tool_call.delta": {
      const idx = toolMessageMap.get(data.tool_name);
      if (typeof idx === "number" && data.tool_tokens) {
        messages.value[idx].content += data.tool_tokens;
        scrollToBottom();
      }
      break;
    }

    case "stream.tool_call.completed": {
      const idx = toolMessageMap.get(data.tool_name);
      if (typeof idx === "number") {
        // 用分隔線表示結束
        messages.value[idx].content += `\n🔧 工具 '${data.tool_name}' 執行完成`;
      } else {
        appendMessage("tool", `🔧 工具 '${data.tool_name}' 完成。\n\n輸出: ${data.tool_tokens || '(無)'}`);
      }
      scrollToBottom();
      break;
    }

    case "stream.llm_tokens.delta":
      if (data.llm_tokens) onDelta(data.llm_tokens);
      break;

    case "stream.completed":
      console.log("🏁 Agent 串流完成", data);
      break;

    case "stream.error":
      appendMessage("assistant", `❌ 串流錯誤：${data.error}`);
      break;
  }
}



onMounted(() => {
  checkHealth();
  healthCheckInterval.value = setInterval(checkHealth, 30000);
  autoGrowTextarea();
});

onUnmounted(() => {
  if (healthCheckInterval.value) clearInterval(healthCheckInterval.value);
  clearInterval(thinkingInterval);
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');

:root {
  --gemini-primary-text: #1f1f1f;
  --gemini-secondary-text: #5f6368;
  --gemini-background: #ffffff;
  --gemini-user-message-bg: #e8f0fe;
  --gemini-ai-message-bg: #f8f9fa;
  --gemini-border-color: #dadce0;
  --gemini-input-bg: #f1f3f4;
  --gemini-button-bg: #1a73e8;
  --gemini-button-text: #ffffff;

  --gemini-font-family: 'Roboto', 'Noto Sans TC', sans-serif;
}

#gemini-chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: var(--gemini-background);
  font-family: var(--gemini-font-family);
  color: var(--gemini-primary-text);
  overflow: hidden;
  box-shadow: 0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 2px 6px 2px rgba(60, 64, 67, 0.15);
  border-radius: 8px;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid var(--gemini-border-color);
  background-color: var(--gemini-background);
  flex-shrink: 0;
}

.header-title {
  font-size: 1.1em;
  font-weight: 500;
  color: #3c4043;
}

.status-indicators {
  display: flex;
  align-items: center;
}

.mode-indicator {
  font-size: 0.85em;
  color: var(--gemini-secondary-text);
  background-color: #e8eaed;
  padding: 4px 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.mode-indicator:hover {
  background-color: #dadce0;
}

#chatBox {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scrollbar-width: thin;
  scrollbar-color: var(--gemini-border-color) transparent;
}

#chatBox::-webkit-scrollbar {
  width: 6px;
}

#chatBox::-webkit-scrollbar-thumb {
  background-color: var(--gemini-border-color);
  border-radius: 3px;
}

.message-row {
  display: flex;
  max-width: 85%;
}

.message-row-user {
  justify-content: flex-end;
  margin-left: auto;
}

.message-row-assistant,
.message-row-tool {
  justify-content: flex-start;
  margin-right: auto;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 18px;
  line-height: 1.5;
  display: flex;
  word-break: break-word;
}

.message-bubble-user {
  background-color: var(--gemini-user-message-bg);
  color: #17a69f;
  border-bottom-right-radius: 6px;
}

.message-bubble-assistant {
  background-color: var(--gemini-ai-message-bg);
  color: var(--gemini-primary-text);
  border: 1px solid var(--gemini-border-color);
  border-bottom-left-radius: 6px;
}

.message-bubble-tool {
  background-color: #fef7e0;
  color: #754c00;
  border: 1px solid #fce8b2;
  font-size: 0.9em;
}

.tool-output-indicator {
  font-weight: 500;
  font-size: 0.8em;
  color: #b08800;
  margin-top: 4px;
  border-top: 1px dashed #fce8b2;
  padding-top: 4px;
}



.message-content {
  display: flex;
  flex-direction: column;
}

.role-name {
  font-weight: 500;
  font-size: 0.9em;
  margin-bottom: 4px;
  color: var(--gemini-secondary-text);
}

.text-content {
  font-size: 1em;
  white-space: pre-wrap;
}

.text-content>>>br {
  display: block;
  content: "";
  margin-top: 0.5em;
}

.text-content .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: var(--gemini-secondary-text);
  border-radius: 50%;
  margin: 0 2px;
}

.text-content .dot.animate {
  animation: blink 1.4s infinite both;
}

.text-content .dot.animate:nth-child(2) {
  animation-delay: .2s;
}

.text-content .dot.animate:nth-child(3) {
  animation-delay: .4s;
}

.text-content .thinking-placeholder-dot {
  opacity: 0.5;
}

@keyframes blink {

  0%,
  80%,
  100% {
    opacity: 0;
  }

  40% {
    opacity: 1;
  }
}

.input-area-container {
  padding: 16px 20px;
  border-top: 1px solid var(--gemini-border-color);
  background-color: var(--gemini-background);
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  background-color: var(--gemini-input-bg);
  border-radius: 24px;
  padding: 6px 8px 6px 16px;
  border: 1px solid transparent;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: #9aa0a6;
  box-shadow: 0 0 0 1px #9aa0a6;
}

.user-input {
  flex-grow: 1;
  border: none;
  outline: none;
  padding: 8px 0;
  background-color: transparent;
  color: var(--gemini-primary-text);
  font-family: var(--gemini-font-family);
  font-size: 1em;
  resize: none;
  line-height: 1.5;
  max-height: 150px;
  overflow-y: auto;
}

.user-input::placeholder {
  color: var(--gemini-secondary-text);
  opacity: 0.8;
}

.send-button {
  background-color: transparent;
  border: none;
  color: var(--gemini-secondary-text);
  padding: 8px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
  transition: background-color 0.2s, color 0.2s;
  width: 40px;
  height: 40px;
}

.send-button:hover:not(:disabled) {
  background-color: #e0e0e0;
  color: var(--gemini-button-bg);
}

.send-button:disabled {
  color: #bdc1c6;
  cursor: not-allowed;
}

.send-button:not(:disabled) {
  color: var(--gemini-button-bg);
}

.send-button svg {
  width: 22px;
  height: 22px;
}

.disclaimer {
  font-size: 0.75em;
  color: var(--gemini-secondary-text);
  text-align: center;
  margin-top: 12px;
  padding: 0 10px;
}
</style>