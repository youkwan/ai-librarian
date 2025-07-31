# ai-librarian-core

`ai-librarian-core` is a Python package designed to streamline the development of AI agents. It provides a comprehensive wrapper around LangChain and LangGraph, offering seamless integration with essential functionalities such as tooling, memory management, and real-time streaming capabilities.

## Key Features

*   **Tooling Integration**: Easily integrate and manage a variety of pre-built and custom tools to extend agent capabilities.
*   **Memory Management**: Efficiently handle conversational memory, enabling stateful and context-aware AI agents.
*   **Streaming Support**: Facilitate interactive user experiences with real-time token streaming for agent responses.

## Built-in Tools

The following tools are readily available within `ai-librarian-core`:

*   **Google Books**: Search for books and publications on Google Books.
*   **Google Search**: Perform web searches using Google.
*   **YouTube Search**: Search for videos on YouTube.
*   **Date Time**: Retrieve the current date and time.
*   **arXiv Search**: Search for academic papers and preprints on arXiv.
*   **DuckDuckGo Search**: Conduct web searches using DuckDuckGo.
*   **Wikipedia Search**: Access information from Wikipedia.
*   **OpenWeatherMap**: Obtain current weather data for specified locations.
*   **NCL Crawler**: A specialized web crawler for the National Central Library of Taiwan (國家圖書館).

## Installation

To set up the `ai-librarian-core` package, follow these steps:

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/youkwan/ai-librarian.git
    cd ai-librarian/backend/ai_librarian_monorepo/ai_librarian_core/
    ```

2.  **Install uv:**
    This project leverages [uv](https://github.com/astral-sh/uv) for efficient virtual environment and dependency management. If you do not have `uv` installed, please follow the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

3.  **Install Playwright Browsers (Optional):**
    If you intend to use the `NCL Crawler` tool, you must install the necessary browser binaries for Playwright:

    ```bash
    playwright install
    ```

4.  **Install Package Dependencies:**
    Navigate to the `ai_librarian_core` directory and install all required dependencies:

    ```bash
    uv sync
    ```

## Usage

### Environment Variables

Certain tools require API keys or specific IDs to function correctly. Set the following environment variables as needed:

*   `OPENAI_API_KEY`: Required for OpenAI models.
*   `GOOGLE_API_KEY`: Required for Google Books and Google Search.
*   `GOOGLE_CSE_ID`: Required for Google Search.
*   `OPENWEATHERMAP_API_KEY`: Required for the OpenWeatherMap tool.

### Initializing Tools

The `init_built_in_tools()` function automatically initializes and loads all available built-in tools based on the configured environment variables.

```python
import os
from ai_librarian_core.tools.tools import init_built_in_tools

# Example: Set environment variables (replace with your actual keys)
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
os.environ["GOOGLE_API_KEY"] = "your_google_api_key"
os.environ["GOOGLE_CSE_ID"] = "your_google_cse_id"
os.environ["OPENWEATHERMAP_API_KEY"] = "your_openweathermap_api_key"

tools = init_built_in_tools()
# tools will contain initialized instances of BaseTool subclasses
```

Tools are based on `langchain_core.tools.BaseTool`. You can implement custom tools by subclassing `BaseTool` and appending them to the `tools` list. Tools can be directly invoked using their `invoke()` or `ainvoke()` methods.

```python
from langchain_core.tools import BaseTool
from ai_librarian_core.tools.date_time import DateTimeTool
from ai_librarian_core.tools.tools import init_built_in_tools

# Initialize tools
tools: list[BaseTool] = init_built_in_tools()

# Example: Directly invoking the DateTimeTool
date_time_tool = DateTimeTool()
result = date_time_tool.invoke({})
print(result)
```

**Expected Output:**

```plaintext
The current time is YYYY-MM-DDTHH:MM:SS.SSSSSS+ZZ:ZZ (actual time will vary)
```

### Invoking a `ReactAgent` (Synchronous)

The `ReactAgent` class provides a synchronous interface for invoking the agent and processing its output.

```python
import os
from langchain_core.messages import HumanMessage, SystemMessage
from rich.pretty import pprint
from ai_librarian_core.agents.react.synchronous import ReactAgent
from ai_librarian_core.models.llm_config import LLMConfig
from ai_librarian_core.tools.tools import init_built_in_tools

# Set environment variables (replace with your actual keys)
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
os.environ["GOOGLE_API_KEY"] = "your_google_api_key"
os.environ["GOOGLE_CSE_ID"] = "your_google_cse_key"

# Initialize tools
tools = init_built_in_tools()

# Create and run the ReactAgent
react_agent = ReactAgent(tools=tools)
messages, used_tools = react_agent.run(
    messages=[
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(
            content="I'm learning how to build AI agents. Could you help me find online tutorials and some educational videos?"
        ),
    ],
    thread_id="test-1234567890",
    llm_config=LLMConfig(model="openai:gpt-4o-mini", temperature=1.0, max_tokens=1000),
)

pprint(messages)
pprint(used_tools)
```

### Streaming from a `ReactAgent` (Synchronous)

The `ReactAgent` also supports real-time streaming of responses.

```python
import os
from ai_librarian_core.agents.react.synchronous import ReactAgent
from ai_librarian_core.models.llm_config import LLMConfig
from ai_librarian_core.tools.tools import init_built_in_tools
from langchain_core.messages import HumanMessage, SystemMessage
from rich.pretty import pprint

# Set environment variables (replace with your actual keys)
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
os.environ["GOOGLE_API_KEY"] = "your_google_api_key"
os.environ["GOOGLE_CSE_ID"] = "your_google_cse_key"

# Initialize tools
tools = init_built_in_tools()

# Create and stream from the ReactAgent
agent = ReactAgent(tools=tools)
result = agent.stream(
    [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(
            content="I'm learning how to build AI agents. Could you help me find online tutorials and some educational videos?"
        ),
    ],
    thread_id="test-1234567890",
    llm_config=LLMConfig(model="openai:gpt-4o-mini", temperature=1.0, max_tokens=1000),
)

for chunk in result:
    pprint(chunk)
```

### Invoking an `AsyncReactAgent` (Asynchronous)

For asynchronous operations, use the `AsyncReactAgent` class.

```python
import asyncio
import os
from ai_librarian_core.agents.react.asynchronous import AsyncReactAgent
from langchain_core.messages import HumanMessage, SystemMessage
from rich.pretty import pprint
from ai_librarian_core.models.llm_config import LLMConfig
from ai_librarian_core.tools.tools import init_built_in_tools

# Set environment variables (replace with your actual keys)
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
os.environ["GOOGLE_API_KEY"] = "your_google_api_key"
os.environ["GOOGLE_CSE_ID"] = "your_google_cse_key"

# Initialize tools
tools = init_built_in_tools()

# Create and run the AsyncReactAgent
agent = AsyncReactAgent(tools=tools)
async def run_async_agent():
    messages, used_tools = await agent.run(
        [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(
                content="I'm learning how to build AI agents. Could you help me find online tutorials and some educational videos?"
            ),
        ],
        thread_id="test-1234567890",
        llm_config=LLMConfig(model="openai:gpt-4o-mini", temperature=1.0, max_tokens=1000),
    )
    pprint(messages)
    pprint(used_tools)

asyncio.run(run_async_agent())
```

### Streaming from an `AsyncReactAgent` (Asynchronous)

Asynchronous streaming for real-time response generation.

```python
import asyncio
import os
from ai_librarian_core.agents.react.asynchronous import AsyncReactAgent
from ai_librarian_core.models.llm_config import LLMConfig
from ai_librarian_core.tools.tools import init_built_in_tools
from langchain_core.messages import HumanMessage, SystemMessage
from rich.pretty import pprint

# Set environment variables (replace with your actual keys)
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
os.environ["GOOGLE_API_KEY"] = "your_google_api_key"
os.environ["GOOGLE_CSE_ID"] = "your_google_cse_key"

# Initialize tools
tools = init_built_in_tools()

# Create and stream from the AsyncReactAgent
agent = AsyncReactAgent(tools=tools)
async def stream_async_agent():
    result = await agent.stream(
        [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(
                content="I'm learning how to build AI agents. Could you help me find online tutorials and some educational videos?"
            )
        ],
        thread_id="test-1234567890",
        llm_config=LLMConfig(model="openai:gpt-4o-mini", temperature=1.0, max_tokens=1000),
    )
    async for chunk in result:
        pprint(chunk)

asyncio.run(stream_async_agent())
```

## TODO

1.  Deep search agent implementation.
2.  MCP (Multi-hop Reasoning) support.
3.  Tool for searching resources on the National Library of Public Information (國立公共資訊圖書館).
