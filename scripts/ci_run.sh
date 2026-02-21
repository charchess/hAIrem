#!/bin/bash
# hAIrem CI/CD - Unified Quality Gate Script
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting hAIrem Quality Gate...${NC}"

# 1. Secret Scanning (Gitleaks)
echo -e "\n${GREEN}🔍 Phase 1: Secret Scanning (Gitleaks)${NC}"
if command -v gitleaks &> /dev/null; then
    gitleaks detect --verbose --redact
else
    echo -e "${RED}⚠️ Gitleaks not found. Running via Docker...${NC}"
    docker run -v $(pwd):/path zricethezav/gitleaks:latest detect --source="/path" --verbose --redact
fi

# 2. Static Analysis (Ruff)
echo -e "\n${GREEN}⚡ Phase 2: Analysis (Ruff)${NC}"
pip install -q ruff --break-system-packages
ruff check apps/h-core/src apps/h-bridge/src

# 3. Type Checking (Mypy)
echo -e "\n${GREEN}📊 Phase 3: Type Checking (Mypy)${NC}"
pip install -q mypy types-PyYAML redis pydantic types-requests --break-system-packages
echo "Checking H-Core..."
mypy apps/h-core/src --ignore-missing-imports
echo "Checking H-Bridge..."
mypy apps/h-bridge/src --ignore-missing-imports

# 4. Unit Tests (Pytest — fast, no real services required)
echo -e "\n${GREEN}🧪 Phase 4a: Unit Tests (Pytest)${NC}"
export PYTHONPATH=$PYTHONPATH:$(pwd)/apps/h-core:$(pwd)/apps/h-core/src:$(pwd)/apps/h-bridge
cd apps/h-core && python3 -m pytest tests/ -m "not integration" -q --tb=short && cd ../..

# 4b. Integration Tests (require Redis + SurrealDB)
echo -e "\n${GREEN}🧪 Phase 4b: Integration Tests (Pytest — requires services)${NC}"
if redis-cli ping > /dev/null 2>&1; then
    cd apps/h-core && python3 -m pytest tests/ -m "integration" -q --tb=short && cd ../..
else
    echo -e "${RED}⚠️ Skipping integration tests: Redis not available.${NC}"
fi

# 5. Master Regression (E2E)
echo -e "\n${GREEN}🏆 Phase 5: Master Regression (E2E)${NC}"
# Note: Requires a running Redis server
if pgrep redis-server > /dev/null; then
    python3 scripts/master_regression_v3.py
else
    echo -e "${RED}⚠️ Skipping E2E: No Redis server found.${NC}"
fi

# 6. UI Regression (Playwright)
echo -e "\n${GREEN}🎭 Phase 6: UI Regression (Playwright)${NC}"
TARGET_URL="http://192.168.200.61:8000"

if curl -s "$TARGET_URL/" > /dev/null; then
    # Ensure playwright browsers are installed only if needed
    # python3 -m playwright install chromium
    export APP_URL="$TARGET_URL"
    python3 tests/validate_epic_7.py
else
    echo -e "${RED}⚠️ Skipping UI Test: H-Bridge ($TARGET_URL) not accessible. Is the Docker stack up?${NC}"
fi

# 7. Build Integrity (Docker)
echo -e "\n${GREEN}🐳 Phase 7: Build Integrity (Docker)${NC}"
docker compose build --quiet

echo -e "\n${GREEN}✅ Quality Gate passed successfully!${NC}"

