#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_status() {
    if [ $? -eq 0 ]; then
        printf "${GREEN}[OK]${NC} $1\n"
    else
        printf "${RED}[ERROR]${NC} $2\n"
        exit 1
    fi
}

printf "${YELLOW}[INFO]Checking Docker installation...${NC}\n"

# Checking Docker
which docker > /dev/null 2>&1
check_status \
    "Docker is installed" \
    "Docker is not installed or not in PATH\nPlease install Docker first: https://docs.docker.com/get-docker/"

# Checking Docker daemon
docker info > /dev/null 2>&1
check_status \
    "Docker daemon is running" \
    "Docker daemon is not running\nPlease start Docker desktop or Docker service"

printf "${YELLOW}[INFO]Building image obsiflask...${NC}\n"

# Docker building
docker build . -t obsiflask 
check_status \
    "Docker image built successfully: obsiflask" \
    "Docker build failed"

printf "\n"
printf "${GREEN}[DEMO_RUN]${NC} ${YELLOW}<docker run -p 8000:8000 obsiflask>${NC}\n"