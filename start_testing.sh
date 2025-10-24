#!/bin/bash

echo "🚀 Discord Implementation - Quick Start"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Run ./setup_discord_env.sh first to create it."
    exit 1
fi

echo "✅ .env file found"
echo ""

# Step 1: Run tests
echo "📋 Step 1: Running automated tests..."
echo "--------------------------------------"
./run_tests.sh
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Some tests failed, but continuing..."
fi
echo ""

# Step 2: Check if service is already running
echo "🔍 Step 2: Checking if service is already running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Service is already running on port 8000"
    echo ""
else
    echo "📌 Service not running. Starting it now..."
    echo ""
    echo "Run this command in a separate terminal:"
    echo "----------------------------------------"
    echo "cd src/services/discord_client_service && uv run uvicorn discord_client_service.service:app --reload --port 8000"
    echo "----------------------------------------"
    echo ""
    read -p "Press Enter after you've started the service in another terminal..."
    
    # Check again
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Service is now running!"
    else
        echo "❌ Service still not reachable. Please check the other terminal."
        exit 1
    fi
fi

# Step 3: Test health endpoint
echo ""
echo "🏥 Step 3: Testing health endpoint..."
echo "--------------------------------------"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Step 4: Show next steps
echo ""
echo "✅ Setup complete! Next steps:"
echo "======================================"
echo ""
echo "1️⃣  Set up OAuth redirect URI in Discord:"
echo "   → https://discord.com/developers/applications"
echo "   → Add redirect: http://localhost:8000/auth/callback"
echo ""
echo "2️⃣  Open Swagger UI in your browser:"
echo "   → http://localhost:8000/docs"
echo ""
echo "3️⃣  Initialize OAuth flow:"
echo "   → curl http://localhost:8000/auth/login"
echo "   → Copy the authorization_url and open in browser"
echo "   → After authorizing, copy the 'code' from callback URL"
echo ""
echo "4️⃣  Complete OAuth (replace YOUR_CODE):"
echo "   → curl -X POST http://localhost:8000/auth/callback \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"code\": \"YOUR_CODE\", \"user_id\": \"test_user_123\"}'"
echo ""
echo "5️⃣  Test Discord operations:"
echo "   → curl http://localhost:8000/test_user_123/channels"
echo ""
echo "📖 For detailed instructions, see: QUICK_START.md"
echo ""
