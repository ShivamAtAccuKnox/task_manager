# Task Manager

A robust Task Management application built with Django, utilizing Celery for asynchronous background processing. The entire stack is containerized using Docker and Docker Compose for easy deployment and development.

## 🛠 Tech Stack

* **Backend:** Python 3.10, Django
* **Database:** PostgreSQL 15
* **Task Queue:** Celery
* **Message Broker:** RabbitMQ 3 (Management enabled)
* **Caching/Results:** Redis
* **Infrastructure:** Docker & Docker Compose

## 📋 Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop) (Windows/Mac) or Docker Engine (Linux)
* Git

## 🚀 Getting Started

Follow these steps to get the project running locally.

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd task_manager

```

### 2. Environment Configuration

The project uses environment variables to manage sensitive configuration. A template is provided in `example.env`.

Create your local `.env` file:

```bash
# Copy the example file to a real .env file
cp example.env .env

```

*Note: The default values in `example.env` are pre-configured to work with the Docker setup out of the box.*

### 3. Build and Run

Start the entire application stack:

```bash
docker compose up --build

```

*Wait for the logs to stop scrolling. The `web` container depends on `postgres` and `rabbitmq` being healthy before it fully starts.*

### 4. Initialize Database & Data

Once the containers are running, open a **new terminal** window and run these commands to set up the database and populate it with your sample data:

```bash
# 1. Apply database migrations
docker compose exec web python manage.py migrate

# 2. Populate the database with sample users/tasks (using your custom command)
docker compose exec web python manage.py seed_data

# 3. (Optional) Create a specific admin user if needed
docker compose exec web python manage.py createsuperuser

```

**Services will be available at:**

* **Web App:** [http://localhost:8000](https://www.google.com/search?q=http://localhost:8000)
* **RabbitMQ Dashboard:** [http://localhost:15672](https://www.google.com/search?q=http://localhost:15672) (User: `guest`, Pass: `guest`)

---

## 💻 Common Commands

Since the application runs inside Docker, you must execute management commands inside the container.

### View Logs

```bash
# View logs for the web application
docker compose logs -f web

# View logs for celery worker (useful for debugging background tasks)
docker compose logs -f celery_worker

```

### Access Container Shell

If you need to look at files inside the container:

```bash
docker compose exec web /bin/bash

```

### Run Tests

```bash
docker compose exec web python manage.py test

```

---

## 📂 Project Structure

```text
.
├── core/                # Core Django project settings
├── project/             # Main application logic (models, views, tasks)
├── docker-compose.yml   # Orchestration for Web, DB, Redis, RabbitMQ, Celery
├── Dockerfile           # Python environment definition
├── health_check.sh      # Container health verification script
├── manage.py            # Django entry point
├── requirements.txt     # Python dependencies
└── .env                 # Local secrets (Not committed to Git)

```

## ⚠️ Troubleshooting

**1. "Permission Denied" on `health_check.sh**`
If you are running on Windows and see errors related to the health check script, it may be due to line endings (CRLF). Run this to fix it permanently:

```bash
git add --renormalize .

```

**2. Database connection failed**
Ensure the `postgres` container is "healthy". It may take a few seconds to initialize on the first run. The `web` container is configured to wait for it.
