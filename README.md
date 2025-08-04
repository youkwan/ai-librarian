# AI Librarian

`ai-librarian` is a web-based application designed to integrate AI agents into libraries, offering intelligent agents with essential functionalities such as multi-hop tool use, memory management, real-time streaming capabilities, and Live2D avatar control.

## Key Features

*   **Multi-hop Tool Use**: Enables agents to call multiple tools in sequence to generate comprehensive responses.
*   **Streaming Support**: Delivers real-time token streaming for immediate agent responses.
*   **Memory Management**: Implements conversational memory systems for stateful and context-aware AI interactions.

## Built-in Tools

The following tools are readily available:

*   **Google Books**: Search for books and publications on Google Books.
*   **Google Search**: Perform web searches using Google.
*   **YouTube Search**: Search for videos on YouTube.
*   **Date Time**: Retrieve the current date and time.
*   **arXiv Search**: Search for academic papers and preprints on arXiv.
*   **DuckDuckGo Search**: Conduct web searches using DuckDuckGo.
*   **Wikipedia Search**: Access information from Wikipedia.
*   **OpenWeatherMap**: Obtain current weather data for specified locations.
*   **NCL Crawler**: A specialized web crawler for the National Central Library of Taiwan (國家圖書館).


## Structure

```
ai-librarian/
├── backend/
│    ├── ai_librarian_monorepo/
│    │   ├── ai_librarian_core/ # Core functionalities of the AI librarian
│    │   ├── ai_librarian_apis/ # RESTful API service that provides interaction with ai_librarian_core
│    │   └── ...
│    └── ...
├── frontend/ # Frontend of the application
└── README.md
```

## Installation

Follow these steps to install and set up:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/youkwan/ai-librarian.git
    ```

2.  **Configure Environment Variables:**

    First, navigate to the `ai_librarian_apis` directory:
    ```bash
    cd ./backend/ai_librarian_monorepo/ai_librarian_apis/
    ```

    Then copy the example environment file and fill in the required configuration values (e.g., OPENAI API key, GOOGLE CSE ID, etc.):
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file with a text editor and fill in the required configuration values (e.g., OPENAI API key, LangSmith API key, etc.).

    > Note: The `.env` file is used to store the configuration values for the application. It is not included in the repository to prevent sensitive information from being exposed.

3.  **Start the Application:**
    
    Navigate back to project root directory:
    ```bash
    cd ../../..
    ```

    Run application with docker compose:
    ```bash
    docker compose up
    ```

    > Note: The application will start and run at http://localhost:8000.

    > By default, the API documentation is available at:
    > - ReDoc: http://localhost:8000/redoc
    > - Swagger UI: http://localhost:8000/docs