#!/bin/bash
# hAIrem Deployment Script
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting hAIrem Deployment...${NC}"

# 1. Pull latest changes (if in a git repo)
if [ -d .git ]; then
    echo -e "\n${GREEN}📥 Pulling latest changes from Git...${NC}"
    git pull
fi

# 2. Rebuild and Restart Containers
echo -e "\n${GREEN}🐳 Rebuilding and restarting containers...${NC}"
docker compose up -d --build

# 3. Health Check
echo -e "\n${GREEN}🔍 Running Health Check...${NC}"
if [ -f scripts/check_health.py ]; then
    python3 scripts/check_health.py
else
    echo -e "${RED}⚠️ Health check script (scripts/check_health.py) not found. Skipping...${NC}"
fi

echo -e "\n${GREEN}✨ Deployment complete!${NC}"
