#!/bin/bash

# Test script for Railway deployment
# Usage: ./test_railway.sh <your-railway-url>
# Example: ./test_railway.sh https://your-app-name.up.railway.app

if [ $# -eq 0 ]; then
    echo "Usage: $0 <your-railway-url>"
    echo "Example: $0 https://your-app-name.up.railway.app"
    exit 1
fi

BASE_URL=$1
echo "🚀 Testing Railway deployment: $BASE_URL"
echo "=================================================="

# Test root endpoint
echo "📡 Testing root endpoint..."
curl -s "$BASE_URL/" | jq . 2>/dev/null || curl -s "$BASE_URL/"
echo -e "\n"

# Test health check
echo "🏥 Testing health check..."
curl -s "$BASE_URL/v1/healthz" | jq . 2>/dev/null || curl -s "$BASE_URL/v1/healthz"
echo -e "\n"

# Test account status
echo "💰 Testing account status..."
curl -s "$BASE_URL/v1/account" | jq . 2>/dev/null || curl -s "$BASE_URL/v1/account"
echo -e "\n"

# Test API docs
echo "📚 Testing API documentation..."
curl -s "$BASE_URL/docs" | head -20
echo -e "\n"

echo "✅ Endpoint testing complete!"
echo "🔗 If all tests pass, your Railway deployment is working correctly."
