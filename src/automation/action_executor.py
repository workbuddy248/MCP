import asyncio
import logging
import time
from typing import Dict, Any, Optional
from playwright.async_api import Page, Locator, Error as PlaywrightError
from .element_detector import ElementDetector

logger = logging.getLogger("e2e_testing_mcp")

class ActionExecutor:
    """Executes browser actions with error handling, verification and SSL bypass"""
    
    def __init__(self, page: Page):
        self.page = page
        self.detector = ElementDetector(page)
        
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test step with SSL error handling"""
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
       """Navigate to URL with SSL error handling and retries - Fixed port handling"""
       try:
          # Ensure URL is properly formatted and preserve port
          original_url = url
          if url and not url.startswith(('http://', 'https://')):
             url = f'https://{url}'
        
          # Ensure URL ends with / if it has a port
          if ':443' in url and not url.endswith('/'):
             url = url + '/'
          elif ':80' in url and not url.endswith('/'):
             url = url + '/'
        
          logger.info(f"Navigating to: {url} (original: {original_url})")
        
          # Reduced navigation options to prevent timeouts
          navigation_options = {
            "wait_until": "domcontentloaded",  # Changed from networkidle
            "timeout": 60000  # 1 minute timeout
          }
        
          max_retries = 2  # Reduced from 3
          last_error = None
        
          for attempt in range(max_retries):
            try:
                logger.info(f"Navigation attempt {attempt + 1}/{max_retries} to: {url}")
                await self.page.goto(url, **navigation_options)
                
                # Verify we actually navigated to the URL with port
                current_url = self.page.url
                logger.info(f"Navigation completed to: {current_url}")
                break  # Success, exit retry loop
                
            except PlaywrightError as e:
                error_message = str(e).lower()
                last_error = e
                
                # Handle SSL-specific errors
                if any(ssl_term in error_message for ssl_term in [
                    'ssl', 'certificate', 'tls', 'handshake', 'cert', 'x509'
                ]):
                    logger.warning(f"SSL error on attempt {attempt + 1}/{max_retries}: {e}")
                    
                    if attempt < max_retries - 1:
                        # Try different wait strategy
                        navigation_options["wait_until"] = "load"
                        await asyncio.sleep(3)
                        continue
                
                # Handle network errors  
                elif any(net_term in error_message for net_term in [
                    'net::', 'network', 'timeout', 'connection', 'refused'
                ]):
                    logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                
                # Non-recoverable error
                logger.error(f"Non-recoverable navigation error: {e}")
                raise
        
          else:
            # All retries exhausted
            raise last_error
        
          # Simplified page stabilization
          try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=15000)
          except:
            await asyncio.sleep(3)  # Fallback wait
        
          # Get final page state
          current_url = self.page.url
          title = await self.page.title()
        
          logger.info(f"Final navigation state - URL: {current_url}, Title: {title}")
        
          # Simplified SSL error handling
          page_content = await self.page.content()
          ssl_error_indicators = [
            "your connection is not private", "privacy error", 
            "certificate error", "ssl error", "not secure"
          ]
        
          is_ssl_error_page = any(indicator in page_content.lower() for indicator in ssl_error_indicators)
        
          if is_ssl_error_page:
            logger.warning(f"Detected SSL error page for {url}, attempting to proceed")
            
            # Try to proceed through SSL warning
            ssl_proceed_selectors = [
                "#proceed-link", "#advanced-button", 
                "button:has-text('Advanced')", "a:has-text('Proceed')"
            ]
            
            for selector in ssl_proceed_selectors:
                try:
                    proceed_element = self.page.locator(selector)
                    if await proceed_element.count() > 0:
                        logger.info(f"Clicking SSL proceed: {selector}")
                        await proceed_element.click()
                        await asyncio.sleep(5)
                        break
                except Exception:
                    continue
        
          # Final verification
          final_url = self.page.url
          final_title = await self.page.title()
        
          return {
            "status": "success",
            "message": f"Successfully navigated to {url}",
            "initial_url": url,
            "current_url": final_url,
            "page_title": final_title,
            "ssl_warning_handled": is_ssl_error_page,
            "port_preserved": ":443" in final_url or ":80" in final_url
          }
        
       except Exception as e:
        error_message = str(e)
        logger.error(f"Navigation failed for {url}: {error_message}")
        
        return {
            "status": "failed",
            "message": f"Failed to navigate to {url}: {error_message}",
            "error_details": error_message,
            "initial_url": url
        }
    
    async def _click(self, target: str, locator_strategy: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Click element with enhanced error handling"""
        try:
            element = await self.detector.find_element(target, locator_strategy)
            if not element:
                return {
                    "status": "failed",
                    "message": f"Element not found: {target}",
                    "locator_strategy": locator_strategy
                }
            
            # Wait for element to be visible and enabled with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await element.wait_for(state="visible", timeout=10000)
                    await element.scroll_into_view_if_needed()
                    
                    # Check if element is clickable
                    if await element.is_enabled():
                        break
                    else:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        else:
                            return {
                                "status": "failed",
                                "message": f"Element not clickable: {target}",
                                "locator_strategy": locator_strategy
                            }
                            
                except Exception as wait_error:
                    if attempt == max_retries - 1:
                        raise wait_error
                    await asyncio.sleep(1)
            
            # Perform click with retries for network-related issues
            for attempt in range(2):
                try:
                    await element.click()
                    break
                except Exception as click_error:
                    if "network" in str(click_error).lower() and attempt == 0:
                        logger.warning(f"Network error during click, retrying: {click_error}")
                        await asyncio.sleep(1)
                        continue
                    raise click_error
            
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
        """Fill input field with enhanced error handling"""
        try:
            element = await self.detector.find_element(target, locator_strategy)
            if not element:
                return {
                    "status": "failed",
                    "message": f"Input field not found: {target}",
                    "locator_strategy": locator_strategy
                }
            
            # Wait for element to be visible with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await element.wait_for(state="visible", timeout=10000)
                    await element.scroll_into_view_if_needed()
                    break
                except Exception as wait_error:
                    if attempt == max_retries - 1:
                        raise wait_error
                    await asyncio.sleep(1)
            
            # Clear and fill the field with retries
            for attempt in range(2):
                try:
                    await element.clear()
                    await element.fill(value)
                    break
                except Exception as fill_error:
                    if "network" in str(fill_error).lower() and attempt == 0:
                        logger.warning(f"Network error during fill, retrying: {fill_error}")
                        await asyncio.sleep(1)
                        continue
                    raise fill_error
            
            # Verify the value was entered
            try:
                filled_value = await element.input_value()
                value_verified = filled_value == value
            except:
                value_verified = False
            
            return {
                "status": "success",
                "message": f"Successfully filled {target} with value",
                "value_entered": len(value),  # Don't log actual values for security
                "value_verified": value_verified,
                "locator_strategy": locator_strategy
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Failed to fill {target}: {str(e)}",
                "error_details": str(e)
            }
    
    async def _verify(self, target: str, expected_value: str, locator_strategy: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Verify element or content with enhanced error handling"""
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
                # Verify element contains expected text with retries
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        page_content = await self.page.content()
                        if expected_value.lower() in page_content.lower():
                            return {
                                "status": "success",
                                "message": f"Content verified: found '{expected_value}'",
                                "content_found": True
                            }
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)  # Wait for content to load
                            continue
                            
                    except Exception as content_error:
                        if attempt == max_retries - 1:
                            raise content_error
                        await asyncio.sleep(1)
                
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
        """Wait for element or duration with enhanced error handling"""
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
                # Wait for element to appear with retries
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        element = await self.detector.find_element(target, "auto")
                        if element:
                            await element.wait_for(state="visible", timeout=10000)
                            return {
                                "status": "success",
                                "message": f"Element appeared: {target}",
                                "element_found": True
                            }
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)
                            continue
                            
                    except Exception as wait_error:
                        if attempt == max_retries - 1:
                            raise wait_error
                        await asyncio.sleep(2)
                
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
        """Select option from dropdown with enhanced error handling"""
        try:
            element = await self.detector.find_element(target, locator_strategy)
            if not element:
                return {
                    "status": "failed",
                    "message": f"Select element not found: {target}",
                    "locator_strategy": locator_strategy
                }
            
            # Wait for element and perform selection with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await element.wait_for(state="visible", timeout=10000)
                    await element.select_option(value)
                    break
                except Exception as select_error:
                    if attempt == max_retries - 1:
                        raise select_error
                    await asyncio.sleep(1)
            
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