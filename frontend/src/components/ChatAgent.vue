<template>
  <div id="gemini-chat-container">
    <div class="chat-header">
      <div class="header-title"></div>
      <div class="status-indicators">
        <span class="health-light-indicator" :title="healthStatusTooltipText">
          <span class="status-dot" :style="{ backgroundColor: healthLightColorComputed }"></span>
        </span>

        <div class="settings-menu-container" ref="settingsMenuContainerRef">
          <button @click="toggleSettingsMenu" class="settings-button" title="設定">
            <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 0 24 24" width="20px" fill="currentColor">
              <path d="M0 0h24v24H0V0z" fill="none" />
              <path
                d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
            </svg>
          </button>
          <div v-if="isSettingsMenuOpen" class="settings-dropdown">
            <ul>
              <li @click="handleSwitchMode" :class="{ 'disabled-menu-item': isThinking }">
                切換模式 (目前: {{ agentStatusTextShort }})
              </li>
              <li @click="openSystemPromptModal">自訂系統提示</li>
              <li @click="openModelSelectionModal" :class="{ 'disabled-menu-item': isThinking }">
                切換語言模型 (目前: {{ getModelShortName(currentModel) }})
              </li>
              <li @click="openLive2DModelModal" :class="{ 'disabled-menu-item': isThinking }">
                切換角色模型 (目前: {{ currentLive2DModel }})
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <div id="chatBox" ref="chatBoxRef">
      <div v-for="(msg, index) in messages" :key="index" class="message-row" :class="`message-row-${msg.role}`">
        <div class="message-bubble" :class="`message-bubble-${msg.role}`">
          <div class="message-content">
            <div v-if="msg.role === 'assistant'" class="role-name">{{ getRoleDisplayName(msg.role) }}</div>
            <template v-if="msg.role === 'user' || msg.role === 'assistant'">
              <div class="text-content" v-html="formatMessageContent(msg.content)"></div>
            </template>
            <template v-if="msg.role === 'tool'">
              <div class="show-thinking-button" @click="msg.isExpanded = !msg.isExpanded"
                :class="{ 'expanded': msg.isExpanded, 'collapsed': !msg.isExpanded }">
                顯示思路 <span class="tool-toggle-icon">{{ msg.isExpanded ? '▼' : '▶' }}</span>
              </div>
              <div class="text-content tool-details-content" v-if="msg.isExpanded"
                v-html="formatMessageContent(msg.content)">
              </div>
            </template>
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

    <div v-if="isSystemPromptModalOpen" class="modal-overlay" @click.self="cancelSystemPromptEdit">
      <div class="modal-content">
        <h3>自訂系統提示</h3>
        <p>修改下方內容以變更 AI 助理的行為、角色或回應風格。留空將使用預設提示。</p>
        <textarea v-model="editableSystemPrompt" class="system-prompt-textarea" rows="8"
          placeholder="例如：你是一位樂於助人的圖書館員..."></textarea>
        <div class="modal-actions">
          <button @click="cancelSystemPromptEdit" class="modal-button">取消</button>
          <button @click="saveSystemPrompt" class="modal-button primary">儲存並套用</button>
        </div>
      </div>
    </div>

    <div v-if="isModelSelectionModalOpen" class="modal-overlay" @click.self="cancelModelSelection">
      <div class="modal-content">
        <h3>選擇語言模型</h3>
        <p>選擇一個 AI 助理使用的語言模型。變更將在下次發送訊息時生效。</p>
        <div class="model-selection-list">
          <div v-for="modelId in availableModels" :key="modelId" class="model-option">
            <input type="radio" :id="`model-${modelId}`" :value="modelId" v-model="editableSelectedModel"
              name="llmModel" />
            <label :for="`model-${modelId}`" :title="modelId">{{ getModelDisplayName(modelId) }}</label>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="cancelModelSelection" class="modal-button">取消</button>
          <button @click="saveSelectedModel" class="modal-button primary">儲存並套用</button>
        </div>
      </div>
    </div>

    <div v-if="isLive2DModelModalOpen" class="modal-overlay" @click.self="cancelLive2DModelSelection">
      <div class="modal-content">
        <h3>選擇角色模型</h3>
        <p>選擇一個喜歡的 Live2D 角色模型。變更將會立即生效。</p>
        <div class="model-selection-list">
          <div v-for="modelName in availableLive2DModels" :key="modelName" class="model-option">
            <input type="radio" :id="`live2d-model-${modelName}`" :value="modelName" v-model="editableLive2DModel"
              name="live2dModel" />
            <label :for="`live2d-model-${modelName}`">{{ modelName }}</label>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="cancelLive2DModelSelection" class="modal-button">取消</button>
          <button @click="saveSelectedLive2DModel" class="modal-button primary">套用</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue';

const props = defineProps({
  currentLive2DModel: {
    type: String,
    required: true
  }
});
const emit = defineEmits(['update:live2d-model']);

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

const toolMessageMap = new Map();
const currentTurnToolMessageIndices = ref([]);

const isSettingsMenuOpen = ref(false);
const settingsMenuContainerRef = ref(null);
const isSystemPromptModalOpen = ref(false);
const defaultSystemPrompt = "You are a helpful, creative, and friendly AI assistant, in the style of Gemini.";
const currentSystemPrompt = ref(defaultSystemPrompt);
const editableSystemPrompt = ref("");

const defaultModel = "openai:gpt-4o-mini";
const currentModel = ref(defaultModel);
const editableSelectedModel = ref(defaultModel);
const isModelSelectionModalOpen = ref(false);
const availableModels = ref([
  "openai:gpt-4o-mini", "openai:gpt-4o", "openai:gpt-4.5-preview", "openai:o1-mini", "openai:o1",
  "anthropic:claude-3-7-sonnet-latest", "anthropic:claude-3-5-haiku-latest", "anthropic:claude-3-5-sonnet-latest", "anthropic:claude-3-5-sonnet-20240620",
  "google_genai:gemini-2.5-pro-exp-03-25", "google_genai:gemini-2.0-flash", "google_genai:gemini-2.0-flash-lite", "google_genai:gemini-1.5-flash", "google_genai:gemini-1.5-flash-80", "google_genai:gemini-1.5-pro",
  "groq:meta-llama/Llama-4-scout-170-i6e-instruct", "groq:llama-3.1-70b-versatile", "groq:llama-3.1-70b-specdec", "groq:llama-3.1-1b-preview", "groq:llama-3.1-3b-preview", "groq:llama-3.1-8b-instant",
  "groq:mistral-saba-240", "groq:gwen-qwq-32b", "groq:gwen-2.5-coder-32b", "groq:gwen-2.5-32b"
]);

const availableLive2DModels = ref(['Haru', 'Hiyori', 'Mao', 'Mark', 'Natori', 'Rice', 'Wanko']);
const isLive2DModelModalOpen = ref(false);
const editableLive2DModel = ref('');

const healthLightColorComputed = computed(() => {
  if (healthStatus.value === 'ok') return '#1e8e3e';
  if (healthStatus.value === 'error') return '#d93025';
  return '#aaaaaa';
});
const healthStatusTooltipText = computed(() => {
  if (healthStatus.value === 'ok') return '連線狀態：良好';
  if (healthStatus.value === 'error') return '連線狀態：異常';
  return '連線狀態：檢查中...';
});
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

const agentStatusTextShort = computed(() => (useStreamAgent.value ? '串流' : '呼叫'));

const getModelShortName = (modelId) => {
  if (!modelId) return 'N/A';
  if (modelId.includes(':')) {
    const parts = modelId.split(':');
    if (parts[1]) {
      const subParts = parts[1].split('/');
      return subParts[subParts.length - 1];
    }
    return parts[0];
  }
  return modelId;
};

const getModelDisplayName = (modelId) => {
  if (!modelId) return '未知模型';
  let name = modelId;
  if (modelId.startsWith("openai:")) name = "OpenAI " + modelId.substring(7);
  else if (modelId.startsWith("anthropic:")) name = "Anthropic " + modelId.substring(10);
  else if (modelId.startsWith("google_genai:")) name = "Google " + modelId.substring(13).replace("-exp-", " Exp ");
  else if (modelId.startsWith("groq:")) name = "Groq " + modelId.substring(5);
  return name.replace(/-/g, ' ').replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};
async function checkHealth() {
  try {
    const res = await fetch("http://localhost:8000/v1/sys/health");
    if (!res.ok) {
      console.warn(`健康檢查失敗，狀態碼: ${res.status}`);
      healthStatus.value = 'error'; return;
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

const toggleSettingsMenu = () => {
  isSettingsMenuOpen.value = !isSettingsMenuOpen.value;
};

const handleSwitchMode = () => {
  toggleAgentMode();
  isSettingsMenuOpen.value = false;
};

const handleClickOutsideSettingsMenu = (event) => {
  if (isSettingsMenuOpen.value && settingsMenuContainerRef.value && !settingsMenuContainerRef.value.contains(event.target)) {
    isSettingsMenuOpen.value = false;
  }
};

const openSystemPromptModal = () => {
  editableSystemPrompt.value = currentSystemPrompt.value === defaultSystemPrompt ? "" : currentSystemPrompt.value;
  isSettingsMenuOpen.value = false;
  isSystemPromptModalOpen.value = true;
};

const saveSystemPrompt = () => {
  currentSystemPrompt.value = editableSystemPrompt.value.trim() || defaultSystemPrompt;
  isSystemPromptModalOpen.value = false;
};
const cancelSystemPromptEdit = () => {
  isSystemPromptModalOpen.value = false;
};
const openModelSelectionModal = () => {
  if (isThinking.value) return;
  editableSelectedModel.value = currentModel.value;
  isSettingsMenuOpen.value = false;
  isModelSelectionModalOpen.value = true;
};
const saveSelectedModel = () => {
  currentModel.value = editableSelectedModel.value;
  isModelSelectionModalOpen.value = false;
};
const cancelModelSelection = () => {
  isModelSelectionModalOpen.value = false;
};

const openLive2DModelModal = () => {
  if (isThinking.value) return;
  editableLive2DModel.value = props.currentLive2DModel;
  isSettingsMenuOpen.value = false;
  isLive2DModelModalOpen.value = true;
};

const saveSelectedLive2DModel = () => {
  emit('update:live2d-model', editableLive2DModel.value);
  isLive2DModelModalOpen.value = false;
};

const cancelLive2DModelSelection = () => {
  isLive2DModelModalOpen.value = false;
};

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

  messages.value.push({ role: 'user', content: text });
  userInput.value = '';
  if (userInputRef.value) userInputRef.value.style.height = 'auto';

  isThinking.value = true;
  currentTurnToolMessageIndices.value = [];
  currentAssistantMessage.value = '';

  let dotCount = 0;
  clearInterval(thinkingInterval);
  thinkingInterval = setInterval(() => {
    dotCount = (dotCount + 1) % 4;
    let dots = Array(dotCount).fill('<span class="dot animate">.</span>').join('');
    if (!currentAssistantMessage.value) {
      thinkingDots.value = dots || '<span class="dot thinking-placeholder-dot">.</span>';
    }
  }, 500);
  const payload = {
    thread_id: threadId.value,
    messages: [
      { role: "system", content: currentSystemPrompt.value },
      ...messages.value.filter(m => m.role === 'user' || m.role === 'assistant').slice(-10),
    ],
    llm_config: { model: currentModel.value, temperature: 0.7, max_tokens: 2000 }
  };
  try {
    if (useStreamAgent.value) {
      await streamAgentRequest(payload);
    } else {
      await invokeAgentRequest(payload);
    }
  } catch (error) {
    console.error("發送訊息時捕獲到未處理的錯誤:", error);
    messages.value.push({ role: 'assistant', content: `❌ 糟糕，似乎發生了一些問題：${error.message}` });
  } finally {
    isThinking.value = false;
    clearInterval(thinkingInterval);
    thinkingDots.value = '';
    currentAssistantMessage.value = null;
    currentTurnToolMessageIndices.value.forEach(index => {
      if (messages.value[index] && messages.value[index].role === 'tool') {
        messages.value[index].isExpanded = false;
      }
    });
    currentTurnToolMessageIndices.value = [];

    scrollToBottom();
  }
}

async function invokeAgentRequest(payload) {
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
    const assistantMsgs = data.messages?.filter(msg => msg.role === "assistant" && msg.content);
    if (assistantMsgs && assistantMsgs.length > 0) {
      assistantMsgs.forEach(msg => messages.value.push({ role: 'assistant', content: msg.content }));
    } else {
      messages.value.push({ role: 'assistant', content: '(AI 沒有提供回應)' });
    }
    if (Array.isArray(data.tools_used)) {
      data.tools_used.forEach(tool => {
        if (tool.name) {
          const toolContent = `工具 '${tool.name}' 已執行。\n輸出: ${JSON.stringify(tool.tool_output, null, 2) || '(無輸出)'}`;
          messages.value.push({ role: 'tool', content: toolContent, isExpanded: false });
        }
      });
    }
  } catch (err) {
    console.error("呼叫 (Invoke) Agent 時出錯:", err);
    messages.value.push({ role: 'assistant', content: `❌ 呼叫 AI 時發生錯誤： ${err.message}` });
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
    if (!response.ok) { const errorText = await response.text(); throw new Error(`伺服器錯誤 ${response.status}: ${errorText || response.statusText}`); }
    if (!response.body) { throw new Error("回應 body 為空，無法讀取串流。"); }

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
          if (line.startsWith("event:")) eventType = line.substring(6).trim();
          else if (line.startsWith("data:")) eventDataLines.push(line.substring(5).trim());
        });
        const eventData = eventDataLines.join("\n");
        if (eventData) {
          try {
            const jsonData = JSON.parse(eventData);
            processStreamEvent(eventType, jsonData, (delta) => {
              if (currentAssistantMessage.value === '' && delta.trim() !== '') {
                clearInterval(thinkingInterval);
                thinkingDots.value = '';
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
      messages.value.push({ role: 'assistant', content: accumulatedAssistantReply });
    } else if (!messages.value.some(m => m.role === 'assistant' && m.content?.trim()) && toolMessageMap.size === 0) {
      messages.value.push({ role: 'assistant', content: '(AI 沒有提供回應)' });
    }
  } catch (err) {
    console.error("串流 Agent 請求錯誤:", err);
    messages.value.push({ role: 'assistant', content: `❌ 串流處理時發生錯誤: ${err.message}` });
  } finally {
    toolMessageMap.clear();
  }
}

function processStreamEvent(eventType, data, onDelta) {
  const toolId = data.tool_call_id || data.tool_name;
  switch (eventType) {
    case "stream.tool_call.start": {
      const startContent = `🔧 工具 '${data.tool_name}' 執行中...\n`;
      const newToolMsg = { role: "tool", content: startContent, isExpanded: true };
      messages.value.push(newToolMsg);
      const newMsgIndex = messages.value.length - 1;
      toolMessageMap.set(toolId, newMsgIndex);
      if (isThinking.value) {
        currentTurnToolMessageIndices.value.push(newMsgIndex);
      }
      scrollToBottom();
      break;
    }
    case "stream.tool_call.delta": {
      const deltaIdx = toolMessageMap.get(toolId);
      if (typeof deltaIdx === "number" && messages.value[deltaIdx] && data.tool_tokens) {
        messages.value[deltaIdx].content += data.tool_tokens;
        scrollToBottom();
      }
      break;
    }
    case "stream.tool_call.completed": {
      const completedIdx = toolMessageMap.get(toolId);
      if (typeof completedIdx === "number" && messages.value[completedIdx]) {
        messages.value[completedIdx].content += `\n🔧 工具 '${data.tool_name}' 執行完成`;
        if (data.tool_output) {
          messages.value[completedIdx].content += `\n輸出: ${JSON.stringify(data.tool_output, null, 2)}`;
        }
      } else {
        const completeContent = `🔧 工具 '${data.tool_name}' 完成 (獨立事件)。\n\n輸出: ${JSON.stringify(data.tool_output, null, 2) ||
          '(無)'}`;
        messages.value.push({ role: "tool", content: completeContent, isExpanded: false });
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
      messages.value.push({ role: 'assistant', content: `❌ 串流錯誤：${data.error}` });
      scrollToBottom();
      break;
  }
}

onMounted(() => {
  checkHealth();
  healthCheckInterval.value = setInterval(checkHealth, 30000);
  autoGrowTextarea();
  document.addEventListener('click', handleClickOutsideSettingsMenu);
});
onUnmounted(() => {
  if (healthCheckInterval.value) clearInterval(healthCheckInterval.value);
  clearInterval(thinkingInterval);
  document.removeEventListener('click', handleClickOutsideSettingsMenu);
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');

:root {
  --gemini-primary-text: #1f1f1f;
  --gemini-secondary-text: #5f6368;
  --gemini-background: #ffffff;
  --gemini-user-message-bg: #e8f0fe;
  --gemini-user-message-text: #1a73e8;
  --gemini-ai-message-bg: #f8f9fa;
  --gemini-assistant-message-text: #3c4043;
  --gemini-tool-message-bg: #fef7e0;
  --gemini-tool-text-color: #754c00;
  --gemini-tool-border-color: #fce8b2;
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
  max-width: 40vw;
  min-width: 320px;
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
  flex-direction: column;
  word-break: break-word;
}

.message-bubble-user {
  background-color: var(--gemini-user-message-bg);
  color: var(--gemini-user-message-text);
  border-bottom-right-radius: 6px;
}

.message-bubble-assistant {
  background-color: var(--gemini-ai-message-bg);
  color: var(--gemini-assistant-message-text);
  border: 1px solid var(--gemini-border-color);
  border-bottom-left-radius: 6px;
}

.message-bubble-tool {
  background-color: var(--gemini-tool-message-bg);
  color: var(--gemini-tool-text-color);
  font-size: 0.9em;
  border-radius: 12px;
}

.message-content {
  display: flex;
  flex-direction: column;
  width: 100%;
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

.tool-details-content {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--gemini-tool-border-color);
}

.show-thinking-button {
  display: inline-block;
  font-size: 0.85em;
  font-weight: 500;
  color: var(--gemini-secondary-text);
  cursor: pointer;
  user-select: none;
  transition: background-color 0.15s ease, padding 0.15s ease, border-color 0.15s ease, border-radius 0.15s ease;
  align-self: flex-start;
  padding: 2px 4px;
}

.show-thinking-button.expanded {
  padding: 5px 12px;
  background-color: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 16px;
}

.show-thinking-button.expanded:hover {
  background-color: rgba(0, 0, 0, 0.06);
}

.show-thinking-button.collapsed {
  background-color: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  padding-left: 0;
  padding-right: 0;
}

.show-thinking-button.collapsed:hover {
  background-color: rgba(0, 0, 0, 0.025);
}

.tool-toggle-icon {
  display: inline-block;
  margin-left: 6px;
  font-weight: normal;
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

.settings-menu-container {
  position: relative;
  display: inline-block;
}

.settings-button {
  background: transparent;
  border: none;
  padding: 6px;
  margin-left: 8px;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gemini-secondary-text);
  transition: background-color 0.2s;
}

.settings-button:hover {
  background-color: #e0e0e0;
}

.settings-button svg {
  width: 20px;
  height: 20px;
}

.settings-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  background-color: #ffffff !important;
  opacity: 1 !important;
  border: 1px solid var(--gemini-border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 220px;
  overflow: hidden;
}

.settings-dropdown ul {
  list-style: none;
  padding: 8px 0;
  margin: 0;
}

.settings-dropdown li {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 0.9em;
  color: #000000 !important;
  font-weight: 500;
  white-space: nowrap;
}

.settings-dropdown li:hover {
  background-color: var(--gemini-input-bg);
}

.settings-dropdown li.disabled-menu-item {
  color: #aaa !important;
  cursor: not-allowed;
  font-weight: normal;
}

.settings-dropdown li.disabled-menu-item:hover {
  background-color: transparent;
}

.health-light-indicator {
  display: inline-flex;
  align-items: center;
  margin-right: 10px;
  height: 20px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  transition: background-color 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: var(--gemini-background);
  padding: 25px 30px;
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 550px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 5px;
  color: var(--gemini-primary-text);
  font-size: 1.4em;
}

.modal-content p {
  font-size: 0.9em;
  color: var(--gemini-secondary-text);
  margin-bottom: 10px;
  line-height: 1.6;
}

.system-prompt-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--gemini-border-color);
  border-radius: 6px;
  font-family: var(--gemini-font-family);
  font-size: 0.95em;
  resize: vertical;
  min-height: 100px;
  box-sizing: border-box;
}

.system-prompt-textarea:focus {
  outline: none;
  border-color: var(--gemini-button-bg);
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 15px;
}

.modal-button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9em;
  transition: background-color 0.2s, box-shadow 0.2s;
}

.modal-button.primary {
  background-color: var(--gemini-button-bg);
  color: var(--gemini-button-text);
}

.modal-button.primary:hover {
  background-color: #1558b0;
}

.modal-button:not(.primary) {
  background-color: var(--gemini-input-bg);
  color: var(--gemini-primary-text);
  border: 1px solid var(--gemini-border-color);
}

.modal-button:not(.primary):hover {
  background-color: #e0e0e0;
}

.model-selection-list {
  max-height: 300px;
  overflow-y: auto;
  padding-right: 10px;
  margin-top: 10px;
  margin-bottom: 10px;
  border: 1px solid var(--gemini-border-color);
  border-radius: 6px;
  padding: 10px;
}

.model-option {
  display: flex;
  align-items: center;
  padding: 8px 5px;
  cursor: pointer;
  border-radius: 4px;
}

.model-option:hover {
  background-color: var(--gemini-input-bg);
}

.model-option input[type="radio"] {
  margin-right: 10px;
  accent-color: var(--gemini-button-bg);
}

.model-option label {
  font-size: 0.95em;
  color: var(--gemini-primary-text);
  cursor: pointer;
  flex-grow: 1;
}
</style>
