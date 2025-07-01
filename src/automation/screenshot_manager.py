import asyncio
import logging
from pathlib import Path
from typing import Optional
from playwright.async_api import Page
import time

logger = logging.getLogger("e2e_testing_mcp")

class ScreenshotManager:
    """Manages screenshot capture and storage"""
    
    def __init__(self, screenshots_dir: Path):
        self.screenshots_dir = screenshots_dir
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def capture_step_screenshot(self, page: Page, session_id: str, step_number: int, action: str) -> Optional[str]:
        """Capture screenshot for a test step"""
        try:
            timestamp = int(time.time())
            filename = f"{session_id}_step_{step_number:02d}_{action}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            await page.screenshot(path=str(filepath), full_page=True)
            
            logger.debug(f"Screenshot captured: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            return None
    
    async def capture_error_screenshot(self, page: Page, session_id: str, error_context: str) -> Optional[str]:
        """Capture screenshot when an error occurs"""
        try:
            timestamp = int(time.time())
            filename = f"{session_id}_error_{error_context}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            await page.screenshot(path=str(filepath), full_page=True)
            
            logger.info(f"Error screenshot captured: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to capture error screenshot: {str(e)}")
            return None