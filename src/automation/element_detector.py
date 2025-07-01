import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Page, Locator

logger = logging.getLogger("e2e_testing_mcp")

class ElementDetector:
    """Smart element detection with multiple strategies"""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def find_element(self, target: str, locator_strategy: str = "auto") -> Optional[Locator]:
        """Find element using multiple strategies"""
        try:
            logger.debug(f"Finding element: {target} using strategy: {locator_strategy}")
            
            if locator_strategy == "auto":
                return await self._auto_detect_element(target)
            elif locator_strategy == "id":
                return await self._find_by_id(target)
            elif locator_strategy == "class":
                return await self._find_by_class(target)
            elif locator_strategy == "text":
                return await self._find_by_text(target)
            elif locator_strategy == "xpath":
                return await self._find_by_xpath(target)
            elif locator_strategy == "css":
                return await self._find_by_css(target)
            else:
                logger.warning(f"Unknown locator strategy: {locator_strategy}, using auto")
                return await self._auto_detect_element(target)
                
        except Exception as e:
            logger.error(f"Error finding element {target}: {str(e)}")
            return None
    
    async def _auto_detect_element(self, target: str) -> Optional[Locator]:
        """Auto-detect element using multiple strategies"""
        target_lower = target.lower()
        
        # Strategy 1: Common form field patterns
        if "username" in target_lower or "email" in target_lower:
            patterns = [
                'input[type="email"]',
                'input[name*="username"]',
                'input[name*="email"]',
                'input[id*="username"]',
                'input[id*="email"]',
                '#username', '#email', '#user', '#login'
            ]
            for pattern in patterns:
                locator = self.page.locator(pattern).first
                if await locator.count() > 0:
                    return locator
        
        elif "password" in target_lower:
            patterns = [
                'input[type="password"]',
                'input[name*="password"]',
                'input[id*="password"]',
                '#password', '#pass'
            ]
            for pattern in patterns:
                locator = self.page.locator(pattern).first
                if await locator.count() > 0:
                    return locator
        
        elif "login" in target_lower and "button" in target_lower:
            patterns = [
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'input[type="submit"]',
                'button[type="submit"]',
                '[role="button"]:has-text("Login")'
            ]
            for pattern in patterns:
                locator = self.page.locator(pattern).first
                if await locator.count() > 0:
                    return locator
        
        # Strategy 2: Generic button detection
        elif "button" in target_lower:
            # Extract button text if possible
            button_texts = ["add", "create", "submit", "send", "save", "continue", "next"]
            for text in button_texts:
                if text in target_lower:
                    locator = self.page.locator(f'button:has-text("{text.title()}")').first
                    if await locator.count() > 0:
                        return locator
        
        # Strategy 3: Text-based search
        text_patterns = [
            f':has-text("{target}")',
            f'[aria-label*="{target}"]',
            f'[placeholder*="{target}"]',
            f'[title*="{target}"]'
        ]
        for pattern in text_patterns:
            locator = self.page.locator(pattern).first
            if await locator.count() > 0:
                return locator
        
        # Strategy 4: Fallback to partial text match
        locator = self.page.locator(f':has-text("{target}")').first
        if await locator.count() > 0:
            return locator
        
        logger.warning(f"Could not find element: {target}")
        return None
    
    async def _find_by_id(self, target: str) -> Optional[Locator]:
        """Find element by ID"""
        locator = self.page.locator(f'#{target}')
        return locator if await locator.count() > 0 else None
    
    async def _find_by_class(self, target: str) -> Optional[Locator]:
        """Find element by class"""
        locator = self.page.locator(f'.{target}')
        return locator if await locator.count() > 0 else None
    
    async def _find_by_text(self, target: str) -> Optional[Locator]:
        """Find element by text content"""
        locator = self.page.locator(f':has-text("{target}")').first
        return locator if await locator.count() > 0 else None
    
    async def _find_by_xpath(self, target: str) -> Optional[Locator]:
        """Find element by XPath"""
        locator = self.page.locator(f'xpath={target}')
        return locator if await locator.count() > 0 else None
    
    async def _find_by_css(self, target: str) -> Optional[Locator]:
        """Find element by CSS selector"""
        locator = self.page.locator(target)
        return locator if await locator.count() > 0 else None