<template>
  <div id="input-container">
    <div>
      <strong>狀態：</strong>
      <span :style="{ color: healthColor }">{{ healthStatusText }}</span>
    </div>

    <div>
      <strong>模式：</strong><span>{{ agentStatusText }}</span>
      <button @click="toggleAgentMode">mode</button>
    </div>

    <input type="text" v-model="userInput" placeholder="輸入訊息..." @keydown.enter.prevent="sendMessage"
      :disabled="isThinking" />
    <button @click="sendMessage" :disabled="isThinking">
      {{ isThinking ? '傳送中...' : '送出' }}
    </button>

    <div id="chatBox" ref="chatBoxRef">
      <div v-for="(msg, index) in messages" :key="index" class="message">
        <span :class="msg.role">{{ getRoleDisplayName(msg.role) }}：</span>
        <span class="content">{{ msg.content }}</span>
      </div>
      <div v-if="currentAssistantMessage !== null" class="message">
        <span class="assistant">agent：</span>
        <span class="content">{{ currentAssistantMessage || 'Thinking...' }}</span>
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
const useStreamAgent = ref(false);
const isThinking = ref(false);
const currentAssistantMessage = ref(null);
const chatBoxRef = ref(null);

const healthStatusText = computed(() => {
  if (healthStatus.value === 'ok') return '✅';
  if (healthStatus.value === 'error') return '❌';
  return '檢查中...';
});

const healthColor = computed(() => {
  if (healthStatus.value === 'ok') return 'green';
  if (healthStatus.value === 'error') return 'red';
  return 'grey';
});

const agentStatusText = computed(() => useStreamAgent.value ? 'Stream' : 'Invoke');

async function checkHealth() {
  try {
    const res = await fetch("http://localhost:8000/v1/sys/health");
    const data = await res.json();
    if (res.ok && data.status === "ok") {
      healthStatus.value = 'ok';
    } else {
      healthStatus.value = 'error';
    }
  } catch (err) {
    console.error("檢查失敗:", err);
    healthStatus.value = 'error';
  }
}

function getRoleDisplayName(role) {
  switch (role) {
    case 'user': return 'user';
    case 'assistant': return 'agent';
    case 'tool': return 'tool';
    default: return role;
  }
}

function appendMessage(role, content) {
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
  useStreamAgent.value = !useStreamAgent.value;
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isThinking.value) return;

  if (!threadId.value) {
    threadId.value = `thread-${crypto.randomUUID()}`;
  }

  appendMessage('user', text);
  userInput.value = '';
  isThinking.value = true;
  currentAssistantMessage.value = '';

  const payload = {
    thread_id: threadId.value,
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: text }
    ],
    llm_config: {
      model: "openai:gpt-4o-mini",
      temperature: 1,
      max_tokens: null
    }
  };

  try {
    if (useStreamAgent.value) {
      await streamAgentRequest(payload);
    } else {
      await invokeAgentRequest(payload);
    }
  } catch (error) {
    console.error("發送訊息時出錯:", error);
    appendMessage('assistant', `❌ 錯誤：${error.message}`);
    currentAssistantMessage.value = null;
  } finally {
    isThinking.value = false;
    scrollToBottom();
  }
}

async function invokeAgentRequest(payload) {
  try {
    const res = await fetch("http://localhost:8000/v1/agents/invoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`HTTP 錯誤！ 狀態碼： ${res.status}`);
    }

    const data = await res.json();

    const assistantMessage = data.messages?.slice().reverse().find(msg => msg.role === "assistant");
    if (assistantMessage) {
      appendMessage('assistant', assistantMessage.content);
    } else {
      appendMessage('assistant', '(無回應內容)');
    }

    if (Array.isArray(data.tools_used)) {
      data.tools_used.forEach(tool => {
        if (tool.name) {
          appendMessage('tool', `✅ ${tool.name}`);
        }
      });
    }
  } catch (err) {
    console.error("呼叫 Agent 時出錯:", err);
    appendMessage('assistant', `❌ 呼叫錯誤： ${err.message}`);
  } finally {
    currentAssistantMessage.value = null;
  }
}

async function streamAgentRequest(payload) {
  let finalAssistantReply = "";

  try {
    const response = await fetch("http://localhost:8000/v1/agents/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP 錯誤！ 狀態碼： ${response.status}`);
    }
    if (!response.body) {
      throw new Error("回應 body 為空");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let eventType = null;
    let eventData = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          eventData += line.slice(6).trim();
        } else if (line.trim() === "") {
          if (eventType && eventData) {
            try {
              const data = JSON.parse(eventData);

              switch (eventType) {
                case "stream.start":
                  console.log("🟢 串流已開始");
                  break;

                case "stream.llm_tokens.start":
                  break;

                case "stream.llm_tokens.delta":
                  if (data.llm_tokens) {
                    currentAssistantMessage.value += data.llm_tokens;
                    finalAssistantReply += data.llm_tokens;
                    scrollToBottom();
                  }
                  break;

                case "stream.llm_tokens.completed":
                  break;

                case "stream.tool_call.start":
                  appendMessage("tool", ` ${data.tool_name} 啟動`);
                  break;

                case "stream.tool_call.delta":
                  break;

                case "stream.tool_call.completed":
                  appendMessage("tool", ` ${data.tool_name} 完成: ${JSON.stringify(data.tool_output)}`);
                  break;

                case "stream.completed":
                  console.log("🏁 Agent 串流邏輯已完成");
                  break;

                case "stream.error":
                  console.error("串流錯誤事件:", data.error);
                  appendMessage("assistant", ` 錯誤：${data.error}`);
                  break;

                default:
                  console.warn("⚠️ 未處理事件類型：", eventType, data);
                  break;
              }
            } catch (err) {
              console.error("❌ JSON 解析錯誤於 data:", eventData, "錯誤:", err);
              appendMessage("assistant", `❌ 解析錯誤: ${err.message}`);
            }

            eventType = null;
            eventData = "";
          }
        }
      }
    }

    if (finalAssistantReply) {
      appendMessage('assistant', finalAssistantReply);
    } else if (currentAssistantMessage.value === '') {
      appendMessage('assistant', '(無回應內容)');
    }

  } catch (err) {
    console.error("串流 Agent 錯誤:", err);
    appendMessage('assistant', `❌ 串流錯誤: ${err.message}`);
  } finally {
    currentAssistantMessage.value = null;
    isThinking.value = false;
    scrollToBottom();
  }
}

onMounted(() => {
  checkHealth();
  healthCheckInterval.value = setInterval(checkHealth, 15000);
});

onUnmounted(() => {
  if (healthCheckInterval.value) {
    clearInterval(healthCheckInterval.value);
  }
});

</script>

<style scoped>
#input-container {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 10;
  background-color: #ADD8E6;
  /* 淺藍色背景 */
  padding: 15px;
  border-radius: 8px;
  font-family: sans-serif;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  width: 350px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

/* 狀態和模式所在行的 div 樣式 */
#input-container>div:nth-child(1),
#input-container>div:nth-child(2) {
  color: #000000 !important;
  /* 強制黑色文字 */
  display: flex;
  /* 使用 Flexbox 佈局 */
  align-items: center;
  /* 垂直居中對齊 */
  margin-bottom: 10px;
  /* 底部外邊距 (從通用規則移到這裡更精確) */
}

/* 模式文字 span 樣式 */
#input-container>div:nth-child(2)>span {
  color: #000000 !important;
  /* 強制黑色文字 */
  opacity: 1 !important;
  /* 強制不透明 */
  margin-left: 5px;
  /* 與「模式：」標籤間距 */
}

/* 切換模式按鈕樣式 */
#input-container>div:nth-child(2)>button {
  padding: 8px 12px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  margin-left: auto;
  /* 自動左外邊距，使其靠右 */
}

/* 針對 :hover 和 :disabled 的樣式可以加在這裡或通用按鈕處 */
#input-container>div:nth-child(2)>button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

#input-container>div:nth-child(2)>button:hover:not(:disabled) {
  background-color: #0056b3;
}


/* 輸入框樣式 */
#input-container input[type="text"] {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  flex-grow: 1;
  /* 在 flex 容器中佔用剩餘空間 (如果父層是 flex column，這可能意義不大，但保留也無妨) */
  margin-bottom: 10px;
  /* 底部外邊距 */
}

/* 送出按鈕樣式 (通用按鈕樣式，移除特定佈局的 margin) */
#input-container>button {
  /* 選擇 #input-container 的直接子按鈕 (送出按鈕) */
  padding: 8px 12px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  /* margin-left: 5px; */
  /* 移除通用的 margin-left */
  margin-bottom: 10px;
  /* 底部外邊距 */
}

/* 送出按鈕禁用樣式 */
#input-container>button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* 送出按鈕滑鼠懸停樣式 */
#input-container>button:hover:not(:disabled) {
  background-color: #0056b3;
}

/* 聊天框樣式 */
#chatBox {
  margin-top: 10px;
  padding: 10px;
  height: 400px;
  overflow-y: auto;
  background-color: #f9f9f9;
  border: 1px solid #ccc;
  border-radius: 6px;
  white-space: pre-wrap;
  word-wrap: break-word;
  flex-grow: 1;
}

/* 每條訊息容器樣式 */
.message {
  margin-bottom: 12px;
  line-height: 1.4;
}

/* 使用者角色名稱樣式 */
.user {
  color: #004080;
  /* 深藍 */
  font-weight: bold;
}

/* Agent 角色名稱樣式 */
.assistant {
  color: #155724;
  /* 深綠 */
  font-weight: bold;
}

/* 工具角色名稱樣式 */
.tool {
  color: #49128C;
  /* 深紫 */
  font-weight: bold;
  font-style: italic;
}

/* 訊息內容文字樣式 */
.content {
  margin-left: 8px;
  display: inline-block;
  color: #333333;
  /* 深灰色 */
}
</style>