# src/automation/saas_element_detector.py

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from playwright.async_api import Page, Locator

logger = logging.getLogger("e2e_testing_mcp")

class SaaSElementDetector:
    """Enhanced element detection specifically designed for SaaS applications"""
    
    def __init__(self, page: Page):
        self.page = page
        self.saas_patterns = self._initialize_saas_patterns()
        
    def _initialize_saas_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize SaaS-specific element patterns"""
        return {
            "login_fields": {
                "username": [
                    'input[type="email"]',
                    'input[name*="username"]', 'input[name*="email"]', 'input[name*="login"]',
                    'input[id*="username"]', 'input[id*="email"]', 'input[id*="login"]',
                    'input[placeholder*="email"]', 'input[placeholder*="username"]',
                    '#username', '#email', '#user', '#login', '#user-email',
                    '[data-testid*="username"]', '[data-testid*="email"]',
                    '.username-input', '.email-input', '.login-input'
                ],
                "password": [
                    'input[type="password"]',
                    'input[name*="password"]', 'input[name*="pass"]',
                    'input[id*="password"]', 'input[id*="pass"]',
                    'input[placeholder*="password"]',
                    '#password', '#pass', '#pwd',
                    '[data-testid*="password"]',
                    '.password-input', '.pass-input'
                ]
            },
            "buttons": {
                "login": [
                    'button[type="submit"]', 'input[type="submit"]',
                    'button:has-text("Login")', 'button:has-text("Sign in")', 'button:has-text("Log in")',
                    'button:has-text("Submit")', 'button:has-text("Enter")',
                    '[data-testid*="login"]', '[data-testid*="signin"]',
                    '.login-button', '.signin-button', '.submit-button',
                    '#login-btn', '#signin-btn', '#submit-btn'
                ],
                "save": [
                    'button:has-text("Save")', 'button:has-text("Submit")', 'button:has-text("Create")',
                    'button:has-text("Update")', 'button:has-text("Confirm")',
                    '[data-testid*="save"]', '[data-testid*="submit"]', '[data-testid*="create"]',
                    '.save-button', '.submit-button', '.create-button',
                    '#save-btn', '#submit-btn', '#create-btn'
                ],
                "add_create": [
                    'button:has-text("Add")', 'button:has-text("Create")', 'button:has-text("New")',
                    'button:has-text("+ ")', 'button:has-text("Plus")',
                    '[data-testid*="add"]', '[data-testid*="create"]', '[data-testid*="new"]',
                    '.add-button', '.create-button', '.new-button',
                    '#add-btn', '#create-btn', '#new-btn',
                    'a:has-text("Add")', 'a:has-text("Create")', 'a:has-text("New")'
                ]
            },
            "navigation": {
                "design": [
                    'a:has-text("Design")', 'nav a:has-text("Design")',
                    '[data-testid*="design"]', '.design-link',
                    '#design', '#design-nav', 'button:has-text("Design")'
                ],
                "network_hierarchy": [
                    'a:has-text("Network Hierarchy")', 'a[href*="networkHierarchy"]',
                    '[data-testid*="network-hierarchy"]', '.network-hierarchy-link'
                ]
            }
        }
    
    async def find_element(self, target: str, locator_strategy: str = "auto") -> Optional[Locator]:
        """Enhanced element finding with SaaS-specific strategies"""
        try:
            logger.debug(f"🔍 SaaS element detection: {target} using strategy: {locator_strategy}")
            
            if locator_strategy == "auto":
                return await self._auto_detect_saas_element(target)
            else:
                return await self._basic_element_detection(target, locator_strategy)
                
        except Exception as e:
            logger.error(f"❌ Error finding element {target}: {str(e)}")
            return None
    
    async def _auto_detect_saas_element(self, target: str) -> Optional[Locator]:
        """Auto-detect element using SaaS-specific patterns"""
        target_lower = target.lower().strip()
        
        # Strategy 1: SaaS Login Field Detection
        if any(term in target_lower for term in ["username", "email", "user", "login"]):
            return await self._find_by_pattern_list(self.saas_patterns["login_fields"]["username"])
        
        elif "password" in target_lower:
            return await self._find_by_pattern_list(self.saas_patterns["login_fields"]["password"])
        
        # Strategy 2: SaaS Button Detection
        elif any(term in target_lower for term in ["login", "sign in", "log in"]):
            return await self._find_by_pattern_list(self.saas_patterns["buttons"]["login"])
        
        elif any(term in target_lower for term in ["save", "submit", "create", "confirm"]):
            return await self._find_by_pattern_list(self.saas_patterns["buttons"]["save"])
        
        elif any(term in target_lower for term in ["add", "create", "new", "plus"]):
            return await self._find_by_pattern_list(self.saas_patterns["buttons"]["add_create"])
        
        # Strategy 3: SaaS Navigation Detection
        elif "design" in target_lower:
            return await self._find_by_pattern_list(self.saas_patterns["navigation"]["design"])
        
        elif "network hierarchy" in target_lower:
            return await self._find_by_pattern_list(self.saas_patterns["navigation"]["network_hierarchy"])
        
        # Strategy 4: Fallback to intelligent text-based search
        return await self._intelligent_text_search(target)
    
    async def _find_by_pattern_list(self, patterns: List[str]) -> Optional[Locator]:
        """Find element by trying a list of CSS selectors/patterns"""
        for pattern in patterns:
            try:
                locator = self.page.locator(pattern).first
                if await locator.count() > 0:
                    try:
                        await locator.wait_for(state="visible", timeout=2000)
                        logger.debug(f"✅ Found element with pattern: {pattern}")
                        return locator
                    except:
                        continue
            except Exception as e:
                logger.debug(f"🔍 Pattern {pattern} failed: {e}")
                continue
        
        return None
    
    async def _intelligent_text_search(self, target: str) -> Optional[Locator]:
        """Intelligent text-based element search with multiple strategies"""
        
        # Strategy 1: Exact text match
        locator = self.page.locator(f':has-text("{target}")').first
        if await locator.count() > 0:
            return locator
        
        # Strategy 2: Partial text match (case insensitive)
        words = target.lower().split()
        for word in words:
            if len(word) > 3:  # Only search for meaningful words
                locator = self.page.locator(f':has-text("{word}")').first
                if await locator.count() > 0:
                    return locator
        
        # Strategy 3: Aria-label search
        locator = self.page.locator(f'[aria-label*="{target}"]').first
        if await locator.count() > 0:
            return locator
        
        return None
    
    async def _basic_element_detection(self, target: str, locator_strategy: str) -> Optional[Locator]:
        """Basic element detection fallback"""
        if locator_strategy == "id":
            locator = self.page.locator(f'#{target}')
            return locator if await locator.count() > 0 else None
        elif locator_strategy == "class":
            locator = self.page.locator(f'.{target}')
            return locator if await locator.count() > 0 else None
        elif locator_strategy == "text":
            locator = self.page.locator(f':has-text("{target}")').first
            return locator if await locator.count() > 0 else None
        elif locator_strategy == "css":
            locator = self.page.locator(target)
            return locator if await locator.count() > 0 else None
        else:
            return await self._auto_detect_saas_element(target)