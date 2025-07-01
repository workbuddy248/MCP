#!/bin/bash
cd /Users/varsaraf/Downloads/e2e-testing-mcp-server
sudo mkdir -p data logs
sudo chown -R $(whoami) data logs
chmod 755 data logs
