# AI Librarian

## Installation

Follow these steps to install and set up:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/youkwan/ai-librarian.git
    cd ./ai-librarian/backend/
    ```

2.  **Install uv(if not already installed):**
    This project uses [uv](https://github.com/astral-sh/uv) to manage the virtual environment and dependencies. If you don't have uv installed, follow the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

3.  **Create Virtual Environment:**
    In the `backend` directory, run:
    ```bash
    uv venv
    ```

3.  **Activate Virtual Environment:**
    Activate the environment based on your operating system and terminal:

    *   **Linux / macOS (Bash/Zsh):**
        ```bash
        source .venv/bin/activate
        ```
    *   **Windows (PowerShell):**
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```

4.  **Install Dependencies:**
    With the virtual environment activated, run:
    ```bash
    uv pip install .
    ```
    This command reads the `pyproject.toml` file and installs all necessary Python packages.

5.  **Configure Environment Variables:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Then, open the `.env` file in the `backend` directory with a text editor and fill in the required configuration values (e.g., OPENAI API key, LangSmith API key, etc.).

6.  **Start the Application:**
    In the `backend` directory, run:
    ```bash
    uv run .\app\main.py
    ```
    The backend will start and run at http://127.0.0.1:8000

    API documentation can be viewed at:
    - Swagger UI: http://127.0.0.1:8000/docs
    - ReDoc: http://127.0.0.1:8000/redoc

## VSCode/Cursor Setup

This section is optional. You can use `uv` directly without configuring VSCode/Cursor. However, if you use VSCode or Cursor and want to use the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python), you can apply the following settings to help the extension correctly identify and use this project's virtual environment.

1.  **Create Configuration Directory and File:**
    Ensure you are in the root directory of the `ai-librarian` project (the parent directory of `backend`). If the `.vscode` directory and `settings.json` file do not exist, use the appropriate command for your operating system to create them:

    *   **Linux / macOS:**
        ```bash
        # Make sure you are in the ai-librarian/ directory
        mkdir .vscode
        touch .vscode/settings.json
        ```

    *   **Windows (PowerShell):**
        ```powershell
        # Make sure you are in the ai-librarian/ directory
        mkdir .vscode
        if (-not (Test-Path .vscode/settings.json)) { New-Item .vscode/settings.json -ItemType File }
        ```

2.  **Configure Python Interpreter Path:**
    Open the `.vscode/settings.json` file. Copy and paste the following content. **Choose the setting that matches your operating system.**

    *   **For Linux / macOS users:**
        ```json
        {
            "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python"
        }
        ```

    *   **For Windows users:**
        ```json
        {
            "python.defaultInterpreterPath": "${workspaceFolder}\\backend\\.venv\\Scripts\\python.exe"
        }
        ```

After completing these steps, VSCode should automatically detect and select the Python virtual environment located in `backend/.venv`.