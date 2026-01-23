#!/bin/bash

# ==========================================
# Docker Stack Health Checker
# ==========================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting System Health Check...${NC}"
echo "----------------------------------------"

# 1. Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}[CRITICAL] Docker is not running!${NC}"
  exit 1
fi

# Function to check a container's health status
check_container() {
    service_name=$1
    # Get container ID based on service name (adjusting for docker-compose naming)
    container_id=$(docker compose ps -q $service_name)
    
    if [ -z "$container_id" ]; then
        echo -e "${RED}[FAIL] $service_name: Container not found (Is it running?)${NC}"
        return
    fi

    # Check State
    state=$(docker inspect -f '{{.State.Status}}' $container_id)
    
    # Check Health (if configured)
    health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' $container_id)

    if [ "$state" == "running" ]; then
        if [ "$health" == "healthy" ]; then
             echo -e "${GREEN}[OK]   $service_name${NC} (Running & Healthy)"
        elif [ "$health" == "N/A" ]; then
             echo -e "${GREEN}[OK]   $service_name${NC} (Running)"
        else
             echo -e "${RED}[WARN] $service_name${NC} is Running but Health is: $health"
        fi
    else
        echo -e "${RED}[FAIL] $service_name${NC} is $state"
    fi
}

# 2. Check Container Statuses
echo "Checking Containers..."
check_container "postgres"
check_container "redis"
check_container "rabbitmq"
check_container "vault"
check_container "aws_s3"   # MinIO
check_container "web"
check_container "celery_worker"

echo "----------------------------------------"

# 3. Check Network Endpoints (Curl)
echo "Checking Service Endpoints..."

check_url() {
    name=$1
    url=$2
    if curl --output /dev/null --silent --head --fail --max-time 2 "$url"; then
        echo -e "${GREEN}[OK]   $name endpoint is reachable ($url)${NC}"
    else
        # Try GET if HEAD fails (some services like MinIO prefer GET)
        if curl --output /dev/null --silent --fail --max-time 2 "$url"; then
            echo -e "${GREEN}[OK]   $name endpoint is reachable ($url)${NC}"
        else
            echo -e "${RED}[FAIL] $name endpoint is DOWN ($url)${NC}"
        fi
    fi
}

# Django Web
check_url "Django Web" "http://localhost:8000"

# MinIO Health (Standard MinIO health endpoint)
check_url "MinIO (S3)" "http://localhost:9000/minio/health/live"

# Vault Health (Vault returns JSON status)
check_url "Vault" "http://localhost:8200/v1/sys/health"

# RabbitMQ Management
check_url "RabbitMQ UI" "http://localhost:15672"

echo "----------------------------------------"

# 4. Celery Deep Check
echo "Checking Celery Worker Connection..."
# We execute a command inside the container to ping the broker
if docker compose exec celery_worker celery -A core inspect ping > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]   Celery Worker is connected to RabbitMQ${NC}"
else
    echo -e "${RED}[FAIL] Celery Worker cannot connect to Broker!${NC}"
fi

echo "----------------------------------------"
echo -e "${YELLOW}Health Check Complete.${NC}"