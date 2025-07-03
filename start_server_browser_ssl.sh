#!/bin/bash

# E2E Testing MCP Server Startup with Browser SSL Bypass Only
echo "🚀 Starting E2E Testing MCP Server with browser SSL bypass..."

# Set project path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "🌐 Browser SSL bypass enabled for automation"
echo "ℹ️ Azure OpenAI client remains unchanged"

# Start the server
echo "📡 Launching MCP server..."
python src/main.py
