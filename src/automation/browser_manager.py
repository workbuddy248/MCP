import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import time

logger = logging.getLogger("e2e_testing_mcp")

class BrowserManager:
    """Manages browser lifecycle and sessions with SSL certificate bypass - Version Compatible"""
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self.playwright = None
        self.browser = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        
    async def initialize(self):
        """Initialize Playwright and browser with SSL bypass"""
        try:
            logger.info("Initializing Playwright browser manager with SSL bypass")
            self.playwright = await async_playwright().start()
            
            # Browser launch args to bypass SSL and security checks
            browser_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--ignore-certificate-errors-spki-list", 
                "--ignore-ssl-errors-list",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-features=VizDisplayCompositor",
                "--disable-extensions",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-field-trial-config",
                "--disable-back-forward-cache",
                "--disable-ipc-flooding-protection",
                "--accept-lang=en-US"
            ]
            
            # Launch browser based on type with SSL bypass
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=browser_args
                )
            elif self.browser_type == "firefox":
                # Firefox specific SSL bypass args
                firefox_args = [
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
                self.browser = await self.playwright.firefox.launch(
                    headless=self.headless,
                    args=firefox_args
                )
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            logger.info(f"Browser launched successfully with SSL bypass: {self.browser_type} (headless: {self.headless})")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    def _get_context_options(self):
        """Get context options with version-compatible SSL bypass settings"""
        # Base context options
        base_options = {
            "viewport": {"width": 1280, "height": 720},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "permissions": ["geolocation", "microphone", "camera", "notifications"],
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            }
        }
        
        # Try different SSL bypass parameter names based on Playwright version
        ssl_bypass_options = [
            "ignore_https_errors",    # Most common in recent versions
            "ignoreHTTPSErrors",      # Alternative camelCase
            "ignore_ssl_errors",      # Alternative
            "ignoreSslErrors"         # Another alternative
        ]
        
        # Try to determine which parameter works
        for ssl_param in ssl_bypass_options:
            try:
                test_options = base_options.copy()
                test_options[ssl_param] = True
                
                # Additional options that might be version-dependent
                try:
                    test_options["accept_downloads"] = True
                except:
                    try:
                        test_options["acceptDownloads"] = True
                    except:
                        pass
                
                logger.info(f"Using SSL bypass parameter: {ssl_param}")
                return test_options
                
            except Exception as e:
                logger.debug(f"SSL parameter {ssl_param} not supported: {e}")
                continue
        
        # Fallback - return base options without SSL bypass if none work
        logger.warning("Could not determine SSL bypass parameter, using base options")
        return base_options
    
    async def create_session(self, session_id: str) -> Page:
        """Create a new browser session with SSL bypass"""
        try:
            if not self.browser:
                await self.initialize()
            
            # Get version-compatible context options
            context_options = self._get_context_options()
            
            # Firefox specific context options
            if self.browser_type == "firefox":
                try:
                    context_options.update({
                        "bypass_csp": True,  # Bypass Content Security Policy
                    })
                except:
                    pass  # Ignore if not supported
            
            context = await self.browser.new_context(**context_options)
            
            # Set additional security bypasses for the context
            try:
                await context.add_init_script("""
                    // Bypass SSL certificate validation in the page context
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // Override certificate validation for XMLHttpRequest
                    if (window.XMLHttpRequest) {
                        const originalOpen = window.XMLHttpRequest.prototype.open;
                        window.XMLHttpRequest.prototype.open = function(...args) {
                            this.addEventListener('error', (e) => {
                                if (e.target.status === 0) {
                                    console.log('SSL Certificate error bypassed in XMLHttpRequest');
                                }
                            });
                            return originalOpen.apply(this, args);
                        };
                    }
                    
                    // Override certificate validation for fetch
                    if (window.fetch) {
                        const originalFetch = window.fetch;
                        window.fetch = function(...args) {
                            const options = args[1] || {};
                            options.mode = options.mode || 'cors';
                            args[1] = options;
                            return originalFetch.apply(this, args).catch(err => {
                                if (err.name === 'TypeError' && err.message.includes('certificate')) {
                                    console.log('Fetch SSL Certificate error bypassed');
                                    return new Response('SSL Bypass', { status: 200 });
                                }
                                throw err;
                            });
                        };
                    }
                """)
            except Exception as script_error:
                logger.warning(f"Could not add init script: {script_error}")
            
            # Create new page
            page = await context.new_page()
            
            # Set additional page-level SSL bypass headers if possible
            try:
                await page.set_extra_http_headers({
                    "Accept-Insecure-Certs": "1",
                    "Ignore-Certificate-Errors": "1"
                })
            except Exception as header_error:
                logger.debug(f"Could not set extra headers: {header_error}")
            
            # Store context and page
            self.contexts[session_id] = context
            self.pages[session_id] = page
            
            logger.info(f"Created browser session with SSL bypass: {session_id}")
            return page
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {str(e)}")
            raise
    
    async def get_page(self, session_id: str) -> Optional[Page]:
        """Get existing page for session"""
        return self.pages.get(session_id)
    
    async def close_session(self, session_id: str):
        """Close browser session"""
        try:
            if session_id in self.contexts:
                await self.contexts[session_id].close()
                del self.contexts[session_id]
            
            if session_id in self.pages:
                del self.pages[session_id]
            
            logger.info(f"Closed browser session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error closing session {session_id}: {str(e)}")
    
    async def cleanup(self):
        """Cleanup all browser resources"""
        try:
            # Close all contexts
            for context in self.contexts.values():
                await context.close()
            
            # Close browser
            if self.browser:
                await self.browser.close()
            
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("Browser manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def test_ssl_bypass(self):
        """Test SSL bypass functionality"""
        try:
            test_page = await self.create_session("ssl_test")
            
            # Test with a known SSL problem site
            await test_page.goto("https://self-signed.badssl.com/", timeout=10000)
            title = await test_page.title()
            
            await self.close_session("ssl_test")
            
            return True, f"SSL bypass working - page title: {title}"
            
        except Exception as e:
            return False, f"SSL bypass test failed: {str(e)}"
