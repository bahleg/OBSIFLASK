#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_status() {
    if [ $? -eq 0 ]; then
        echo "${GREEN}[OK]${NC} $1"
    else
        echo "${RED}[ERROR]${NC} $2"
        exit 1
    fi
}

echo "${YELLOW}[INFO]Checking Docker installation...${NC}"

# Проверка наличия Docker
which docker > /dev/null 2>&1
check_status \
    "Docker is installed" \
    "Docker is not installed or not in PATH\nPlease install Docker first: https://docs.docker.com/get-docker/"

# Проверка работы Docker daemon
docker info > /dev/null 2>&1
check_status \
    "Docker daemon is running" \
    "Docker daemon is not running\nPlease start Docker desktop or Docker service"

echo "${YELLOW}[INFO]Building image obsiflask...${NC}"

# Сборка Docker образа
docker build . -t obsiflask > /dev/null 2>&1
check_status \
    "Docker image built successfully: obsiflask" \
    "Docker build failed"

echo ""
echo "${GREEN}[DEMO_RUN]${NC} ${YELLOW}<docker run -p 8000:8000 obsiflask>${NC}"