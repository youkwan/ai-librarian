# backend
## Installation

Follow these steps to install and set up:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/youkwan/ai-librarian.git
    cd ai-librarian/backend/
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Then, open the `.env` file with a text editor and fill in the required configuration values (e.g., OPENAI API key, LangSmith API key, etc.).

3.  **Install uv(if not already installed):**
    This project uses [uv](https://github.com/astral-sh/uv) to manage the virtual environment and dependencies. If you don't have uv installed, follow the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

4.  **Start the Application:**
    In the `backend` directory, run:
    ```bash
    uv run ./app/main.py
    ```
    This command reads the `pyproject.toml` file and installs all necessary Python packages. The backend will start and run at http://127.0.0.1:8000

    > Note: By default, the API documentation is available at:
    > - ReDoc: http://127.0.0.1:8000/redoc
    > - Swagger UI: http://127.0.0.1:8000/docs
