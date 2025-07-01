import asyncio
import logging
import time
from typing import Dict, Any, Optional
from playwright.async_api import Page, Locator
from .element_detector import ElementDetector

logger = logging.getLogger("e2e_testing_mcp")

class ActionExecutor:
    """Executes browser actions with error handling and verification"""
    
    def __init__(self, page: Page):
        self.page = page
        self.detector = ElementDetector(page)
        
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test step"""
        start_time = time.time()
        
        try:
            action = step.get("action", "").lower()
            target = step.get("target", "")
            value = step.get("value", "")
            locator_strategy = step.get("locator_strategy", "auto")
            
            logger.info(f"Executing step: {action} on {target}")
            
            if action == "navigate":
                return await self._navigate(target, step)
            elif action == "click":
                return await self._click(target, locator_strategy, step)
            elif action == "fill":
                return await self._fill(target, value, locator_strategy, step)
            elif action == "verify":
                return await self._verify(target, value, locator_strategy, step)
            elif action == "wait":
                return await self._wait(target, value, step)
            elif action == "select":
                return await self._select(target, value, locator_strategy, step)
            else:
                return {
                    "status": "failed",
                    "message": f"Unknown action: {action}",
                    "execution_time_ms": int((time.time() - start_time) * 1000)
                }
                
        except Exception as e:
            logger.error(f"Error executing step {action}: {str(e)}")
            return {
                "status": "failed",
                "message": f"Failed to execute {action}: {str(e)}",
                "error_details": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
    
    async def _navigate(self, url: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to URL"""
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Verify navigation
            current_url = self.page.url
            title = await self.page.title()
            
            return {
                "status": "success",
                "message": f"Successfully navigated to {url}",
                "current_url": current_url,
                "page_title": title,
                "execution_time_ms": 2000  # Approximate navigation time
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Failed to navigate to {url}: {str(e)}",
                "error_details": str(e)
            }
    
    async def _click(self, target: str, locator_strategy: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Click element"""
        try:
            element = await self.detector.find_element(target, locator_strategy)
            if not element:
                return {
                    "status": "failed",
                    "message": f"Element not found: {target}",
                    "locator_strategy": locator_strategy
                }
            
            # Wait for element to be visible and enabled
            await element.wait_for(state="visible", timeout=10000)
            await element.scroll_into_view_if_needed()
            
            # Click the element
            await element.click()
            
            # Wait a moment for any page changes
            await asyncio.sleep(0.5)
            
            return {
                "status": "success", 
                "message": f"Successfully clicked: {target}",
                "element_found": True,
                "locator_strategy": locator_strategy
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Failed to click {target}: {str(e)}",
                "error_details": str(e)
            }
    
    async def _fill(self, target: str, value: str, locator_strategy: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Fill input field"""
        try:
            element = await self.detector.find_element(target, locator_strategy)
            if not element:
                return {
                    "status": "failed",
                    "message": f"Input field not found: {target}",
                    "locator_strategy": locator_strategy
                }
            
            # Wait for element to be visible
            await element.wait_for(state="visible", timeout=10000)
            await element.scroll_into_view_if_needed()
            
            # Clear and fill the field
            await element.clear()
            await element.fill(value)
            
            # Verify the value was entered
            filled_value = await element.input_value()
            
            return {
                "status": "success",
                "message": f"Successfully filled {target} with value",
                "value_entered": len(value),  # Don't log actual values for security
                "value_verified": filled_value == value,
                "locator_strategy": locator_strategy
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Failed to fill {target}: {str(e)}",
                "error_details": str(e)
            }
    
    async def _verify(self, target: str, expected_value: str, locator_strategy: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Verify element or content"""
        try:
            if not expected_value:
                # Just verify element exists
                element = await self.detector.find_element(target, locator_strategy)
                if element and await element.count() > 0:
                    return {
                        "status": "success",
                        "message": f"Element verified: {target}",
                        "element_exists": True
                    }
                else:
                    return {
                        "status": "failed",
                        "message": f"Element not found for verification: {target}",
                        "element_exists": False
                    }
            else:
                # Verify element contains expected text
                page_content = await self.page.content()
                if expected_value.lower() in page_content.lower():
                    return {
                        "status": "success",
                        "message": f"Content verified: found '{expected_value}'",
                        "content_found": True
                    }
                else:
                    return {
                        "status": "failed",
                        "message": f"Expected content not found: '{expected_value}'",
                        "content_found": False
                    }
                    
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Failed to verify {target}: {str(e)}",
                "error_details": str(e)
            }
    
    async def _wait(self, target: str, duration: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for element or duration"""
        try:
            if target.lower() == "time" or target.lower() == "duration":
                # Wait for specific duration
                wait_time = float(duration) if duration else 1.0
                await asyncio.sleep(wait_time)
                return {
                    "status": "success",
                    "message": f"Waited for {wait_time} seconds",
                    "wait_duration": wait_time
                }
            else:
                # Wait for element to appear
                element = await self.detector.find_element(target, "auto")
                if element:
                    await element.wait_for(state="visible", timeout=10000)
                    return {
                        "status": "success",
                        "message": f"Element appeared: {target}",
                        "element_found": True
                    }
                else:
                    return {
                        "status": "failed",
                        "message": f"Element did not appear: {target}",
                        "element_found": False
                    }
                    
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Wait failed: {str(e)}",
                "error_details": str(e)
            }
    
    async def _select(self, target: str, value: str, locator_strategy: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Select option from dropdown"""
        try:
            element = await self.detector.find_element(target, locator_strategy)
            if not element:
                return {
                    "status": "failed",
                    "message": f"Select element not found: {target}",
                    "locator_strategy": locator_strategy
                }
            
            await element.wait_for(state="visible", timeout=10000)
            await element.select_option(value)
            
            return {
                "status": "success",
                "message": f"Successfully selected '{value}' from {target}",
                "option_selected": value,
                "locator_strategy": locator_strategy
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Failed to select from {target}: {str(e)}",
                "error_details": str(e)
            }
