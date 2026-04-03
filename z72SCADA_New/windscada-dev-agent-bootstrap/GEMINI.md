# Project Overview

This project is a "WindSCADA Dev Agent (Bootstrap)", a demonstration of an agent-driven development project scaffold. It's a Python-based FastAPI application designed to provide basic functionalities like health checks and logging, with a clear path for future expansion into areas like OPC UA data acquisition and alarm aggregation. The project emphasizes structured development with documentation and CI/CD integration.

## Technologies Used

*   **Backend:** Python, FastAPI, Uvicorn
*   **Dependency Management:** pip
*   **Data Validation:** Pydantic
*   **Testing:** Pytest
*   **Containerization:** Docker
*   **CI/CD:** GitHub Actions

## Building and Running

### Local Development

1.  **Set up a virtual environment (optional but recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the API server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000` by default.

### Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t windscada-dev-agent .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 windscada-dev-agent
    ```
    The API will be available at `http://localhost:8000`.

## Testing

To run the unit tests:

```bash
pytest -q
```

## Development Conventions

*   **Agent-Driven Development:** The project follows an "agent-driven" approach, with `project.md`, `roadmap.md`, `todo.md`, and `development.log` used for project management and tracking.
*   **Documentation:** The `docs/` directory contains various documentation, including discovery, inception, and Architectural Decision Records (ADR).
*   **Code Style:** While not explicitly defined by a linter config, the Python code in `app/main.py` and `tests/test_health.py` follows a clean and readable style.
*   **Continuous Integration:** GitHub Actions are configured to run tests automatically on every push and pull request, ensuring code quality and preventing regressions.
*   **VS Code Integration:** The `.vscode/` directory suggests VS Code specific tasks or configurations are available for developers.
