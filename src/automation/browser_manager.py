import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import time

logger = logging.getLogger("e2e_testing_mcp")

class BrowserManager:
    """Manages browser lifecycle and sessions"""
    
    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        self.headless = headless
        self.browser_type = browser_type
        self.playwright = None
        self.browser = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        
    async def initialize(self):
        """Initialize Playwright and browser"""
        try:
            logger.info("Initializing Playwright browser manager")
            self.playwright = await async_playwright().start()
            
            # Launch browser based on type
            if self.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
            elif self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif self.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
            logger.info(f"Browser launched successfully: {self.browser_type} (headless: {self.headless})")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def create_session(self, session_id: str) -> Page:
        """Create a new browser session"""
        try:
            if not self.browser:
                await self.initialize()
            
            # Create new context for isolation
            context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ignoreHTTPSErrors=True
            )
            
            # Create new page
            page = await context.new_page()
            
            # Store context and page
            self.contexts[session_id] = context
            self.pages[session_id] = page
            
            logger.info(f"Created browser session: {session_id}")
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
