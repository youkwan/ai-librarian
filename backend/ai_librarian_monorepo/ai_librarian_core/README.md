# Ai-Librarian-Core

`ai-librarian-core` is a Python package designed to simplify the development of AI agents by providing a wrapper for LangChain and LangGraph. It offers comprehensive support for tooling, memory management, and streaming.

## Key Features

*   **Tooling**: Seamless integration with a variety of built-in tools.
*   **Memory Management**: Efficient handling of conversational memory for stateful agents.
*   **Streaming**: Support for real-time token streaming for interactive experiences.

## Available Built-in Tools

The following tools are readily available for use within `ai-librarian-core`:

*   **Google Books**: Search for books on Google Books.
*   **Google Search**: Search for information on Google.
*   **YouTube Search**: Search for videos on YouTube.
*   **Date Time**: Retrieve the current date and time.
*   **arXiv Search**: Search for academic papers on arXiv.
*   **DuckDuckGo Search**: Search for information using DuckDuckGo.
*   **Wikipedia Search**: Search for information on Wikipedia.
*   **OpenWeatherMap**: Get the current weather for a given location.
*   **NCL Crawler**: A specialized crawler for the Taiwan National Central Library (台灣國家圖書館).

## Installation

Follow these steps to set up the `ai-librarian-core` package:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/youkwan/ai-librarian.git
    cd ai-librarian/backend/ai_librarian_monorepo/ai_librarian_core/
    ```

2.  **Install uv (if not already installed):**
    This project utilizes [uv](https://github.com/astral-sh/uv) for efficient virtual environment and dependency management. If you do not have `uv` installed, please follow the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

3.  **Install Package Dependencies:**
    Navigate to the `ai_librarian_core` directory and run the following command to install all necessary dependencies:
    ```bash
    uv sync
    ```

## Usage

### Initializing Tools

The `init_built_in_tools()` function automatically initializes and includes all available built-in tools based on the environment variables you provide.

```python
import os
from ai_librarian_core.tools.tools import init_built_in_tools

# (Optional) For Google Books: If GOOGLE_API_KEY is not provided, the Google Books tool will not be initialized.
os.environ["GOOGLE_API_KEY"] = "your_google_api_key"
# (Optional) For Google Search: If GOOGLE_CSE_ID is not provided, the Google Search tool will not be initialized.
os.environ["GOOGLE_CSE_ID"] = "your_google_cse_id"
# (Optional) For OpenWeatherMap: If OPENWEATHERMAP_API_KEY is not provided, the OpenWeatherMap tool will not be initialized.
os.environ["OPENWEATHERMAP_API_KEY"] = "your_openweathermap_api_key"

tools = init_built_in_tools()
```

Tools are based on `langchain_core.tools.BaseTool`. You can implement custom tools by subclassing `BaseTool` and adding them to the `tools` list. Tools can be directly invoked using `.invoke()` or `.ainvoke()`.

```python
from langchain_core.tools import BaseTool
from ai_librarian_core.tools.date_time import DateTimeTool
from ai_librarian_core.tools.tools import init_built_in_tools

tools: list[BaseTool] = init_built_in_tools()

date_time_tool = DateTimeTool()
result = date_time_tool.invoke({}) # Directly invoke the tool
print(result)
```

```plaintext
The current time is 2025-07-29T22:29:13.161976+08:00
```

### Invoking a ReAct Agent

```python
import asyncio
import os
from langgraph.checkpoint.memory import InMemorySaver
from ai_librarian_core.graph.react import init_react_graph
from ai_librarian_core.tools.tools import init_built_in_tools

os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

tools = init_built_in_tools()

in_memory_react_graph = init_react_graph(
    name="react_graph",
    tools=tools,
    checkpointer=InMemorySaver(),
)

result = asyncio.run(
    in_memory_react_graph.ainvoke(
        input={
            "messages": [
                {"role": "system", "content": "you are a helpful assistant"},
                {
                    "role": "user",
                    "content": "I'm learning how to build AI agents. Could you help me find online tutorials and some educational videos?",
                },
            ],
            "llm_config": {
                "model": "openai:gpt-4o-mini",
                "temperature": 1.0,
            },
        },
        config={
            "configurable": {
                "thread_id": "thread-1234567890",
            },
        },
    )
)

print(result["messages"][-1].content)
```

```plaintext
Here are some resources to help you learn how to build AI agents:

### Online Tutorials
1. **Building AI Agents in Pure Python - Beginner Course**: A comprehensive course that covers the fundamentals of building AI agents. This course is segmented into three chapters, focusing on foundational understanding, hands-on tutorials, and practical applications.

2. **Free Video Course on DeepLearning.ai**: This course guides you from beginner to expert in understanding, using, and building AI agents. It covers core techniques for building responsive AI systems.

3. **Vertex AI Agent Builder**: A resource that helps you turn your processes into multi-agent experiences, focusing on building rather than disrupting existing systems.

### Educational Videos
Here are some YouTube videos that can help you get started:

1. [Building AI Agents - Video 1](https://www.youtube.com/watch?v=_Udb5NC6vTI&pp=ygUSYnVpbGRpbmcgQUkgYWdlbnRz)
2. [Building AI Agents - Video 2](https://www.youtube.com/watch?v=T1Lowy1mnEg&pp=ygUSYnVpbGRpbmcgQUkgYWdlbnRz)
3. [Building AI Agents - Video 3](https://www.youtube.com/watch?v=w0H1-b044KY&pp=ygUSYnVpbGRpbmcgQUkgYWdlbnRz)
4. [Building AI Agents - Video 4](https://www.youtube.com/watch?v=bZzyPscbtI8&pp=ygUSYnVpbGRpbmcgQUkgYWdlbnRz)
5. [Building AI Agents - Video 5](https://www.youtube.com/watch?v=NUPjbWsSe7s&pp=ygUSYnVpbGRpbmcgQUkgYWdlbnRz)

These resources should provide a solid foundation for your learning journey in building AI agents!
```

### Streaming from a ReAct Agent

```python
import asyncio
from langgraph.checkpoint.memory import InMemorySaver
from ai_librarian_core.graph.react import init_react_graph
from ai_librarian_core.tools.tools import init_built_in_tools

os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

tools = init_built_in_tools()
in_memory_react_graph = init_react_graph("react_graph", tools, InMemorySaver())

async def stream_tokens():
    async for msg, metadata in in_memory_react_graph.astream(
        input={
            "messages": [
                {"role": "system", "content": "you are a helpful assistant"},
                {
                    "role": "user",
                    "content": "I'm learning how to build AI agents. Could you help me find online tutorials and some educational videos?",
                },
            ],
            "llm_config": {
                "model": "openai:gpt-4o-mini",
                "temperature": 1.0,
            },
        },
        config={
            "configurable": {
                "thread_id": "thread-1234567890",
            },
        },
        stream_mode="messages",
    ):
        print(msg.content, end="|", flush=True)

asyncio.run(stream_tokens())
```

```plaintext
Here| are| some| resources| to| help| you| learn| how| to| build| AI| agents|:

|###| Online| Tutorials|
|1|.| **|Master|ing| AI| Agents|**|:| A| list| of| the| best| free| courses|,| tutorials|,| and| learning| tools| for| AI| agents|.| You| can| find| courses| ranging| from| beginner| to| advanced| levels| that| cover| the| fundamentals| of| understanding|,| using|,| and| building| AI| agents|.| Here| are| some| highlights|:
|  | -| **|AI| Agents| Explained|**|:| A| short| video| guide| that| provides| a| good| introduction|.
|  | -| **|Begin|ner|-friendly| courses|**|:| There| are| courses| that| take| you| from| concept| to| code|,| covering| the| fundamentals| of| building| AI| agents| in| detail|.

|2|.| **|Building| an| AI| Agent| with| Vertex| AI| Agent| Builder|**|:| This| tutorial| covers| how| to| build| AI| agents|,| automation| bots|,| chat| assistants|,| and| more| without| requiring| APIs|.| Consider| exploring| this| if| you're| interested| in| practical| applications|.

|###| Educational| Videos|
|Here| are| a| couple| of| educational| videos| on| AI| agents|:
|1|.| [|AI| Agents| Explained|:| Educational| Video|](|https|://|www|.youtube|.com|/watch|?v|=|Fw|OT|s|4|Ux|QS|4|&|pp|=|yg|Uc|QU|kg|YW|dl|bn|R|z|IG|V|kd|WN|hd|Gl|v|bm|Fs|IH|Z|p|Z|GV|vc|w|%|3D|%|3D|)
|2|.| [|Another| AI| Agents| Educational| Video|](|https|://|www|.youtube|.com|/watch|?v|=h|L|JT|c|V|HW|8|_I|&|pp|=|yg|Uc|QU|kg|YW|dl|bn|R|z|IG|V|kd|WN|hd|Gl|v|bm|Fs|IH|Z|p|Z|GV|vc|w|%|3D|%|3D|)

|Feel| free| to| explore| these| resources| to| enhance| your| understanding| and| skills| in| building| AI| agents|!||
```
