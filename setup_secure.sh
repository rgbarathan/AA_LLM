#!/bin/bash

# Security Setup Script for Telecom Architecture Advisor
# This script helps you set up the project securely

echo "🔒 Telecom Architecture Advisor - Security Setup"
echo "================================================"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "⚠️  Warning: .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Your existing .env file was not modified."
        exit 0
    fi
fi

# Copy template
echo "📝 Creating .env file from template..."
cp .env.example .env

# Prompt for API key
echo ""
echo "🔑 Please enter your Google Gemini API key"
echo "   (Get one from: https://makersuite.google.com/app/apikey)"
echo ""
read -p "API Key: " api_key

# Validate input
if [ -z "$api_key" ]; then
    echo "❌ Error: API key cannot be empty"
    rm .env
    exit 1
fi

# Update .env file
sed -i.bak "s/your_gemini_api_key_here/$api_key/" .env
rm .env.bak 2>/dev/null || true

echo ""
echo "✅ .env file created successfully!"
echo ""

# Install dependencies
read -p "Do you want to install Python dependencies now? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
    echo "✅ Dependencies installed!"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "⚠️  Security Reminders:"
echo "   • Never commit your .env file to version control"
echo "   • Never share your API key with others"
echo "   • Read SECURITY.md for best practices"
echo ""
echo "🚀 You can now run the application:"
echo "   streamlit run streamlit_app.py"
echo ""
