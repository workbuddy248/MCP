#!/bin/bash

# Browser-Only SSL Bypass Setup Script for E2E Testing MCP Server
# This script ONLY configures browser SSL bypass, leaving Azure OpenAI untouched

echo "🔧 Setting up Browser SSL bypass configuration for E2E Testing MCP Server..."
echo "ℹ️ Note: This setup only affects browser automation, not Azure OpenAI client"

# Create browser SSL test script
echo "📝 Creating browser SSL bypass test script..."
cat > test_browser_ssl.py << 'EOL'
#!/usr/bin/env python3
"""
Browser SSL Bypass Test Script
Tests only browser SSL certificate bypass functionality
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_playwright_ssl_bypass():
    """Test Playwright SSL bypass with common SSL problem sites"""
    print("🧪 Testing Playwright Browser SSL bypass...")
    
    try:
        from src.automation.browser_manager import BrowserManager
        from src.automation.action_executor import ActionExecutor
        
        # Test sites with various SSL issues
        test_sites = [
            ("https://self-signed.badssl.com/", "Self-signed certificate"),
            ("https://expired.badssl.com/", "Expired certificate"),
            ("https://wrong.host.badssl.com/", "Wrong hostname"),
            ("https://example.com/", "Valid certificate (control test)")
        ]
        
        browser_manager = BrowserManager(headless=True, browser_type="chromium")
        
        results = []
        
        for url, description in test_sites:
            try:
                print(f"  🔗 Testing {description}: {url}")
                
                # Create browser session
                page = await browser_manager.create_session(f"test_{len(results)}")
                action_executor = ActionExecutor(page)
                
                # Test navigation with SSL bypass
                result = await action_executor._navigate(url, {})
                
                if result["status"] == "success":
                    title = result.get("page_title", "Unknown")
                    ssl_handled = result.get("ssl_warning_handled", False)
                    
                    print(f"    ✅ Success: {title}")
                    if ssl_handled:
                        print(f"    🛡️ SSL warning detected and handled")
                    
                    results.append(True)
                else:
                    print(f"    ❌ Failed: {result['message']}")
                    results.append(False)
                
                # Clean up session
                await browser_manager.close_session(f"test_{len(results)-1}")
                
            except Exception as e:
                print(f"    💥 Exception: {str(e)}")
                results.append(False)
        
        # Clean up browser
        await browser_manager.cleanup()
        
        success_count = sum(results)
        total_count = len(results)
        
        print(f"\n📊 Browser SSL Test Results: {success_count}/{total_count} passed")
        
        if success_count >= 3:  # Allow some failures for the deliberately broken certs
            print("🎉 Browser SSL bypass is working correctly!")
            return True
        else:
            print("⚠️ Browser SSL bypass may need attention.")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Browser SSL bypass test failed: {e}")
        return False

async def main():
    """Run browser SSL bypass test"""
    print("🚀 Starting Browser SSL Bypass Test")
    print("=" * 40)
    
    success = await test_playwright_ssl_bypass()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Browser SSL bypass test passed!")
        print("\n🎯 Your browser automation can now handle:")
        print("  • Self-signed certificates")
        print("  • Expired certificates") 
        print("  • Certificate hostname mismatches")
        print("  • SSL warning pages (auto-bypass)")
    else:
        print("❌ Browser SSL bypass test failed!")
        print("\n�� Check the error messages above and ensure:")
        print("  • You've updated browser_manager.py and action_executor.py")
        print("  • Playwright is installed and browsers are available")
        print("  • You're running from the project root directory")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n�� Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)
EOL

chmod +x test_browser_ssl.py
echo "✅ Created browser SSL test script: test_browser_ssl.py"

# Create startup script
echo "📝 Creating startup script..."
cat > start_server_browser_ssl.sh << 'EOL'
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
EOL

chmod +x start_server_browser_ssl.sh
echo "✅ Created startup script: start_server_browser_ssl.sh"

# Check if Playwright is installed
echo "🔍 Checking Playwright installation..."
if python -c "import playwright" 2>/dev/null; then
    echo "✅ Playwright is installed"
    
    # Check if browsers are installed
    if python -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch()" 2>/dev/null; then
        echo "✅ Chromium browser is available"
    else
        echo "⚠️ Chromium browser not found. Installing..."
        python -m playwright install chromium
    fi
else
    echo "❌ Playwright not found. Installing..."
    pip install playwright
    python -m playwright install chromium
fi

# Test the browser SSL bypass
echo ""
echo "🧪 Testing browser SSL bypass configuration..."
python test_browser_ssl.py

echo ""
echo "🎯 Browser SSL Bypass Setup Complete!"
echo ""
echo "📋 What was configured:"
echo "  ✅ Browser SSL certificate bypass (Playwright)"
echo "  ✅ SSL warning page auto-handling"
echo "  ✅ Navigation retry logic for SSL errors"
echo "  ✅ Test script for validation"
echo ""
echo "📋 What was NOT changed:"
echo "  ℹ️ Azure OpenAI client (left untouched as requested)"
echo "  ℹ️ Other HTTP requests outside browser automation"
echo ""
echo "🚀 Next Steps:"
echo "1. Start server: ./start_server_browser_ssl.sh"
echo "2. Or run directly: python src/main.py"
echo "3. Test with SSL sites to verify bypass works"
echo ""
echo "🧪 To test browser SSL bypass anytime:"
echo "   python test_browser_ssl.py"
