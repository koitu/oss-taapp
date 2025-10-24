#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Discord Implementation Test Suite"
echo "=========================================="
echo ""

# Function to run a test and check result
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${YELLOW}Running: ${test_name}${NC}"
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Track results
passed=0
failed=0

# Layer 1: Chat Client API
echo ""
echo "Layer 1: Chat Client API"
echo "------------------------"
if run_test "Chat Client API Tests" "PYTHONPATH=src/chat_client_api/src:\$PYTHONPATH uv run pytest src/chat_client_api/tests/ -q"; then
    ((passed++))
else
    ((failed++))
fi

# Layer 2: Discord Client Implementation
echo ""
echo "Layer 2: Discord Client Implementation"
echo "---------------------------------------"
if run_test "Discord Client Tests" "PYTHONPATH=src/discord_client_impl/src:src/chat_client_api/src:\$PYTHONPATH uv run pytest src/discord_client_impl/tests/test_discord_impl.py -q"; then
    ((passed++))
else
    ((failed++))
fi

# Layer 3: Database Layer
echo ""
echo "Layer 3: Database Layer"
echo "-----------------------"
if run_test "Database Tests" "uv run pytest src/discord_client_impl/tests/test_database.py -q"; then
    ((passed++))
else
    ((failed++))
fi

# Type Checking
echo ""
echo "Type Checking (Mypy)"
echo "--------------------"
if run_test "chat_client_api mypy" "uv run mypy src/chat_client_api/src --explicit-package-bases"; then
    ((passed++))
else
    ((failed++))
fi

if run_test "discord_client_impl mypy" "uv run mypy src/discord_client_impl/src --explicit-package-bases"; then
    ((passed++))
else
    ((failed++))
fi

if run_test "discord_client_service mypy" "uv run mypy src/services/discord_client_service/src --explicit-package-bases"; then
    ((passed++))
else
    ((failed++))
fi

if run_test "discord_client_service_adapter mypy" "uv run mypy src/discord_client_service_adapter/src --explicit-package-bases"; then
    ((passed++))
else
    ((failed++))
fi

# Linting
echo ""
echo "Linting (Ruff)"
echo "--------------"
if run_test "chat_client_api ruff" "uv run ruff check src/chat_client_api"; then
    ((passed++))
else
    ((failed++))
fi

if run_test "discord_client_impl ruff" "uv run ruff check src/discord_client_impl"; then
    ((passed++))
else
    ((failed++))
fi

if run_test "discord_client_service ruff" "uv run ruff check src/services/discord_client_service"; then
    ((passed++))
else
    ((failed++))
fi

if run_test "discord_client_service_adapter ruff" "uv run ruff check src/discord_client_service_adapter"; then
    ((passed++))
else
    ((failed++))
fi

# Summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $passed${NC}"
echo -e "${RED}Failed: $failed${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set up Discord OAuth2 credentials (see TESTING.md)"
    echo "2. Run: cd src/services/discord_client_service && uv run uvicorn discord_client_service.service:app --reload"
    echo "3. Test manually with curl (see TESTING.md)"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
