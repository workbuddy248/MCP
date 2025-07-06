# =====================================
# Updated src/main.py with Instruction Analyzer Integration
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
from src.core.instruction_analyzer import InstructionAnalyzer, WorkflowType
from src.workflows.workflow_step_definitions import WorkflowStepDefinitions
from src.automation import BrowserManager, ActionExecutor, ScreenshotManager

# Initialize settings and logging
settings = Settings()
logger = setup_logging(settings)

# Global state storage
_active_sessions: Dict[str, Dict[str, Any]] = {}

# Global managers
_browser_manager = None
_screenshot_manager = None
_instruction_analyzer = None
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

def _get_instruction_analyzer():
    """Get or create instruction analyzer"""
    global _instruction_analyzer
    if _instruction_analyzer is None:
        _instruction_analyzer = InstructionAnalyzer()
        logger.info("Instruction analyzer initialized")
    return _instruction_analyzer

def _get_azure_openai_client():
    """Get or create Azure OpenAI client"""
    global _azure_openai_client
    if _azure_openai_client is None:
        try:
            from src.ai.azure_openai_client import AzureOpenAIClient
            config = settings.get_azure_openai_config()
            logger.info("config - {config}")
            _azure_openai_client = AzureOpenAIClient(config)
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure OpenAI client: {e}")
            _azure_openai_client = None
    return _azure_openai_client

# =====================================
# FastMCP Implementation with Instruction Analyzer
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
        Parse natural language test instructions using Instruction Analyzer + Azure OpenAI
        
        Args:
            prompt: Natural language description of the test scenario
            url: Target application URL (optional if included in prompt)
            username: Login username (optional if included in prompt)
            password: Login password (optional if included in prompt)
        
        Returns:
            Structured test plan with steps and metadata
        """
        try:
            logger.info(f"🧠 Analyzing instruction: {prompt[:100]}...")
            
            # Step 1: Analyze instruction to extract workflow type and parameters
            analyzer = _get_instruction_analyzer()
            analysis = analyzer.analyze_instruction(prompt)
            
            # Add provided parameters to extracted ones
            if url:
                analysis.extracted_params["url"] = url
            if username:
                analysis.extracted_params["username"] = username  
            if password:
                analysis.extracted_params["password"] = password
            
            logger.info(f"📋 Detected workflow: {analysis.workflow_type.value} (confidence: {analysis.confidence:.2f})")
            logger.info(f"🔧 Extracted parameters: {list(analysis.extracted_params.keys())}")
            
            # Step 2: Check if we have validation errors or missing required params
            if analysis.validation_errors:
                logger.warning(f"⚠️ Validation errors: {analysis.validation_errors}")
                return {
                    "status": "validation_failed",
                    "workflow_type": analysis.workflow_type.value,
                    "validation_errors": analysis.validation_errors,
                    "missing_parameters": analysis.missing_required_params,
                    "suggested_defaults": analysis.suggested_defaults,
                    "message": f"Validation failed: {'; '.join(analysis.validation_errors)}"
                }
            
            if analysis.missing_required_params:
                logger.warning(f"❌ Missing required parameters: {analysis.missing_required_params}")
                return {
                    "status": "missing_parameters",
                    "workflow_type": analysis.workflow_type.value,
                    "missing_parameters": analysis.missing_required_params,
                    "suggested_defaults": analysis.suggested_defaults,
                    "extracted_params": analysis.extracted_params,
                    "message": f"Missing required parameters: {', '.join(analysis.missing_required_params)}"
                }
            
            # Step 3: Merge extracted params with suggested defaults
            final_params = analysis.extracted_params.copy()
            final_params.update(analysis.suggested_defaults)
            
            logger.info(f"✅ Final parameters: {final_params}")
            
            # Step 4: Generate Azure OpenAI context with workflow definition
            if analysis.workflow_type != WorkflowType.UNKNOWN:
                azure_context = WorkflowStepDefinitions.get_azure_openai_context(
                    analysis.workflow_type, 
                    final_params
                )
                
                # Step 5: Use Azure OpenAI with enhanced context to generate Playwright steps
                azure_client = _get_azure_openai_client()
                if azure_client:
                    try:
                        # Enhanced prompt with workflow context
                        enhanced_prompt = f"""
{azure_context}

ORIGINAL USER INSTRUCTION: {prompt}

Generate detailed Playwright automation steps for this workflow.
"""
                        
                        ai_result = await azure_client.parse_test_instructions(
                            enhanced_prompt, 
                            final_params.get("url", ""), 
                            final_params.get("username", ""), 
                            final_params.get("password", "")
                        )
                        
                        # Convert AI result to TestPlan
                        test_plan = TestPlan(
                            name=ai_result.get("test_name", f"{analysis.workflow_type.value} Test Plan"),
                            description=ai_result.get("description", prompt),
                            steps=ai_result.get("steps", [])
                        )
                        
                        parsing_method = f"Analyzer + Azure OpenAI ({analysis.workflow_type.value})"
                        
                    except Exception as ai_error:
                        logger.warning(f"⚠️ Azure OpenAI generation failed: {ai_error}")
                        # Fallback to basic workflow steps
                        test_plan = await _generate_basic_workflow_steps(analysis.workflow_type, final_params)
                        parsing_method = f"Analyzer + Fallback ({analysis.workflow_type.value})"
                else:
                    # Fallback to basic workflow steps
                    test_plan = await _generate_basic_workflow_steps(analysis.workflow_type, final_params)
                    parsing_method = f"Analyzer + Basic ({analysis.workflow_type.value})"
            else:
                # Unknown workflow, use basic parsing
                logger.warning("❓ Unknown workflow type, using basic parsing")
                instruction = TestInstruction(
                    prompt=prompt,
                    url=final_params.get("url", "https://example.com"),
                    username=final_params.get("username", "demo_user"),
                    password=final_params.get("password", "demo_pass")
                )
                test_plan = await _parse_instructions_to_plan(instruction)
                parsing_method = "Basic Parser (Unknown Workflow)"
            
            # Store in session
            session_id = f"session_{len(_active_sessions) + 1}"
            _active_sessions[session_id] = {
                "instruction": {
                    "prompt": prompt,
                    "url": url,
                    "username": username,
                    "password": password
                },
                "analysis": {
                    "workflow_type": analysis.workflow_type.value,
                    "confidence": analysis.confidence,
                    "extracted_params": analysis.extracted_params,
                    "final_params": final_params
                },
                "test_plan": test_plan.dict(),
                "status": "planned",
                "created_at": asyncio.get_event_loop().time(),
                "parsing_method": parsing_method,
                "browser_session": None
            }
            
            logger.info(f"🎯 Successfully generated {len(test_plan.steps)} steps using {parsing_method}")
            
            return {
                "session_id": session_id,
                "status": "success",
                "workflow_type": analysis.workflow_type.value,
                "confidence": analysis.confidence,
                "test_plan": test_plan.dict(),
                "extracted_params": analysis.extracted_params,
                "final_params": final_params,
                "parsing_method": parsing_method,
                "analyzer_enhanced": True,
                "browser_automation": True,
                "message": f"🧠 Successfully analyzed and generated {len(test_plan.steps)} steps for {analysis.workflow_type.value} workflow"
            }
            
        except Exception as e:
            logger.error(f"💥 Fatal server error: {str(e)}", exc_info=True)
            raise E2ETestingError(f"Failed to parse instructions: {str(e)}")

    @app.tool()
    async def execute_test_plan(session_id: str) -> Dict[str, Any]:
        """
        Execute a test plan with REAL browser automation and self-healing retry logic
        
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
            
            logger.info(f"🚀 Starting REAL browser execution with self-healing for session {session_id}")
            
            # Execute with self-healing retry logic
            execution_result = await _execute_self_healing_workflow(test_plan, session_id, session)
            
            # Update session status
            session["status"] = "completed" if execution_result.success else "failed"
            session["execution_result"] = execution_result.dict()
            session["completed_at"] = asyncio.get_event_loop().time()
            
            logger.info(f"✅ Self-healing execution completed for session {session_id}: {execution_result.success}")
            
            return {
                "session_id": session_id,
                "status": "success",
                "execution_result": execution_result.dict(),
                "browser_automation": True,
                "self_healing": True,
                "screenshots_captured": len([step for step in execution_result.execution_details if step.get("screenshot_path")]),
                "message": f"🎉 Self-healing browser execution {'completed successfully' if execution_result.success else 'failed'} - {execution_result.steps_executed}/{execution_result.total_steps} steps executed"
            }
            
        except Exception as e:
            logger.error(f"Error executing test plan: {str(e)}")
            raise E2ETestingError(f"Failed to execute test plan: {str(e)}")

    @app.tool()
    async def get_session_status(session_id: str) -> Dict[str, Any]:
        """Get status of a test session"""
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
            
            analysis = session.get("analysis", {})
            
            return {
                "session_id": session_id,
                "status": session["status"],
                "created_at": session["created_at"],
                "completed_at": session.get("completed_at"),
                "test_plan_steps": steps_count,
                "workflow_type": analysis.get("workflow_type", "unknown"),
                "confidence": analysis.get("confidence", 0.0),
                "parsing_method": session.get("parsing_method", "unknown"),
                "analyzer_enhanced": True,
                "browser_automation": True,
                "self_healing": True,
                "screenshots_captured": screenshots_count,
                "message": f"Session {session_id} is {session['status']}"
            }
            
        except Exception as e:
            logger.error(f"Error getting session status: {str(e)}")
            raise E2ETestingError(f"Failed to get session status: {str(e)}")

    @app.tool()
    async def list_active_sessions() -> Dict[str, Any]:
        """List all active test sessions"""
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
                
                analysis = session_data.get("analysis", {})
                
                sessions.append({
                    "session_id": session_id,
                    "status": session_data.get("status", "unknown"),
                    "created_at": session_data.get("created_at", 0),
                    "steps_count": steps_count,
                    "workflow_type": analysis.get("workflow_type", "unknown"),
                    "confidence": analysis.get("confidence", 0.0),
                    "parsing_method": session_data.get("parsing_method", "unknown"),
                    "analyzer_enhanced": True,
                    "browser_automation": True,
                    "self_healing": True,
                    "screenshots_captured": screenshots_count
                })
            
            azure_client = _get_azure_openai_client()
            
            return {
                "status": "success",
                "sessions": sessions,
                "total_sessions": len(sessions),
                "azure_openai_available": azure_client is not None,
                "instruction_analyzer_enabled": True,
                "browser_automation_enabled": True,
                "self_healing_enabled": True,
                "browser_type": settings.BROWSER_TYPE,
                "headless_mode": settings.HEADLESS,
                "message": f"Found {len(sessions)} active sessions with instruction analyzer and self-healing browser automation"
            }
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            raise E2ETestingError(f"Failed to list sessions: {str(e)}")

    @app.tool()
    async def test_azure_openai_connection() -> Dict[str, Any]:
        """Test Azure OpenAI connection and configuration"""
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
                "instruction_analyzer": True,
                "browser_automation": True,
                "self_healing": True,
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
        """Test browser automation setup"""
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
                "instruction_analyzer": True,
                "self_healing": True,
                "timeout_per_step": "300000ms (5 minutes)",
                "message": "✅ Browser automation test successful with self-healing capabilities"
            }
            
        except Exception as e:
            logger.error(f"Browser automation test failed: {str(e)}")
            return {
                "status": "error",
                "browser_working": False,
                "error": str(e),
                "message": "❌ Browser automation test failed"
            }

    @app.tool()
    async def analyze_instruction(instruction: str) -> Dict[str, Any]:
        """
        Analyze instruction without executing - for testing the analyzer
        
        Args:
            instruction: Natural language instruction to analyze
        
        Returns:
            Analysis results
        """
        try:
            analyzer = _get_instruction_analyzer()
            analysis = analyzer.analyze_instruction(instruction)
            
            return {
                "status": "success",
                "workflow_type": analysis.workflow_type.value,
                "confidence": analysis.confidence,
                "extracted_params": analysis.extracted_params,
                "missing_required_params": analysis.missing_required_params,
                "validation_errors": analysis.validation_errors,
                "suggested_defaults": analysis.suggested_defaults,
                "raw_instruction": analysis.raw_instruction,
                "analyzer_working": True,
                "message": f"Analyzed as {analysis.workflow_type.value} with {analysis.confidence:.2f} confidence"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing instruction: {str(e)}")
            raise E2ETestingError(f"Failed to analyze instruction: {str(e)}")

    # Use FastMCP's built-in run method
    USE_FASTMCP = True

except ImportError as e:
    logger.warning(f"FastMCP not available, falling back to basic MCP: {e}")
    USE_FASTMCP = False

# =====================================
# Self-Healing Browser Automation Functions
# =====================================

async def _execute_self_healing_workflow(test_plan: TestPlan, session_id: str, session: Dict[str, Any]) -> ExecutionResult:
    """
    Execute test workflow with REAL browser automation and self-healing retry logic
    Retries up to 3 times if steps fail due to automation issues
    """
    
    logger.info(f"🚀 Starting self-healing browser execution: {test_plan.name}")
    
    browser_manager = _get_browser_manager()
    screenshot_manager = _get_screenshot_manager()
    executed_steps = []
    success = True
    page = None
    
    max_workflow_retries = 3
    workflow_attempt = 0
    
    while workflow_attempt < max_workflow_retries:
        workflow_attempt += 1
        logger.info(f"🔄 Workflow attempt {workflow_attempt}/{max_workflow_retries}")
        
        try:
            # Initialize browser and create session
            logger.info("🌐 Initializing browser session...")
            page = await browser_manager.create_session(f"{session_id}_attempt_{workflow_attempt}")
            action_executor = ActionExecutor(page)
            
            # Reset for retry
            executed_steps = []
            success = True
            step_failures = 0
            
            # Execute each step with self-healing
            for i, step in enumerate(test_plan.steps):
                step_number = i + 1
                logger.info(f"📋 Executing step {step_number}/{len(test_plan.steps)}: {step.get('action')} - {step.get('target')}")
                
                # Set 5-minute timeout for each step
                step['timeout'] = 300000  # 5 minutes
                step['retry_count'] = 3
                
                step_success = False
                step_attempt = 0
                max_step_retries = 3
                
                while step_attempt < max_step_retries and not step_success:
                    step_attempt += 1
                    logger.info(f"🔄 Step {step_number} attempt {step_attempt}/{max_step_retries}")
                    
                    try:
                        # Capture screenshot before step
                        screenshot_before = await screenshot_manager.capture_step_screenshot(
                            page, session_id, step_number, f"before_{step.get('action', 'unknown')}_attempt_{step_attempt}"
                        )
                        
                        # Execute the step with extended timeout
                        step_result = await action_executor.execute_step(step)
                        
                        # Capture screenshot after step
                        screenshot_after = await screenshot_manager.capture_step_screenshot(
                            page, session_id, step_number, f"after_{step.get('action', 'unknown')}_attempt_{step_attempt}"
                        )
                        
                        # Check if step succeeded
                        if step_result.get("status") == "success":
                            step_success = True
                            logger.info(f"✅ Step {step_number} succeeded on attempt {step_attempt}")
                            
                            # Create enhanced result
                            enhanced_result = {
                                "step_number": step_number,
                                "action": step.get("action", "unknown"),
                                "target": step.get("target", "unknown"),
                                "value": step.get("value", ""),
                                "status": "success",
                                "message": step_result.get("message", "No message"),
                                "timestamp": asyncio.get_event_loop().time(),
                                "locator_strategy": step.get("locator_strategy", "auto"),
                                "expected_result": step.get("expected_result", "Step completed"),
                                "screenshot_before": screenshot_before,
                                "screenshot_after": screenshot_after,
                                "execution_time_ms": step_result.get("execution_time_ms", 0),
                                "browser_automation": True,
                                "self_healing": True,
                                "attempts_made": step_attempt,
                                "workflow_attempt": workflow_attempt
                            }
                            
                            # Add step-specific data
                            enhanced_result.update({k: v for k, v in step_result.items() 
                                                  if k not in enhanced_result})
                            
                            executed_steps.append(enhanced_result)
                        else:
                            logger.warning(f"⚠️ Step {step_number} failed on attempt {step_attempt}: {step_result.get('message')}")
                            
                            if step_attempt == max_step_retries:
                                # Final failure after all retries
                                logger.error(f"❌ Step {step_number} failed after {max_step_retries} attempts")
                                
                                # Capture error screenshot
                                error_screenshot = await screenshot_manager.capture_error_screenshot(
                                    page, session_id, f"step_{step_number}_final_failure"
                                )
                                
                                enhanced_result = {
                                    "step_number": step_number,
                                    "action": step.get("action", "unknown"),
                                    "target": step.get("target", "unknown"),
                                    "value": step.get("value", ""),
                                    "status": "failed",
                                    "message": f"❌ Step failed after {max_step_retries} attempts: {step_result.get('message')}",
                                    "timestamp": asyncio.get_event_loop().time(),
                                    "error_details": step_result.get("error_details", ""),
                                    "error_screenshot": error_screenshot,
                                    "screenshot_before": screenshot_before,
                                    "screenshot_after": screenshot_after,
                                    "browser_automation": True,
                                    "self_healing": True,
                                    "attempts_made": step_attempt,
                                    "workflow_attempt": workflow_attempt
                                }
                                executed_steps.append(enhanced_result)
                                step_failures += 1
                                break
                            else:
                                # Wait before retry
                                await asyncio.sleep(5)  # Wait 5 seconds between step retries
                        
                    except Exception as step_error:
                        logger.error(f"💥 Step {step_number} exception on attempt {step_attempt}: {str(step_error)}")
                        
                        if step_attempt == max_step_retries:
                            # Final exception after all retries
                            error_screenshot = await screenshot_manager.capture_error_screenshot(
                                page, session_id, f"step_{step_number}_exception"
                            )
                            
                            step_result = {
                                "step_number": step_number,
                                "action": step.get("action", "unknown"),
                                "target": step.get("target", "unknown"),
                                "value": step.get("value", ""),
                                "status": "failed",
                                "message": f"💥 Step exception after {max_step_retries} attempts: {str(step_error)}",
                                "timestamp": asyncio.get_event_loop().time(),
                                "error_details": str(step_error),
                                "error_screenshot": error_screenshot,
                                "browser_automation": True,
                                "self_healing": True,
                                "attempts_made": step_attempt,
                                "workflow_attempt": workflow_attempt
                            }
                            executed_steps.append(step_result)
                            step_failures += 1
                            break
                        else:
                            # Wait before retry
                            await asyncio.sleep(5)
                
                # If step failed, decide whether to continue or regenerate workflow
                if not step_success:
                    if step_failures >= 2:  # If multiple steps fail, regenerate entire workflow
                        logger.warning(f"🔄 Multiple step failures ({step_failures}), will regenerate workflow")
                        success = False
                        break
                    else:
                        # Continue with next steps for single failures
                        logger.info(f"⏭️ Continuing with next step despite failure in step {step_number}")
                
                # Small delay between steps for stability
                await asyncio.sleep(2)
            
            # Capture final screenshot
            if page:
                final_screenshot = await screenshot_manager.capture_step_screenshot(
                    page, session_id, len(test_plan.steps) + 1, f"final_state_attempt_{workflow_attempt}"
                )
                logger.info(f"📸 Final screenshot captured: {final_screenshot}")
            
            # Check if workflow succeeded
            if success and step_failures == 0:
                logger.info(f"🎉 Workflow succeeded on attempt {workflow_attempt}")
                break
            elif workflow_attempt < max_workflow_retries:
                logger.warning(f"🔄 Workflow attempt {workflow_attempt} had issues, regenerating steps for retry...")
                
                # Regenerate steps using Azure OpenAI for next attempt
                if workflow_attempt < max_workflow_retries:
                    await _regenerate_workflow_steps(session, executed_steps)
            
        except Exception as workflow_error:
            logger.error(f"🚨 Workflow execution error on attempt {workflow_attempt}: {str(workflow_error)}")
            
            if workflow_attempt == max_workflow_retries:
                success = False
                # Add error step
                executed_steps.append({
                    "step_number": len(executed_steps) + 1,
                    "action": "workflow_error",
                    "target": "browser_automation",
                    "status": "failed",
                    "message": f"🚨 Workflow error after {max_workflow_retries} attempts: {str(workflow_error)}",
                    "timestamp": asyncio.get_event_loop().time(),
                    "error_details": str(workflow_error),
                    "browser_automation": True,
                    "self_healing": True,
                    "workflow_attempt": workflow_attempt
                })
            
        finally:
            # Clean up browser session for this attempt
            if page:
                try:
                    await browser_manager.close_session(f"{session_id}_attempt_{workflow_attempt}")
                    logger.info(f"🧹 Browser session cleaned up for attempt {workflow_attempt}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Error cleaning up browser session: {cleanup_error}")
    
    # Determine final success status
    final_success = success and len([step for step in executed_steps if step.get("status") == "failed"]) == 0
    
    return ExecutionResult(
        success=final_success,
        steps_executed=len(executed_steps),
        total_steps=len(test_plan.steps),
        execution_details=executed_steps,
        message=f"🎯 Self-healing execution: {len(executed_steps)}/{len(test_plan.steps)} steps, {'completed successfully' if final_success else 'failed'} after {workflow_attempt} workflow attempts"
    )

async def _regenerate_workflow_steps(session: Dict[str, Any], failed_steps: List[Dict[str, Any]]) -> None:
    """
    Regenerate workflow steps using Azure OpenAI based on failure analysis
    """
    try:
        logger.info("🔄 Regenerating workflow steps based on failure analysis...")
        
        analysis = session.get("analysis", {})
        workflow_type = WorkflowType(analysis.get("workflow_type", "UNKNOWN"))
        final_params = analysis.get("final_params", {})
        
        # Create failure context for Azure OpenAI
        failure_context = []
        for step in failed_steps:
            if step.get("status") == "failed":
                failure_context.append(f"Step {step.get('step_number')}: {step.get('action')} on '{step.get('target')}' failed - {step.get('message')}")
        
        if failure_context and workflow_type != WorkflowType.UNKNOWN:
            azure_client = _get_azure_openai_client()
            if azure_client:
                # Enhanced context with failure information
                base_context = WorkflowStepDefinitions.get_azure_openai_context(workflow_type, final_params)
                
                enhanced_context = f"""
{base_context}

PREVIOUS EXECUTION FAILURES:
{chr(10).join(failure_context)}

REGENERATION INSTRUCTIONS:
The previous workflow execution encountered failures. Please regenerate the workflow steps with:
1. More robust element selectors
2. Additional wait times
3. Alternative approaches for failed steps
4. Better error handling

Focus on fixing the specific failures mentioned above while maintaining the overall workflow goals.
"""
                
                try:
                    ai_result = await azure_client.parse_test_instructions(
                        enhanced_context,
                        final_params.get("url", ""),
                        final_params.get("username", ""),
                        final_params.get("password", "")
                    )
                    
                    # Update session with regenerated steps
                    regenerated_plan = TestPlan(
                        name=ai_result.get("test_name", f"Regenerated {workflow_type.value} Test Plan"),
                        description=ai_result.get("description", "Regenerated workflow"),
                        steps=ai_result.get("steps", [])
                    )
                    
                    session["test_plan"] = regenerated_plan.dict()
                    logger.info(f"✅ Regenerated {len(regenerated_plan.steps)} workflow steps")
                    
                except Exception as regen_error:
                    logger.warning(f"⚠️ Failed to regenerate steps: {regen_error}")
        
    except Exception as e:
        logger.error(f"❌ Error in workflow regeneration: {str(e)}")

async def _generate_basic_workflow_steps(workflow_type: WorkflowType, params: Dict[str, Any]) -> TestPlan:
    """Generate basic workflow steps when Azure OpenAI is not available"""
    logger.info(f"🔧 Generating basic workflow steps for {workflow_type.value}")
    
    steps = []
    
    # Common login steps for workflows that need authentication
    if workflow_type in [WorkflowType.CREATE_FABRIC, WorkflowType.MODIFY_FABRIC, WorkflowType.DELETE_FABRIC]:
        steps.extend([
            {
                "action": "navigate",
                "target": params.get("url", "https://example.com"),
                "value": "",
                "description": f"Navigate to {params.get('url', 'target URL')}",
                "locator_strategy": "url",
                "expected_result": "Page loads successfully",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "fill",
                "target": "username field",
                "value": params.get("username", "admin"),
                "description": "Enter username in login form",
                "locator_strategy": "auto",
                "expected_result": "Username field populated",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "fill",
                "target": "password field",
                "value": params.get("password", "password"),
                "description": "Enter password in login form",
                "locator_strategy": "auto",
                "expected_result": "Password field populated",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "click",
                "target": "login button",
                "value": "",
                "description": "Submit login form",
                "locator_strategy": "auto",
                "expected_result": "User successfully logged in",
                "timeout": 300000,
                "retry_count": 3
            }
        ])
    
    # Workflow-specific steps
    if workflow_type == WorkflowType.CREATE_FABRIC:
        steps.extend([
            {
                "action": "click",
                "target": "fabric menu",
                "value": "",
                "description": "Navigate to fabric management section",
                "locator_strategy": "text",
                "expected_result": "Fabric management page opens",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "click",
                "target": "create fabric button",
                "value": "",
                "description": "Open fabric creation form",
                "locator_strategy": "auto",
                "expected_result": "Fabric creation form appears",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "fill",
                "target": "fabric name field",
                "value": params.get("fabric_name", "DefaultFabric"),
                "description": "Enter fabric name",
                "locator_strategy": "auto",
                "expected_result": "Fabric name entered",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "fill",
                "target": "BGP ASN field",
                "value": str(params.get("bgp_asn", "65001")),
                "description": "Enter BGP ASN number",
                "locator_strategy": "auto",
                "expected_result": "BGP ASN entered and validated",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "click",
                "target": "create fabric submit button",
                "value": "",
                "description": "Submit fabric creation",
                "locator_strategy": "auto",
                "expected_result": "Fabric creation initiated",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "verify",
                "target": "fabric creation success",
                "value": "fabric created",
                "description": "Verify fabric was created successfully",
                "locator_strategy": "text",
                "expected_result": "Success confirmation visible",
                "timeout": 300000,
                "retry_count": 3
            }
        ])
    
    elif workflow_type == WorkflowType.LOGIN_ONLY:
        steps.extend([
            {
                "action": "verify",
                "target": "login success",
                "value": "dashboard",
                "description": "Verify successful login",
                "locator_strategy": "text",
                "expected_result": "Welcome to Catalyst Center!",
                "timeout": 300000,
                "retry_count": 3
            }
        ])
    
    elif workflow_type == WorkflowType.GET_FABRIC:
        steps.extend([
           {
                "action": "click",
                "target": "fabric menu",
                "value": "",
                "description": "Navigate to fabric management section",
                "locator_strategy": "text",
                "expected_result": "Fabric management page opens",
                "timeout": 120000,
                "retry_count": 2
           },
           {
            "action": "wait",
            "target": "fabric list",
            "value": "5",
            "description": "Wait for fabric list to load",
            "locator_strategy": "auto",
            "expected_result": "Fabric list is visible",
            "timeout": 60000,
            "retry_count": 2
           },
           {
            "action": "verify",
            "target": "fabric information",
            "value": "fabric",
            "description": "Verify fabric information is displayed",
            "locator_strategy": "text",
            "expected_result": "Fabric data visible on page",
            "timeout": 30000,
            "retry_count": 2
           }
        ])
    
    return TestPlan(
        name=f"Basic {workflow_type.value} Workflow",
        description=f"Basic implementation of {workflow_type.value}",
        steps=steps
    )

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
        "expected_result": "Page loads successfully",
        "timeout": 300000,
        "retry_count": 3
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
                "expected_result": "Username field populated",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "fill", 
                "target": "password field",
                "value": instruction.password,
                "description": "Enter password in login form",
                "locator_strategy": "auto",
                "expected_result": "Password field populated",
                "timeout": 300000,
                "retry_count": 3
            },
            {
                "action": "click",
                "target": "login button",
                "value": "",
                "description": "Submit login form",
                "locator_strategy": "auto",
                "expected_result": "User successfully logged in",
                "timeout": 300000,
                "retry_count": 3
            }
        ])
    
    # Add verification step
    steps.append({
        "action": "verify",
        "target": "page loaded",
        "value": "",
        "description": "Verify page loaded successfully",
        "locator_strategy": "text",
        "expected_result": "Expected content visible",
        "timeout": 300000,
        "retry_count": 3
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
        logger.info(f"🧠 Instruction analyzer: ENABLED")
        logger.info(f"🔄 Self-healing workflows: ENABLED (5min timeouts, 3 retries)")
        
        # Test components at startup
        try:
            azure_client = _get_azure_openai_client()
            if azure_client:
                logger.info("✅ Azure OpenAI client configured successfully")
            else:
                logger.warning("⚠️ Azure OpenAI client not configured - using fallback parsing")
        except Exception as e:
            logger.warning(f"⚠️ Azure OpenAI configuration issue: {e}")
        
        # Test instruction analyzer
        try:
            analyzer = _get_instruction_analyzer()
            logger.info("✅ Instruction analyzer initialized successfully")
        except Exception as e:
            logger.error(f"❌ Instruction analyzer initialization failed: {e}")
        
        # For FastMCP, we should NOT try to detect existing loops
        # FastMCP handles its own event loop management
        if USE_FASTMCP:
            logger.info("🎯 Using FastMCP implementation with instruction analyzer and self-healing")
            # Let FastMCP handle the event loop
            app.run()
        else:
            logger.info("Using basic MCP implementation")
            # For basic MCP, we need our own event loop
            asyncio.run(run_basic_server())
            
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested by user")
    except Exception as e:
        logger.error(f"💥 Server error: {str(e)}", exc_info=True)
        raise

async def run_basic_server():
    """Run basic MCP server implementation"""
    from mcp.server import stdio
    async with stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

async def main_async():
    """Async main function for testing purposes"""
    try:
        logger.info(f"🚀 Starting {settings.MCP_SERVER_NAME} v{settings.MCP_SERVER_VERSION} (async mode)")
        logger.info(f"🔧 Debug mode: {settings.DEBUG}")
        logger.info(f"🌐 Browser automation: {settings.BROWSER_TYPE} (headless: {settings.HEADLESS})")
        logger.info(f"🧠 Instruction analyzer: ENABLED")
        logger.info(f"🔄 Self-healing workflows: ENABLED (5min timeouts, 3 retries)")
        
        # Test components
        try:
            azure_client = _get_azure_openai_client()
            if azure_client:
                logger.info("✅ Azure OpenAI client configured successfully")
            else:
                logger.warning("⚠️ Azure OpenAI client not configured - using fallback parsing")
        except Exception as e:
            logger.warning(f"⚠️ Azure OpenAI configuration issue: {e}")
        
        try:
            analyzer = _get_instruction_analyzer()
            logger.info("✅ Instruction analyzer initialized successfully")
        except Exception as e:
            logger.error(f"❌ Instruction analyzer initialization failed: {e}")
        
        if USE_FASTMCP:
            logger.info("🎯 Running FastMCP in async mode")
            # For testing, we can call the server tools directly
            # This won't start the actual MCP server but will test our tools
            
            # Test parse instructions
            test_result = await parse_test_instructions(
                "test create fabric workflow on https://httpbin.org username admin password secret BGP ASN 65001"
            )
            logger.info(f"✅ Test parse result: {test_result['status']}")
            
            # Test analyzer
            analyze_result = await analyze_instruction(
                "test network site hierarchy workflow area name TestArea building name TestBuilding"
            )
            logger.info(f"✅ Test analyze result: {analyze_result['workflow_type']}")
            
            logger.info("🎉 Async testing completed successfully")
        else:
            await run_basic_server()
            
    except Exception as e:
        logger.error(f"💥 Async main error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        # Check if we want to run in test mode
        if len(sys.argv) > 1 and sys.argv[1] == "--test":
            # Run in test mode (async)
            asyncio.run(main_async())
        else:
            # Run normal MCP server
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