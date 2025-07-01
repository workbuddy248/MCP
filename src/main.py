# =====================================
# Updated src/main.py with Real Browser Automation
# =====================================

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import Settings
from src.core.logging_config import setup_logging
from src.core.models import TestInstruction, TestPlan, ExecutionResult
from src.core.exceptions import E2ETestingError, ValidationError
from src.automation import BrowserManager, ActionExecutor, ScreenshotManager

# Initialize settings and logging
settings = Settings()
logger = setup_logging(settings)

# Global state storage
_active_sessions: Dict[str, Dict[str, Any]] = {}

# Global browser manager
_browser_manager = None
_screenshot_manager = None

# Initialize Azure OpenAI client
_azure_openai_client = None

def _get_browser_manager():
    """Get or create browser manager"""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager(
            headless=settings.HEADLESS,
            browser_type=settings.BROWSER_TYPE
        )
    return _browser_manager

def _get_screenshot_manager():
    """Get or create screenshot manager"""
    global _screenshot_manager
    if _screenshot_manager is None:
        screenshots_dir = settings.DATA_DIR / "screenshots" if settings.DATA_DIR else Path("./screenshots")
        _screenshot_manager = ScreenshotManager(screenshots_dir)
    return _screenshot_manager

def _get_azure_openai_client():
    """Get or create Azure OpenAI client"""
    global _azure_openai_client
    if _azure_openai_client is None:
        try:
            from src.ai.azure_openai_client import AzureOpenAIClient
            config = settings.get_azure_openai_config()
            _azure_openai_client = AzureOpenAIClient(config)
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure OpenAI client: {e}")
            _azure_openai_client = None
    return _azure_openai_client

# =====================================
# FastMCP Implementation with Real Browser Automation
# =====================================

try:
    from mcp.server.fastmcp import FastMCP
    
    # Create FastMCP server instance
    app = FastMCP(
        name=settings.MCP_SERVER_NAME,
        version=settings.MCP_SERVER_VERSION
    )
    
    @app.tool()
    async def parse_test_instructions(
        prompt: str,
        url: str = "",
        username: str = "",
        password: str = ""
    ) -> Dict[str, Any]:
        """
        Parse natural language test instructions into structured test plan using Azure OpenAI
        
        Args:
            prompt: Natural language description of the test scenario
            url: Target application URL (optional if included in prompt)
            username: Login username (optional if included in prompt)
            password: Login password (optional if included in prompt)
        
        Returns:
            Structured test plan with steps and metadata
        """
        try:
            logger.info(f"Parsing test instructions with Azure OpenAI: {prompt[:100]}...")
            
            # Try Azure OpenAI first
            azure_client = _get_azure_openai_client()
            if azure_client:
                try:
                    # Use Azure OpenAI for intelligent parsing
                    ai_result = await azure_client.parse_test_instructions(prompt, url, username, password)
                    
                    # Convert AI result to our TestPlan format
                    test_plan = TestPlan(
                        name=ai_result.get("test_name", f"Test Plan for {url or 'web application'}"),
                        description=ai_result.get("description", prompt),
                        steps=ai_result.get("steps", [])
                    )
                    
                    logger.info("Successfully parsed instructions using Azure OpenAI")
                    
                except Exception as ai_error:
                    logger.warning(f"Azure OpenAI parsing failed, using fallback: {ai_error}")
                    # Fallback to basic parsing
                    instruction = TestInstruction(
                        prompt=prompt,
                        url=url or "https://example.com",
                        username=username or "demo_user",
                        password=password or "demo_pass"
                    )
                    test_plan = await _parse_instructions_to_plan(instruction)
            else:
                # Fallback to basic parsing
                logger.info("Using fallback parsing (Azure OpenAI not available)")
                instruction = TestInstruction(
                    prompt=prompt,
                    url=url or "https://example.com",
                    username=username or "demo_user",
                    password=password or "demo_pass"
                )
                test_plan = await _parse_instructions_to_plan(instruction)
            
            # Store in session - Store as dict consistently
            session_id = f"session_{len(_active_sessions) + 1}"
            _active_sessions[session_id] = {
                "instruction": {
                    "prompt": prompt,
                    "url": url,
                    "username": username,
                    "password": password
                },
                "test_plan": test_plan.dict(),
                "status": "planned",
                "created_at": asyncio.get_event_loop().time(),
                "ai_powered": azure_client is not None,
                "browser_session": None  # Will be created during execution
            }
            
            logger.info(f"Successfully parsed instructions into {len(test_plan.steps)} steps")
            
            return {
                "session_id": session_id,
                "status": "success",
                "test_plan": test_plan.dict(),
                "ai_powered": azure_client is not None,
                "browser_automation": True,
                "message": f"Successfully parsed {len(test_plan.steps)} test steps using {'Azure OpenAI' if azure_client else 'fallback parser'}"
            }
            
        except Exception as e:
            logger.error(f"Error parsing instructions: {str(e)}")
            raise E2ETestingError(f"Failed to parse instructions: {str(e)}")

    @app.tool()
    async def execute_test_plan(session_id: str) -> Dict[str, Any]:
        """
        Execute a test plan with REAL browser automation
        
        Args:
            session_id: Session ID from parse_test_instructions
        
        Returns:
            Execution results with status and details
        """
        try:
            if session_id not in _active_sessions:
                raise ValidationError(f"Session {session_id} not found")
            
            session = _active_sessions[session_id]
            test_plan_data = session["test_plan"]
            if isinstance(test_plan_data, dict):
                test_plan = TestPlan(**test_plan_data)
            else:
                test_plan = test_plan_data
            
            logger.info(f"🚀 Starting REAL browser execution for session {session_id}")
            
            # Execute with real browser automation
            execution_result = await _execute_real_browser_workflow(test_plan, session_id)
            
            # Update session status
            session["status"] = "completed" if execution_result.success else "failed"
            session["execution_result"] = execution_result.dict()
            session["completed_at"] = asyncio.get_event_loop().time()
            
            logger.info(f"✅ Real browser execution completed for session {session_id}: {execution_result.success}")
            
            return {
                "session_id": session_id,
                "status": "success",
                "execution_result": execution_result.dict(),
                "browser_automation": True,
                "screenshots_captured": len([step for step in execution_result.execution_details if step.get("screenshot_path")]),
                "message": f"🎉 REAL browser execution {'completed successfully' if execution_result.success else 'failed'} - {execution_result.steps_executed}/{execution_result.total_steps} steps executed"
            }
            
        except Exception as e:
            logger.error(f"Error executing test plan: {str(e)}")
            raise E2ETestingError(f"Failed to execute test plan: {str(e)}")

    @app.tool()
    async def get_session_status(session_id: str) -> Dict[str, Any]:
        """
        Get status of a test session
        
        Args:
            session_id: Session ID to check
        
        Returns:
            Session status and details
        """
        try:
            if session_id not in _active_sessions:
                raise ValidationError(f"Session {session_id} not found")
            
            session = _active_sessions[session_id]
            
            # Handle both dict and object formats safely
            test_plan = session.get("test_plan", {})
            if isinstance(test_plan, dict):
                steps_count = len(test_plan.get("steps", []))
            else:
                steps_count = len(test_plan.steps) if hasattr(test_plan, 'steps') else 0
            
            execution_result = session.get("execution_result", {})
            screenshots_count = 0
            if isinstance(execution_result, dict):
                execution_details = execution_result.get("execution_details", [])
                screenshots_count = len([step for step in execution_details if step.get("screenshot_path")])
            
            return {
                "session_id": session_id,
                "status": session["status"],
                "created_at": session["created_at"],
                "completed_at": session.get("completed_at"),
                "test_plan_steps": steps_count,
                "ai_powered": session.get("ai_powered", False),
                "browser_automation": True,
                "screenshots_captured": screenshots_count,
                "message": f"Session {session_id} is {session['status']}"
            }
            
        except Exception as e:
            logger.error(f"Error getting session status: {str(e)}")
            raise E2ETestingError(f"Failed to get session status: {str(e)}")

    @app.tool()
    async def list_active_sessions() -> Dict[str, Any]:
        """
        List all active test sessions
        
        Returns:
            List of active sessions with basic info
        """
        try:
            sessions = []
            for session_id, session_data in _active_sessions.items():
                # Handle both TestPlan objects and dict objects safely
                test_plan = session_data.get("test_plan")
                if test_plan:
                    if hasattr(test_plan, 'steps'):
                        steps_count = len(test_plan.steps)
                    elif isinstance(test_plan, dict) and 'steps' in test_plan:
                        steps_count = len(test_plan['steps'])
                    else:
                        steps_count = 0
                else:
                    steps_count = 0
                
                # Count screenshots if execution completed
                screenshots_count = 0
                execution_result = session_data.get("execution_result", {})
                if isinstance(execution_result, dict):
                    execution_details = execution_result.get("execution_details", [])
                    screenshots_count = len([step for step in execution_details if step.get("screenshot_path")])
                
                sessions.append({
                    "session_id": session_id,
                    "status": session_data.get("status", "unknown"),
                    "created_at": session_data.get("created_at", 0),
                    "steps_count": steps_count,
                    "ai_powered": session_data.get("ai_powered", False),
                    "browser_automation": True,
                    "screenshots_captured": screenshots_count
                })
            
            azure_client = _get_azure_openai_client()
            browser_manager = _get_browser_manager()
            
            return {
                "status": "success",
                "sessions": sessions,
                "total_sessions": len(sessions),
                "azure_openai_available": azure_client is not None,
                "browser_automation_enabled": True,
                "browser_type": settings.BROWSER_TYPE,
                "headless_mode": settings.HEADLESS,
                "message": f"Found {len(sessions)} active sessions with real browser automation"
            }
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            raise E2ETestingError(f"Failed to list sessions: {str(e)}")

    @app.tool()
    async def test_azure_openai_connection() -> Dict[str, Any]:
        """
        Test Azure OpenAI connection and configuration
        
        Returns:
            Connection status and configuration details
        """
        try:
            azure_client = _get_azure_openai_client()
            if not azure_client:
                return {
                    "status": "error",
                    "connected": False,
                    "message": "Azure OpenAI client not configured. Check environment variables."
                }
            
            # Test connection by making a simple request
            test_result = await azure_client.parse_test_instructions(
                "Simple test: navigate to example.com", 
                "https://example.com"
            )
            
            return {
                "status": "success",
                "connected": True,
                "model": azure_client.config.model,
                "api_version": azure_client.config.api_version,
                "browser_automation": True,
                "message": "Azure OpenAI connection successful",
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"Azure OpenAI connection test failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "message": "Azure OpenAI connection failed. Check configuration and credentials."
            }

    @app.tool()
    async def test_browser_automation() -> Dict[str, Any]:
        """
        Test browser automation setup
        
        Returns:
            Browser automation status and capabilities
        """
        try:
            browser_manager = _get_browser_manager()
            
            # Test browser initialization
            await browser_manager.initialize()
            
            # Create test session
            test_session_id = "browser_test_session"
            page = await browser_manager.create_session(test_session_id)
            
            # Test navigation
            await page.goto("https://example.com", wait_until="networkidle")
            title = await page.title()
            url = page.url
            
            # Test screenshot
            screenshot_manager = _get_screenshot_manager()
            screenshot_path = await screenshot_manager.capture_step_screenshot(
                page, test_session_id, 1, "test_navigation"
            )
            
            # Clean up test session
            await browser_manager.close_session(test_session_id)
            
            return {
                "status": "success",
                "browser_working": True,
                "browser_type": settings.BROWSER_TYPE,
                "headless_mode": settings.HEADLESS,
                "test_url": url,
                "test_title": title,
                "screenshot_captured": screenshot_path is not None,
                "screenshot_path": screenshot_path,
                "message": "✅ Browser automation test successful"
            }
            
        except Exception as e:
            logger.error(f"Browser automation test failed: {str(e)}")
            return {
                "status": "error",
                "browser_working": False,
                "error": str(e),
                "message": "❌ Browser automation test failed"
            }

    # Use FastMCP's built-in run method
    USE_FASTMCP = True

except ImportError as e:
    logger.warning(f"FastMCP not available, falling back to basic MCP: {e}")
    USE_FASTMCP = False

# =====================================
# Real Browser Automation Functions
# =====================================

async def _execute_real_browser_workflow(test_plan: TestPlan, session_id: str) -> ExecutionResult:
    """Execute test workflow with REAL browser automation"""
    
    logger.info(f"🚀 Starting REAL browser execution: {test_plan.name}")
    
    browser_manager = _get_browser_manager()
    screenshot_manager = _get_screenshot_manager()
    executed_steps = []
    success = True
    page = None
    
    try:
        # Initialize browser and create session
        logger.info("🌐 Initializing browser session...")
        page = await browser_manager.create_session(session_id)
        action_executor = ActionExecutor(page)
        
        # Execute each step
        for i, step in enumerate(test_plan.steps):
            step_number = i + 1
            logger.info(f"📋 Executing step {step_number}/{len(test_plan.steps)}: {step.get('action')} - {step.get('target')}")
            
            try:
                # Capture screenshot before step
                screenshot_before = await screenshot_manager.capture_step_screenshot(
                    page, session_id, step_number, f"before_{step.get('action', 'unknown')}"
                )
                
                # Execute the step
                step_result = await action_executor.execute_step(step)
                
                # Capture screenshot after step
                screenshot_after = await screenshot_manager.capture_step_screenshot(
                    page, session_id, step_number, f"after_{step.get('action', 'unknown')}"
                )
                
                # Enhance step result with additional info
                enhanced_result = {
                    "step_number": step_number,
                    "action": step.get("action", "unknown"),
                    "target": step.get("target", "unknown"),
                    "value": step.get("value", ""),
                    "status": step_result.get("status", "unknown"),
                    "message": step_result.get("message", "No message"),
                    "timestamp": asyncio.get_event_loop().time(),
                    "locator_strategy": step.get("locator_strategy", "auto"),
                    "expected_result": step.get("expected_result", "Step completed"),
                    "screenshot_before": screenshot_before,
                    "screenshot_after": screenshot_after,
                    "execution_time_ms": step_result.get("execution_time_ms", 0),
                    "browser_automation": True
                }
                
                # Add step-specific data
                enhanced_result.update({k: v for k, v in step_result.items() 
                                      if k not in enhanced_result})
                
                executed_steps.append(enhanced_result)
                
                if step_result.get("status") == "failed":
                    logger.error(f"❌ Step {step_number} failed: {step_result.get('message')}")
                    # Capture error screenshot
                    error_screenshot = await screenshot_manager.capture_error_screenshot(
                        page, session_id, f"step_{step_number}_error"
                    )
                    enhanced_result["error_screenshot"] = error_screenshot
                    success = False
                    break
                else:
                    logger.info(f"✅ Step {step_number} completed successfully")
                
                # Small delay between steps for stability
                await asyncio.sleep(0.5)
                
            except Exception as step_error:
                logger.error(f"💥 Step {step_number} exception: {str(step_error)}")
                
                # Capture error screenshot
                error_screenshot = await screenshot_manager.capture_error_screenshot(
                    page, session_id, f"step_{step_number}_exception"
                )
                
                step_result = {
                    "step_number": step_number,
                    "action": step.get("action", "unknown"),
                    "target": step.get("target", "unknown"),
                    "value": step.get("value", ""),
                    "status": "failed",
                    "message": f"💥 Step execution exception: {str(step_error)}",
                    "timestamp": asyncio.get_event_loop().time(),
                    "error_details": str(step_error),
                    "error_screenshot": error_screenshot,
                    "browser_automation": True
                }
                executed_steps.append(step_result)
                success = False
                break
        
        # Capture final screenshot
        if page:
            final_screenshot = await screenshot_manager.capture_step_screenshot(
                page, session_id, len(test_plan.steps) + 1, "final_state"
            )
            logger.info(f"📸 Final screenshot captured: {final_screenshot}")
    
    except Exception as workflow_error:
        logger.error(f"🚨 Workflow execution error: {str(workflow_error)}")
        success = False
        
        # Add error step
        executed_steps.append({
            "step_number": len(executed_steps) + 1,
            "action": "workflow_error",
            "target": "browser_automation",
            "status": "failed",
            "message": f"🚨 Workflow error: {str(workflow_error)}",
            "timestamp": asyncio.get_event_loop().time(),
            "error_details": str(workflow_error),
            "browser_automation": True
        })
    
    finally:
        # Clean up browser session
        if page:
            try:
                await browser_manager.close_session(session_id)
                logger.info(f"🧹 Browser session cleaned up: {session_id}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error cleaning up browser session: {cleanup_error}")
    
    return ExecutionResult(
        success=success,
        steps_executed=len(executed_steps),
        total_steps=len(test_plan.steps),
        execution_details=executed_steps,
        message=f"🎯 REAL browser execution: {len(executed_steps)}/{len(test_plan.steps)} steps {'completed successfully' if success else 'failed'}"
    )

# =====================================
# Enhanced Helper Functions
# =====================================

async def _parse_instructions_to_plan(instruction: TestInstruction) -> TestPlan:
    """Enhanced fallback parsing for when Azure OpenAI is unavailable"""
    steps = []
    prompt_lower = instruction.prompt.lower()
    
    # Always start with navigation
    steps.append({
        "action": "navigate",
        "target": instruction.url,
        "value": "",
        "description": f"Navigate to {instruction.url}",
        "locator_strategy": "url",
        "expected_result": "Page loads successfully"
    })
    
    # Enhanced login detection
    if instruction.username and instruction.password:
        steps.extend([
            {
                "action": "fill",
                "target": "username field",
                "value": instruction.username,
                "description": "Enter username in login form",
                "locator_strategy": "auto",
                "expected_result": "Username field populated"
            },
            {
                "action": "fill", 
                "target": "password field",
                "value": instruction.password,
                "description": "Enter password in login form",
                "locator_strategy": "auto",
                "expected_result": "Password field populated"
            },
            {
                "action": "click",
                "target": "login button",
                "value": "",
                "description": "Submit login form",
                "locator_strategy": "auto",
                "expected_result": "User successfully logged in"
            }
        ])
    
    # Enhanced pattern matching for complex scenarios
    if "navigate" in prompt_lower and "products" in prompt_lower:
        steps.append({
            "action": "click",
            "target": "products",
            "value": "",
            "description": "Navigate to products section",
            "locator_strategy": "text",
            "expected_result": "Products page loaded"
        })
    
    if "click" in prompt_lower and ("add" in prompt_lower or "create" in prompt_lower):
        steps.append({
            "action": "click",
            "target": "add product button",
            "value": "",
            "description": "Click add/create button",
            "locator_strategy": "auto",
            "expected_result": "Add form or page opened"
        })
    
    if "fill" in prompt_lower or "enter" in prompt_lower or "product name" in prompt_lower:
        if "product name" in prompt_lower:
            steps.append({
                "action": "fill",
                "target": "product name field",
                "value": "Test Product",
                "description": "Enter product name",
                "locator_strategy": "auto",
                "expected_result": "Product name entered"
            })
        else:
            steps.append({
                "action": "fill",
                "target": "input field",
                "value": "test data",
                "description": "Fill form field with test data",
                "locator_strategy": "auto",
                "expected_result": "Form field populated"
            })
    
    if "send" in prompt_lower or "submit" in prompt_lower:
        steps.append({
            "action": "click",
            "target": "send button",
            "value": "",
            "description": "Submit or send form",
            "locator_strategy": "auto",
            "expected_result": "Form submitted successfully"
        })
    
    if "verify" in prompt_lower or "check" in prompt_lower or "created" in prompt_lower:
        steps.append({
            "action": "verify",
            "target": "success confirmation",
            "value": "",
            "description": "Verify operation completed successfully",
            "locator_strategy": "text",
            "expected_result": "Success confirmation visible"
        })
    
    return TestPlan(
        name=f"Enhanced Test Plan for {instruction.url}",
        description=instruction.prompt,
        steps=steps
    )

# =====================================
# Cleanup on shutdown
# =====================================

async def cleanup_resources():
    """Clean up browser and other resources on shutdown"""
    try:
        global _browser_manager
        if _browser_manager:
            await _browser_manager.cleanup()
            logger.info("🧹 Browser resources cleaned up")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

# =====================================
# Main Function
# =====================================

def run_server():
    """Run the MCP server with proper asyncio handling"""
    try:
        logger.info(f"🚀 Starting {settings.MCP_SERVER_NAME} v{settings.MCP_SERVER_VERSION}")
        logger.info(f"🔧 Debug mode: {settings.DEBUG}")
        logger.info(f"🌐 Browser automation: {settings.BROWSER_TYPE} (headless: {settings.HEADLESS})")
        
        # Test Azure OpenAI configuration at startup
        try:
            azure_client = _get_azure_openai_client()
            if azure_client:
                logger.info("✅ Azure OpenAI client configured successfully")
            else:
                logger.warning("⚠️ Azure OpenAI client not configured - using fallback parsing")
        except Exception as e:
            logger.warning(f"⚠️ Azure OpenAI configuration issue: {e}")
        
        # Test browser automation setup
        logger.info("🌐 Initializing browser automation...")
        
        # Check if we're already in an asyncio loop
        try:
            loop = asyncio.get_running_loop()
            logger.info("Detected existing asyncio loop, using it")
            
            if USE_FASTMCP:
                logger.info("🎯 Using FastMCP implementation with REAL browser automation")
                task = loop.create_task(app.run())
            else:
                logger.info("Using basic MCP implementation")
                task = loop.create_task(run_basic_server())
            
            return task
            
        except RuntimeError:
            # No existing loop, safe to use asyncio.run()
            logger.info("No existing asyncio loop detected")
            
            if USE_FASTMCP:
                logger.info("🎯 Using FastMCP implementation with REAL browser automation")
                asyncio.run(app.run())
            else:
                logger.info("Using basic MCP implementation")
                asyncio.run(run_basic_server())
            
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise

async def run_basic_server():
    """Run basic MCP server implementation"""
    from mcp.server import stdio
    async with stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
        # Run cleanup
        try:
            asyncio.run(cleanup_resources())
        except:
            pass
    except Exception as e:
        logger.error(f"💥 Fatal server error: {str(e)}", exc_info=True)
        sys.exit(1)