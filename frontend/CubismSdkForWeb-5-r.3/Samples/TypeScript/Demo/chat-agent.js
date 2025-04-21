let threadId = null;
let useStreamAgent = false;
async function checkHealth() {
  const healthStatus = document.getElementById("healthStatus");
  try {
    const res = await fetch("http://localhost:8000/v1/sys/health");
    const data = await res.json();

    if (res.ok && data.status === "ok") {
      healthStatus.textContent = "✅";
      healthStatus.style.color = "green";
    } else {
      healthStatus.textContent = "❌";
      healthStatus.style.color = "red";
    }
  } catch (err) {
    healthStatus.textContent = "❌";
    healthStatus.style.color = "red";
  }
}
checkHealth();
setInterval(checkHealth, 15000); 

const chatBox = document.getElementById('chatBox');
const agentStatus = document.getElementById('agentStatus');
const toggleAgentBtn = document.getElementById('toggleAgentBtn');

function appendMessage(role, text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message';

  const roleSpan = document.createElement('span');
  roleSpan.className = role;
  roleSpan.textContent =
    role === 'user' ? 'user：' :
    role === 'assistant' ? 'agent：' :
    role === 'tool' ? 'tool：' : '';

  const contentSpan = document.createElement('span');
  contentSpan.className = 'content';
  contentSpan.textContent = text;

  msgDiv.appendChild(roleSpan);
  msgDiv.appendChild(contentSpan);
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

toggleAgentBtn.addEventListener('click', () => {
  useStreamAgent = !useStreamAgent;
  agentStatus.textContent = useStreamAgent ? 'Stream Agent' : 'Invoke Agent';
  toggleAgentBtn.textContent = useStreamAgent ? 'mode' : 'mode';
});

document.getElementById('submitBtn')?.addEventListener('click', async () => {
  const textInput = document.getElementById('textInput');
  const userInput = textInput.value.trim();
  if (!userInput) return;

  if (!threadId) {
    threadId = `thread-${crypto.randomUUID()}`;
  }

  appendMessage("user", userInput);

  const assistantMsgDiv = document.createElement('div');
  assistantMsgDiv.className = 'message';
  const assistantRole = document.createElement('span');
  assistantRole.className = 'assistant';
  assistantRole.textContent = 'agent：';
  const assistantContentRef = document.createElement('span');
  assistantContentRef.className = 'content';
  assistantContentRef.textContent = 'thinking...';
  assistantMsgDiv.appendChild(assistantRole);
  assistantMsgDiv.appendChild(assistantContentRef);
  chatBox.appendChild(assistantMsgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  const payload = {
    thread_id: threadId,
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: userInput }
    ],
    llm_config: {
      model: "openai:gpt-4o-mini",
      temperature: 1,
      max_tokens: null
    }
  };

  try {
    if (useStreamAgent) {
      const response = await fetch("http://localhost:8000/v1/agents/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let assistantReply = "";
      let buffer = "";
      let eventType = null;
      let eventData = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

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
                    console.log("🟢 Stream started");
                    break;
                
                  case "stream.llm_tokens.start":
                    appendMessage("assistant", " 開始生成回應");
                    break;
                
                  case "stream.llm_tokens.delta":
                    assistantReply += data.llm_tokens;
                    assistantContentRef.textContent = assistantReply;
                    break;
                
                  case "stream.llm_tokens.completed":
                    appendMessage("assistant", " 回應生成完成");
                    break;
                
                  case "stream.tool_call.start":
                    appendMessage("tool", ` ${data.tool_name} 啟動`);
                    break;
                
                  case "stream.tool_call.delta":
                    appendMessage("tool", ` ${data.tool_name} 執行中`);
                    break;
                
                  case "stream.tool_call.completed":
                    appendMessage("tool", ` ${data.tool_name} 完成`);
                    break;
                
                  case "stream.completed":
                    console.log(" Agent 邏輯執行完成");
                    break;
                
                  case "stream.error":
                    appendMessage("assistant", ` 錯誤：${data.error}`);
                    break;
                
                  default:
                    console.warn("⚠️ 未處理事件類型：", eventType, data);
                    break;
                }
              } catch (err) {
                console.error("❌ JSON 解析錯誤：", err);
              }

              eventType = null;
              eventData = "";
            }
          }
        }
      }
    } else {
      const res = await fetch("http://localhost:8000/v1/agents/invoke", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();  

      const assistantMessage = data.messages?.reverse().find(msg => msg.role === "assistant");
      if (assistantMessage && assistantMessage.content) {
        assistantContentRef.textContent = assistantMessage.content;  
        assistantContentRef.textContent = "沒有找到 agent 回覆";
      }


      if (Array.isArray(data.tools_used)) {
        data.tools_used.forEach(tool => {
          if (tool.name) {
            appendMessage("tool", `✅ ${tool.name}`);
          }
        });
      }
    }
  } catch (err) {
    assistantContentRef.textContent = `❌ 錯誤：${err.message}`;
  }

  textInput.value = "";
});

textInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    document.getElementById('submitBtn').click();
    e.preventDefault();
  }
});
