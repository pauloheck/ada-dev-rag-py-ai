# RAG System with FastAPI

This project implements a Retrieval Augmented Generation (RAG) system using FastAPI, LangChain, and ChromaDB.

## Prerequisites

- Python 3.12 or higher
- Poetry (Python package manager)
- OpenAI API key

## Installation

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ada-dev-rag-py-ai
   ```

3. **Install dependencies using Poetry**:
   ```bash
   poetry install
   ```

4. **Configure environment variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     copy .env.example .env
     ```
   - Edit `.env` and add your OpenAI API key and other required variables:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

## Running the Application

1. **Activate the Poetry shell**:
   ```bash
   poetry shell
   ```

2. **Run the FastAPI application**:
   ```bash
   poetry run python -m uvicorn run:app --reload
   ```

   The application will be available at:
   - API: http://127.0.0.1:8000
   - Documentation: http://127.0.0.1:8000/docs
   - Alternative docs: http://127.0.0.1:8000/redoc

## Project Structure

```
ada-dev-rag-py-ai/
├── src/
│   └── ada_dev_rag_py_ai/
│       ├── api.py           # FastAPI application and endpoints
│       ├── core.py          # Core RAG functionality
│       ├── main.py         # Application initialization
│       └── image_batch_processor.py  # Image processing module
├── tests/                  # Test files
├── .env                    # Environment variables
├── poetry.lock            # Lock file for dependencies
├── pyproject.toml         # Project configuration and dependencies
├── README.md             # This file
└── run.py                # Application entry point
```

## Development

- **Run tests**:
  ```bash
  poetry run pytest
  ```

- **Format code**:
  ```bash
  poetry run black .
  ```

- **Check linting**:
  ```bash
  poetry run flake8
  ```

## Troubleshooting

1. **Module not found errors**:
   - Ensure you're running the application within Poetry's virtual environment:
     ```bash
     poetry shell
     ```
   - Verify the package is installed in development mode:
     ```bash
     poetry install
     ```

2. **OpenAI API errors**:
   - Check if your API key is correctly set in the `.env` file
   - Verify the API key is being loaded properly

3. **Port already in use**:
   - Change the port using the `--port` flag:
     ```bash
     poetry run python -m uvicorn run:app --reload --port 8001
     ```

## Additional Documentation

- [ROADMAP.md](ROADMAP.md) - Project roadmap and future plans
- [tasks.md](tasks.md) - Current tasks and implementation status
