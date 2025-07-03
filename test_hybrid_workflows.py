#!/usr/bin/env python3
"""
Hybrid Workflow System Test Script
Tests template detection, parameter extraction, and workflow execution
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_template_detection():
    """Test workflow template detection from natural language"""
    print("🔍 Testing Template Detection...")
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Test different instruction types
        test_instructions = [
            ("Create network hierarchy with area SJC and building B1 at 192.168.1.100", "network_site_hierarchy"),
            ("Login to DNA Center at 10.10.10.100 with admin credentials", "dna_center_login"),
            ("Add area called NYC and building Tower1 in network hierarchy", "network_site_hierarchy"),
            ("Navigate to network hierarchy and create site structure", "network_site_hierarchy")
        ]
        
        results = []
        
        for instruction, expected_template in test_instructions:
            print(f"  🧠 Testing: {instruction[:60]}...")
            
            detected_template, confidence, parameters = manager.detect_workflow_from_instruction(instruction)
            
            if detected_template == expected_template:
                print(f"    ✅ Correct detection: {detected_template} (confidence: {confidence:.1%})")
                print(f"    📊 Extracted parameters: {list(parameters.keys())}")
                results.append(True)
            elif detected_template:
                print(f"    ⚠️ Detected: {detected_template}, Expected: {expected_template}")
                results.append(False)
            else:
                print(f"    ❌ No template detected (expected: {expected_template})")
                results.append(False)
        
        success_rate = sum(results) / len(results)
        print(f"\n📊 Template Detection Results: {sum(results)}/{len(results)} correct ({success_rate:.1%})")
        
        return success_rate >= 0.75  # 75% success rate
        
    except Exception as e:
        print(f"❌ Template detection test failed: {e}")
        return False

async def test_parameter_extraction():
    """Test parameter extraction from instructions"""
    print("�� Testing Parameter Extraction...")
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Test parameter extraction
        test_cases = [
            ("Create hierarchy at 192.168.1.100 with area NYC and building Tower1", 
             ["cluster_ip", "area_name", "building_name"]),
            ("Login to DNA Center 10.10.10.50 with username admin", 
             ["cluster_ip", "username"]),
            ("Add area SJC and building B2 in San Jose location", 
             ["area_name", "building_name", "address_search"])
        ]
        
        results = []
        
        for instruction, expected_params in test_cases:
            print(f"  🧩 Testing: {instruction}")
            
            # Detect template and extract parameters
            template_name, confidence, extracted_params = manager.detect_workflow_from_instruction(instruction)
            
            if template_name:
                found_params = [param for param in expected_params if param in extracted_params]
                success = len(found_params) >= len(expected_params) * 0.6  # At least 60% of expected params
                
                if success:
                    print(f"    ✅ Found parameters: {list(extracted_params.keys())}")
                    print(f"    📋 Values: {extracted_params}")
                else:
                    print(f"    ⚠️ Expected: {expected_params}, Found: {list(extracted_params.keys())}")
                
                results.append(success)
            else:
                print(f"    ❌ No template detected")
                results.append(False)
        
        success_rate = sum(results) / len(results)
        print(f"\n📊 Parameter Extraction Results: {sum(results)}/{len(results)} successful ({success_rate:.1%})")
        
        return success_rate >= 0.6
        
    except Exception as e:
        print(f"❌ Parameter extraction test failed: {e}")
        return False

async def test_workflow_generation():
    """Test workflow generation from templates"""
    print("⚙️ Testing Workflow Generation...")
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Test workflow generation for network hierarchy
        test_parameters = {
            "cluster_ip": "192.168.1.100",
            "area_name": "TestArea",
            "building_name": "TestBuilding",
            "address_search": "San Jose"
        }
        
        print(f"  📋 Generating workflow for network_site_hierarchy...")
        print(f"  📊 Parameters: {test_parameters}")
        
        workflow = manager.generate_workflow_from_template("network_site_hierarchy", test_parameters)
        
        # Validate workflow structure
        required_fields = ["test_name", "description", "steps", "template_name"]
        missing_fields = [field for field in required_fields if field not in workflow]
        
        if missing_fields:
            print(f"    ❌ Missing required fields: {missing_fields}")
            return False
        
        steps = workflow["steps"]
        if len(steps) < 10:  # Network hierarchy should have many steps
            print(f"    ❌ Too few steps generated: {len(steps)}")
            return False
        
        # Check for essential DNA Center steps
        actions = [step.get("action") for step in steps]
        essential_actions = ["navigate", "click", "fill", "verify"]
        missing_actions = [action for action in essential_actions if action not in actions]
        
        if missing_actions:
            print(f"    ⚠️ Missing essential actions: {missing_actions}")
        
        # Check parameter substitution
        substituted_correctly = True
        for step in steps:
            for field in ["target", "value", "description"]:
                if field in step and step[field]:
                    if "{cluster_ip}" in step[field] or "{area_name}" in step[field]:
                        print(f"    ❌ Parameter not substituted in step: {step[field]}")
                        substituted_correctly = False
                        break
        
        if substituted_correctly:
            print(f"    ✅ Generated {len(steps)} steps with proper parameter substitution")
            print(f"    ✅ Template: {workflow['template_name']} v{workflow['template_version']}")
            print(f"    ✅ Estimated duration: {workflow['estimated_duration']} seconds")
        else:
            print(f"    ❌ Parameter substitution failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow generation test failed: {e}")
        return False

async def test_template_listing():
    """Test template listing and management"""
    print("📋 Testing Template Management...")
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Test listing all templates
        all_templates = manager.list_templates()
        print(f"  📄 Total templates available: {len(all_templates)}")
        
        for name, template in all_templates.items():
            print(f"    • {name}: {template.description} ({template.category})")
        
        # Test listing by category
        dna_templates = manager.list_templates_by_category("dna_center_design")
        print(f"  🔬 DNA Center design templates: {len(dna_templates)}")
        
        auth_templates = manager.list_templates_by_category("authentication")
        print(f"  🔐 Authentication templates: {len(auth_templates)}")
        
        # Verify essential templates exist
        essential_templates = ["network_site_hierarchy", "dna_center_login"]
        missing_templates = [t for t in essential_templates if t not in all_templates]
        
        if missing_templates:
            print(f"    ❌ Missing essential templates: {missing_templates}")
            return False
        else:
            print(f"    ✅ All essential templates present")
        
        return True
        
    except Exception as e:
        print(f"❌ Template management test failed: {e}")
        return False

async def test_workflow_suggestions():
    """Test workflow suggestions"""
    print("💡 Testing Workflow Suggestions...")
    
    try:
        from src.workflows.enhanced_workflow_manager import EnhancedWorkflowManager
        
        manager = EnhancedWorkflowManager()
        
        # Test suggestions for different instructions
        test_instructions = [
            "Create network site hierarchy",
            "Login to DNA Center",
            "Add area and building to network",
            "Configure network hierarchy"
        ]
        
        results = []
        
        for instruction in test_instructions:
            print(f"  🤔 Getting suggestions for: {instruction}")
            
            suggestions = manager.get_workflow_suggestions(instruction)
            
            if suggestions:
                print(f"    ✅ Found {len(suggestions)} suggestions:")
                for i, suggestion in enumerate(suggestions[:3]):  # Show top 3
                    print(f"      {i+1}. {suggestion['template_name']} (confidence: {suggestion['confidence']:.1%})")
                results.append(True)
            else:
                print(f"    ❌ No suggestions found")
                results.append(False)
        
        success_rate = sum(results) / len(results)
        print(f"\n📊 Workflow Suggestions Results: {sum(results)}/{len(results)} successful ({success_rate:.1%})")
        
        return success_rate >= 0.75
        
    except Exception as e:
        print(f"❌ Workflow suggestions test failed: {e}")
        return False

async def main():
    """Run all hybrid workflow system tests"""
    print("🚀 Starting Hybrid Workflow System Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Template Detection
    print("\n1️⃣ Template Detection Test")
    results.append(await test_template_detection())
    
    # Test 2: Parameter Extraction
    print("\n2️⃣ Parameter Extraction Test")
    results.append(await test_parameter_extraction())
    
    # Test 3: Workflow Generation
    print("\n3️⃣ Workflow Generation Test")
    results.append(await test_workflow_generation())
    
    # Test 4: Template Management
    print("\n4️⃣ Template Management Test")
    results.append(await test_template_listing())
    
    # Test 5: Workflow Suggestions
    print("\n5️⃣ Workflow Suggestions Test")
    results.append(await test_workflow_suggestions())
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Overall Hybrid Workflow Results: {sum(results)}/{len(results)} test suites passed")
    
    if all(results):
        print("🎉 All hybrid workflow tests passed!")
        print("\n✅ Your DNA Center E2E testing server now has:")
        print("  • Template-based workflow execution")
        print("  • Natural language instruction parsing") 
        print("  • Smart parameter extraction")
        print("  • DNA Center specific workflows")
        print("  • AI-enhanced workflow learning")
        print("  • Hybrid template + AI approach")
    elif sum(results) >= 4:
        print("✅ Hybrid workflow system is mostly working!")
        print("\n⚠️ Some tests failed, but core functionality is operational.")
    else:
        print("❌ Hybrid workflow system needs attention.")
        print("\n🔧 Check the error messages above and ensure:")
        print("  • All new files are created in the correct directories")
        print("  • Import paths are correct")
        print("  • No syntax errors in the new modules")
    
    return sum(results) >= 4

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)
