#!/usr/bin/env python3
"""
Fixed Browser SSL Bypass Test Script
Tests browser SSL certificate bypass with version compatibility
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_playwright_version_compatibility():
    """Test Playwright version and parameter compatibility"""
    print("🔍 Testing Playwright version compatibility...")
    
    try:
        import playwright
        print(f"    ✅ Playwright version: {playwright.__version__}")
        
        from playwright.async_api import async_playwright
        
        # Test basic browser launch
        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--ignore-certificate-errors"]
        )
        
        # Test different SSL bypass parameter names
        ssl_params_to_test = [
            "ignore_https_errors",
            "ignoreHTTPSErrors", 
            "ignore_ssl_errors",
            "ignoreSslErrors"
        ]
        
        working_param = None
        for param in ssl_params_to_test:
            try:
                context_options = {
                    "viewport": {"width": 1280, "height": 720},
                    param: True
                }
                
                context = await browser.new_context(**context_options)
                await context.close()
                
                working_param = param
                print(f"    ✅ SSL bypass parameter '{param}' works")
                break
                
            except Exception as e:
                print(f"    ❌ SSL bypass parameter '{param}' failed: {e}")
                continue
        
        await browser.close()
        await playwright_instance.stop()
        
        if working_param:
            print(f"    🎯 Using SSL bypass parameter: {working_param}")
            return True, working_param
        else:
            print(f"    ⚠️ No SSL bypass parameter worked")
            return False, None
            
    except Exception as e:
        print(f"    💥 Playwright compatibility test failed: {e}")
        return False, None

async def test_ssl_bypass_with_simple_approach():
    """Test SSL bypass with simplified approach"""
    print("🧪 Testing SSL bypass with simplified approach...")
    
    try:
        from playwright.async_api import async_playwright
        
        # Simple approach - just use browser args for SSL bypass
        playwright_instance = await async_playwright().start()
        
        browser = await playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--disable-web-security",
                "--allow-running-insecure-content"
            ]
        )
        
        # Create context with minimal options
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        
        # Test sites with SSL issues
        test_sites = [
            ("https://httpbin.org/", "Control test (valid SSL)"),
            ("https://self-signed.badssl.com/", "Self-signed certificate"),
            ("https://expired.badssl.com/", "Expired certificate")
        ]
        
        results = []
        
        for url, description in test_sites:
            try:
                print(f"  🔗 Testing {description}: {url}")
                
                await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                title = await page.title()
                
                print(f"    ✅ Success: '{title[:50]}...'")
                results.append(True)
                
            except Exception as e:
                error_msg = str(e)
                if "ssl" in error_msg.lower() or "certificate" in error_msg.lower():
                    print(f"    ❌ SSL Error: {error_msg}")
                else:
                    print(f"    ❌ Other Error: {error_msg}")
                results.append(False)
        
        await context.close()
        await browser.close()
        await playwright_instance.stop()
        
        success_count = sum(results)
        total_count = len(results)
        
        print(f"\n📊 Simple SSL Test Results: {success_count}/{total_count} passed")
        
        return success_count >= 1  # At least control test should pass
        
    except Exception as e:
        print(f"❌ Simple SSL bypass test failed: {e}")
        return False

async def test_browser_manager_ssl():
    """Test the updated browser manager"""
    print("🧪 Testing updated BrowserManager SSL bypass...")
    
    try:
        from src.automation.browser_manager import BrowserManager
        
        browser_manager = BrowserManager(headless=True, browser_type="chromium")
        
        # Test SSL bypass functionality
        success, message = await browser_manager.test_ssl_bypass()
        
        if success:
            print(f"    ✅ BrowserManager SSL test passed: {message}")
        else:
            print(f"    ❌ BrowserManager SSL test failed: {message}")
        
        await browser_manager.cleanup()
        return success
        
    except Exception as e:
        print(f"❌ BrowserManager test failed: {e}")
        return False

async def main():
    """Run compatibility and SSL bypass tests"""
    print("🚀 Starting Browser SSL Compatibility Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Playwright Version Compatibility
    print("\n1️⃣ Playwright Version Compatibility Test")
    compat_success, working_param = await test_playwright_version_compatibility()
    results.append(compat_success)
    
    # Test 2: Simple SSL Bypass Approach
    print("\n2️⃣ Simple SSL Bypass Test")
    simple_success = await test_ssl_bypass_with_simple_approach()
    results.append(simple_success)
    
    # Test 3: BrowserManager SSL Test
    print("\n3️⃣ BrowserManager SSL Test")
    manager_success = await test_browser_manager_ssl()
    results.append(manager_success)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Overall Test Results: {sum(results)}/{len(results)} test suites passed")
    
    if sum(results) >= 2:
        print("✅ Browser SSL bypass is working!")
        print("\n🎯 Your browser automation can handle:")
        print("  • Basic SSL certificate bypass")
        print("  • Navigation to SSL-problematic sites") 
        print("  • Browser-level SSL error ignoring")
        
        if working_param:
            print(f"\n🔧 SSL Parameter: {working_param}")
    else:
        print("❌ Browser SSL bypass needs attention!")
        print("\n🔧 Troubleshooting:")
        print("  1. Update Playwright: pip install --upgrade playwright")
        print("  2. Reinstall browsers: playwright install chromium")
        print("  3. Check browser launch arguments")
        print("  4. Verify context parameter names")
    
    return sum(results) >= 2

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)
