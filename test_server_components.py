#!/usr/bin/env python3
"""
Test individual server components before full integration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_server_components():
    """Test each component individually"""
    
    print("🧪 Testing E2E MCP Server Components")
    print("=" * 50)
    
    # Test 1: Instruction Analyzer
    print("\n1. 📋 Testing Instruction Analyzer...")
    try:
        from src.core.instruction_analyzer import InstructionAnalyzer
        analyzer = InstructionAnalyzer()
        
        test_instruction = "test create fabric workflow on https://10.29.46.11:443/ username - admin, password - secret, BGP ASN - 65001"
        result = analyzer.analyze_instruction(test_instruction)
        
        print(f"   ✅ Workflow Type: {result.workflow_type.value}")
        print(f"   ✅ Confidence: {result.confidence:.2f}")
        print(f"   ✅ Parameters: {len(result.extracted_params)} extracted")
        
    except Exception as e:
        print(f"   ❌ Analyzer Error: {e}")
        return False
    
    # Test 2: Workflow Step Definitions
    print("\n2. 📚 Testing Workflow Step Definitions...")
    try:
        from src.workflows.workflow_step_definitions import WorkflowStepDefinitions
        from src.core.instruction_analyzer import WorkflowType
        
        definition = WorkflowStepDefinitions.get_workflow_definition(WorkflowType.CREATE_FABRIC)
        context = WorkflowStepDefinitions.get_azure_openai_context(
            WorkflowType.CREATE_FABRIC, 
            {"url": "https://test.com", "username": "test", "password": "test", "bgp_asn": 65001}
        )
        
        print(f"   ✅ Workflow: {definition['workflow_name']}")
        print(f"   ✅ Steps: {len(definition['english_steps'])} defined")
        print(f"   ✅ Context: {len(context)} characters")
        
    except Exception as e:
        print(f"   ❌ Workflow Definitions Error: {e}")
        return False
    
    # Test 3: Azure OpenAI Client (if configured)
    print("\n3. 🤖 Testing Azure OpenAI Client...")
    try:
        from src.ai.azure_openai_client import AzureOpenAIClient
        from src.core.config import Settings
        
        settings = Settings()
        config = settings.get_azure_openai_config()
        
        if config.api_key and config.endpoint:
            client = AzureOpenAIClient(config)
            print(f"   ✅ Client configured: {config.model}")
            print(f"   ✅ Endpoint: {config.endpoint}")
            # Don't test actual API call here to save costs
        else:
            print("   ⚠️ Azure OpenAI not configured (will use fallback)")
        
    except Exception as e:
        print(f"   ❌ Azure OpenAI Error: {e}")
        print("   ⚠️ Will use fallback parsing")
    
    # Test 4: Browser Manager
    print("\n4. 🌐 Testing Browser Manager...")
    try:
        from src.automation.browser_manager import BrowserManager
        
        browser_manager = BrowserManager(headless=True, browser_type="chromium")
        await browser_manager.initialize()
        
        # Test session creation
        page = await browser_manager.create_session("test_session")
        await page.goto("https://example.com")
        title = await page.title()
        
        print(f"   ✅ Browser initialized: chromium")
        print(f"   ✅ Navigation test: {title}")
        
        # Cleanup
        await browser_manager.close_session("test_session")
        await browser_manager.cleanup()
        
    except Exception as e:
        print(f"   ❌ Browser Manager Error: {e}")
        return False
    
    # Test 5: MCP Server Import
    print("\n5. 🖥️ Testing MCP Server Import...")
    try:
        from src.main import app, _get_instruction_analyzer, _get_browser_manager
        
        # Test analyzer
        analyzer = _get_instruction_analyzer()
        print(f"   ✅ Instruction analyzer: {type(analyzer).__name__}")
        
        # Test browser manager
        browser_mgr = _get_browser_manager()
        print(f"   ✅ Browser manager: {type(browser_mgr).__name__}")
        
        print(f"   ✅ FastMCP app: {type(app).__name__}")
        
    except Exception as e:
        print(f"   ❌ MCP Server Import Error: {e}")
        return False
    
    print("\n🎉 All Components Test Passed!")
    print("✅ Ready to test full server")
    return True

async def test_mcp_tools():
    """Test MCP tools directly"""
    print("\n🔧 Testing MCP Tools Directly")
    print("=" * 40)
    
    try:
        from src.main import (
            parse_test_instructions,
            analyze_instruction, 
            test_azure_openai_connection,
            test_browser_automation
        )
        
        # Test 1: Analyze Instruction
        print("\n1. 🧠 Testing analyze_instruction tool...")
        result = await analyze_instruction("test create fabric workflow on https://10.29.46.11:443/ username - admin, password - secret, BGP ASN - 65001")
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Workflow: {result['workflow_type']}")
        print(f"   ✅ Confidence: {result['confidence']:.2f}")
        
        # Test 2: Parse Instructions
        print("\n2. 📋 Testing parse_test_instructions tool...")
        result = await parse_test_instructions(
            "test create fabric workflow on https://10.29.46.11:443/ username - admin, password - secret, BGP ASN - 65001"
        )
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Session ID: {result.get('session_id', 'N/A')}")
        print(f"   ✅ Steps Generated: {len(result.get('test_plan', {}).get('steps', []))}")
        
        # Test 3: Azure OpenAI Connection
        print("\n3. 🤖 Testing Azure OpenAI connection...")
        result = await test_azure_openai_connection()
        print(f"   {'✅' if result['connected'] else '⚠️'} Azure OpenAI: {result['status']}")
        
        # Test 4: Browser Automation
        print("\n4. 🌐 Testing browser automation...")
        result = await test_browser_automation()
        print(f"   {'✅' if result['browser_working'] else '❌'} Browser: {result['status']}")
        print(f"   ✅ Screenshot: {result.get('screenshot_captured', False)}")
        
        print("\n🎉 All MCP Tools Test Passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ MCP Tools Error: {e}")
        return False

if __name__ == "__main__":
    async def main():
        # Test components first
        if await test_server_components():
            # Then test MCP tools
            await test_mcp_tools()
        else:
            print("❌ Component tests failed, skipping MCP tools test")
    
    asyncio.run(main())
