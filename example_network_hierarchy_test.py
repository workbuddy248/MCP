#!/usr/bin/env python3
"""
Example: Testing Network Hierarchy Workflow
Shows how to use the hybrid workflow system for DNA Center testing
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def example_natural_language_instruction():
    """Example: Using natural language instruction"""
    print("🗣️ Example: Natural Language Instruction")
    print("=" * 50)
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Natural language instruction
        instruction = "Create network hierarchy at 192.168.1.100 with area SJC and building B1 in San Jose"
        
        print(f"📝 Instruction: {instruction}")
        print()
        
        # Detect workflow and extract parameters
        template_name, confidence, parameters = manager.detect_workflow_from_instruction(instruction)
        
        print(f"🔍 Detected Template: {template_name}")
        print(f"📊 Confidence: {confidence:.1%}")
        print(f"🔧 Extracted Parameters: {parameters}")
        print()
        
        if template_name and confidence > 0.7:
            # Generate workflow from template
            workflow = manager.generate_workflow_from_template(template_name, parameters)
            
            print(f"✅ Generated Workflow: {workflow['test_name']}")
            print(f"📋 Steps: {len(workflow['steps'])}")
            print(f"⏱️ Estimated Duration: {workflow['estimated_duration']} seconds")
            print()
            
            # Show first few steps
            print("🔍 First 5 steps:")
            for i, step in enumerate(workflow['steps'][:5]):
                print(f"  {i+1}. {step['action']} - {step['description']}")
            
            return True
        else:
            print("❌ Template detection failed or confidence too low")
            return False
            
    except Exception as e:
        print(f"❌ Example failed: {e}")
        return False

async def example_direct_template_execution():
    """Example: Direct template execution with parameters"""
    print("\n🎯 Example: Direct Template Execution")
    print("=" * 50)
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Direct template execution with specific parameters
        template_name = "network_site_hierarchy"
        parameters = {
            "cluster_ip": "192.168.1.100",
            "area_name": "NYC",
            "building_name": "Tower1", 
            "address_search": "New York"
        }
        
        print(f"🎯 Template: {template_name}")
        print(f"🔧 Parameters: {parameters}")
        print()
        
        # Generate workflow
        workflow = manager.generate_workflow_from_template(template_name, parameters)
        
        print(f"✅ Generated Workflow: {workflow['test_name']}")
        print(f"📋 Total Steps: {len(workflow['steps'])}")
        print(f"🎯 Template Version: {workflow['template_version']}")
        print()
        
        # Show key steps
        key_actions = ["navigate", "hover_global_menu", "fill_area_name", "fill_building_name"]
        print("🔑 Key steps:")
        for step in workflow['steps']:
            if any(action in step.get('description', '').lower() for action in key_actions):
                print(f"  • {step['action']}: {step['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct template example failed: {e}")
        return False

async def example_workflow_suggestions():
    """Example: Getting workflow suggestions"""
    print("\n💡 Example: Workflow Suggestions")
    print("=" * 50)
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Ambiguous instruction
        instruction = "Set up network structure"
        
        print(f"📝 Ambiguous Instruction: {instruction}")
        print()
        
        # Get suggestions
        suggestions = manager.get_workflow_suggestions(instruction)
        
        print(f"💡 Workflow Suggestions ({len(suggestions)} found):")
        for i, suggestion in enumerate(suggestions):
            print(f"  {i+1}. {suggestion['template_name']}")
            print(f"     📖 {suggestion['description']}")
            print(f"     📊 Confidence: {suggestion['confidence']:.1%}")
            print(f"     ⏱️ Duration: {suggestion['estimated_duration']} seconds")
            print()
        
        return len(suggestions) > 0
        
    except Exception as e:
        print(f"❌ Suggestions example failed: {e}")
        return False

async def main():
    """Run all examples"""
    print("🚀 DNA Center Hybrid Workflow Examples")
    print("=" * 60)
    
    results = []
    
    # Example 1: Natural Language
    results.append(await example_natural_language_instruction())
    
    # Example 2: Direct Template
    results.append(await example_direct_template_execution())
    
    # Example 3: Suggestions
    results.append(await example_workflow_suggestions())
    
    print("\n" + "=" * 60)
    print(f"📊 Examples Results: {sum(results)}/{len(results)} successful")
    
    if all(results):
        print("🎉 All examples completed successfully!")
        print("\n🎯 Ready to use hybrid workflow system for DNA Center testing!")
    else:
        print("⚠️ Some examples failed - check setup and dependencies")
    
    return sum(results) >= 2

if __name__ == "__main__":
    asyncio.run(main())
