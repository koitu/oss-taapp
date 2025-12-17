#!/bin/bash

echo "=== Docker Setup Test ==="
echo ""

# Check if Docker is running
echo "1. Checking if Docker is running..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"
echo ""

# Check if .env file exists
echo "2. Checking for .env file..."
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your actual API keys before running docker-compose"
    exit 1
fi
echo "✅ .env file exists"
echo ""

# Check required environment variables
echo "3. Checking required environment variables..."
source .env
required_vars=("DISCORD_BOT_TOKEN" "TRELLO_API_KEY" "TRELLO_API_SECRET")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your-"* ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Missing or placeholder values for:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo "⚠️  Please update .env with actual values"
    exit 1
fi
echo "✅ Required environment variables are set"
echo ""

# Build the image
echo "4. Building Docker image (this may take a few minutes)..."
if docker build -t ospsd-service:latest . > /dev/null 2>&1; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed. Check output above."
    exit 1
fi
echo ""

# Check image size
echo "5. Checking image size..."
size=$(docker images ospsd-service:latest --format "{{.Size}}")
echo "✅ Image size: $size"
echo ""

echo "=== All checks passed! ==="
echo ""
echo "Next steps:"
echo "  1. Start the service: docker-compose up -d"
echo "  2. View logs: docker-compose logs -f"
echo "  3. Check health: curl http://localhost:8000/health"
echo "  4. Stop service: docker-compose down"
