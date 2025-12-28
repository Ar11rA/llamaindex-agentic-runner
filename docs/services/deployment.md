# Deployment Guide

This guide details how to deploy the LlamaIndex Agents application using Docker and Docker Compose. It covers the build process, environment configuration, and production considerations.

## Docker Architecture

The application is containerized using multi-stage Docker builds to ensure small, secure images.

### 1. Backend Image (`agent/Dockerfile`)
-   **Base**: `python:3.12-slim` (Debian-based for `asyncpg`/`glibc` compatibility).
-   **Builder Stage**: Installs `uv`, creates a virtual environment, and installs dependencies.
-   **Production Stage**: Copies the virtual environment and application code. Runs `uvicorn` with production flags (proxy headers, access logs).

### 2. Frontend Image (`agent-ui/Dockerfile`)
-   **Base**: `node:20-alpine` -> `nginx:alpine`.
-   **Builder Stage**: Installs npm dependencies and builds the React app (`npm run build`).
-   **Production Stage**: Copies the built `dist/` folder to Nginx's html directory.
-   **Nginx Config**: Uses a custom `nginx.conf` to serve the SPA and proxy `/api` requests to the backend.

## Deployment with Docker Compose

The simplest way to deploy is using the provided `docker-compose.yml`.

### Prerequisites
-   Docker Engine
-   Docker Compose (v2)

### Steps

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-org/llamaindex-agents.git
    cd llamaindex-agents
    ```

2.  **Environment Setup**:
    Create a `.env` file with production secrets.
    ```bash
    cp .env.example .env
    ```
    *Update keys in `.env`:*
    ```properties
    OPENAI_API_KEY=sk-...
    PHOENIX_ENABLED=true
    PHOENIX_BATCH_PROCESSOR=true  # Enable for production performance
    MEMORY_DATABASE_URI=postgresql+asyncpg://postgres:postgres@postgres:5432/llamaindex_agents
    ```

3.  **Build and Run**:
    ```bash
    docker-compose up --build -d
    ```

### Services Started

| Service | Internal Port | External Port | Description |
| :--- | :--- | :--- | :--- |
| `frontend` | 3000 | 3000 | Nginx server hosting the React UI |
| `backend` | 6001 | 6001 | FastAPI server |
| `postgres` | 5432 | 5432 | Database |
| `phoenix` | 6006 | 6006 | Observability UI |

## Production Configurations

### Nginx Reverse Proxy (`agent-ui/nginx.conf`)

The frontend container includes an Nginx instance configured for:
-   **SPA Routing**: Redirects all 404s to `index.html` (for React Router).
-   **API Proxying**: Forwards `/api/*` requests to `http://backend:6001`.
-   **SSE Support**: Disables buffering and timeouts for Server-Sent Events (critical for streaming).
-   **Compression**: Gzip enabled for text/js/css.
-   **Security**: Sets standard headers (`X-Frame-Options`, `X-Content-Type-Options`).

### Backend Uvicorn Settings

The backend runs with:
```bash
uvicorn main:app --host 0.0.0.0 --port 6001 --proxy-headers --forwarded-allow-ips '*'
```
-   `--proxy-headers`: Crucial when running behind Nginx/Load Balancer to correctly identify client IPs.
-   `--forwarded-allow-ips '*'`: Trusts the forwarded headers (safe within the private Docker network).

## Cloud Deployment (Example: AWS/GCP/Azure)

To deploy to a cloud provider (e.g., AWS ECS, Google Cloud Run, Azure Container Apps), you typically deploy the **Backend** and **Frontend** as separate services.

### 1. Database
-   **Do not** use the `postgres` container in production.
-   Provision a managed database (RDS, Cloud SQL) and update `MEMORY_DATABASE_URI`.

### 2. Backend
-   Build and push the Docker image.
-   Set environment variables in the cloud console.
-   Expose port 6001.

### 3. Frontend
-   Build and push the Docker image.
-   Update `nginx.conf` (if needed) or configure the cloud load balancer to route `/api` traffic to the Backend service.

### 4. Observability
-   Phoenix can be deployed as a sidecar or a standalone service.
-   Ensure `PHOENIX_ENDPOINT` is accessible from the Backend service.

## Health Checks

-   **Backend**: `GET /health` (Returns `{"status": "healthy"}`)
-   **Frontend**: Nginx default health check.
-   **Postgres**: `pg_isready`

Docker Compose is configured to wait for `postgres` to be healthy before starting the `backend`.

