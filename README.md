# My First DevOps Project: Containerized Flask Web Application

Welcome to your first hands-on DevOps project! This repository contains a production-ready starter setup for containerizing a Python Flask application with Docker and managing multi-service environments with Docker Compose.

---

## 📁 Project Structure

```text
antigravity-devops/
├── app.py              # Main Flask application with endpoints
├── requirements.txt    # Python dependencies
├── Dockerfile          # Instructions to build the Docker image
├── .dockerignore       # Files and directories ignored during Docker build
├── compose.yaml        # Declarative Docker Compose specification
└── README.md           # Documentation and guides
```

---

## 🔍 Purpose of Every File

| File | Purpose | Why It Matters in DevOps |
| :--- | :--- | :--- |
| **`app.py`** | The web application code written in Flask. Defines the routes (`/` and `/health`) and starts the server on port 5000. | In DevOps, we manage, package, deploy, and monitor applications. This is the source application we are operationalizing. |
| **`requirements.txt`** | Lists the third-party Python packages required (`Flask`). | Ensures deterministic, reproducible builds across development, staging, and production environments. |
| **`Dockerfile`** | Step-by-step recipe for packaging the application and its runtime into an isolated container image. | Core building block of modern DevOps and CI/CD pipelines. It ensures that the app runs the exact same way on any machine ("works on my machine" problem solved). |
| **`.dockerignore`** | Specifies files and directories that Docker should ignore when copying files into the image. | Keeps images lean, speeds up Docker builds, and prevents sensitive files (like `.env`) or cache files (`__pycache__`) from leaking into the container image. |
| **`compose.yaml`** | Declarative configuration defining service orchestration, networking, restart policies, resource limits, and automated health checks. | Eliminates lengthy, error-prone manual `docker run` commands; enables consistent, reproducible single-command deployments on AWS EC2 or local hosts. |
| **`README.md`** | Human-readable documentation for developers and operators. | Critical for onboarding team members, documenting deployment steps, and recording operational procedures. |

---

## 🚀 Application Endpoints

1. **`GET /`**
   - **Response**: `<h1>Welcome to My First DevOps Project!</h1>`
   - **Purpose**: Verifies that the web server is running and can serve public web traffic.

2. **`GET /health`**
   - **Response**: `{"status": "healthy", "message": "Application is running smoothly"}`
   - **HTTP Status**: `200 OK`
   - **Purpose**: Used by monitoring tools, load balancers, and container orchestrators (e.g., Kubernetes liveness/readiness probes, Docker Compose health checks) to check system health.

---

## 🛠️ How to Run the Application

### Option A: Running Locally with Python (Without Docker)

1. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Flask server:**
   ```bash
   python3 app.py
   ```

4. **Test the endpoints:**
   - In your browser: Open `http://localhost:5000`
   - In your terminal:
     ```bash
     curl http://localhost:5000/
     curl http://localhost:5000/health
     ```

---

### Option B: Running with Docker Compose (Recommended)

Docker Compose provides a declarative, single-command workflow for building, launching, monitoring, and managing your container on local machines or AWS EC2 instances.

1. **Build the container image:**
   ```bash
   docker compose build
   ```
   * Builds the `devops-flask-app` image defined in `Dockerfile`.

2. **Start the application in detached mode (background):**
   ```bash
   docker compose up -d
   ```
   * Or build and start in one step:
     ```bash
     docker compose up --build -d
     ```

3. **Check container status and health:**
   ```bash
   docker compose ps
   ```
   * Displays the container state, port bindings, and whether the container is `healthy` (evaluated via `/health`).

4. **View live application logs:**
   ```bash
   docker compose logs -f
   ```
   * Follow logs specifically for the Flask app:
     ```bash
     docker compose logs -f flask-app
     ```

5. **Stop the container (without deleting networks/resources):**
   ```bash
   docker compose stop
   ```

6. **Restart the container:**
   ```bash
   docker compose restart
   ```

7. **Tear down the application and custom network:**
   ```bash
   docker compose down
   ```

---

### Option C: Running with Standalone Docker CLI (Reference)

1. **Build the Docker image:**
   ```bash
   docker build -t my-first-devops-app:1.0 .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 5000:5000 --name devops-flask-container my-first-devops-app:1.0
   ```

3. **Verify the container is running:**
   ```bash
   docker ps
   ```

4. **Check container logs:**
   ```bash
   docker logs -f devops-flask-container
   ```

5. **Stop and remove the container:**
   ```bash
   docker stop devops-flask-container
   docker rm devops-flask-container
   ```
