#!/bin/bash

echo "Discord Environment Setup"
echo "========================="
echo ""

# Prompt for credentials
read -p "Enter your Discord Application ID (Client ID): " APP_ID
read -p "Enter your Discord Client Secret: " CLIENT_SECRET
read -p "Enter your Discord Public Key (optional, press Enter to skip): " PUBLIC_KEY

# Create .env file
cat > .env << ENVEOF
# Gmail Configuration (existing)
GMAIL_ACCESS_TOKEN=your-access-token
GMAIL_REFRESH_TOKEN=your-refresh-token
GMAIL_TOKEN_URI=https://oauth2.googleapis.com/token
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_SCOPES=https://mail.google.com/
GMAIL_UNIVERSE_DOMAIN=googleapis.com
GMAIL_ACCOUNT=
GMAIL_TOKEN_EXPIRY=YYYY-MM-DDTHH:MM:SSZ

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID=${APP_ID}
DISCORD_CLIENT_SECRET=${CLIENT_SECRET}
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback
DISCORD_PUBLIC_KEY=${PUBLIC_KEY}

# Database Configuration
DISCORD_DB_PATH=discord_credentials.db
DATABASE_URL=sqlite+aiosqlite:///./discord_auth.db
ENVEOF

echo ""
echo "✓ .env file created successfully!"
echo ""
echo "Important next steps:"
echo "1. Go to https://discord.com/developers/applications/${APP_ID}/oauth2/general"
echo "2. Add this redirect URI: http://localhost:8000/auth/callback"
echo "3. Under OAuth2 → URL Generator, select scopes:"
echo "   - identify"
echo "   - guilds"
echo "   - messages.read"
echo ""
echo "Your .env file is ready to use!"
