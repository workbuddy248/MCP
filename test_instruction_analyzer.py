#!/usr/bin/env python3
"""
Test script for the InstructionAnalyzer
Tests workflow detection and parameter extraction
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.instruction_analyzer import InstructionAnalyzer, WorkflowType

def test_instruction_analyzer():
    """Test the instruction analyzer with various instructions"""
    
    analyzer = InstructionAnalyzer()
    
    test_instructions = [
        # Create Fabric Workflow Tests (includes login automatically)
        "test create fabric workflow on https://10.29.46.11:443/ username - name, password - pass, BGP ASN - 1300 and with pools",
        "create fabric at 192.168.1.100:8443 user admin password secret123 ASN 65001 with 4 spines and 8 leafs",
        "build new fabric on server 10.0.0.1 login test pass test123 BGP ASN 64512 fabric name ProductionFabric",
        
        # Login Only Workflow Tests (just authenticate)
        "just login to https://example.com username admin password secret",
        "only authenticate to server 10.1.1.1 user test pass 123",
        "connect to server 192.168.1.1:443 with admin/admin123",
        
        # Modify Fabric Tests
        "modify fabric TestFabric on 10.1.1.1 user admin pass secret",
        "update existing fabric ProductionFabric at server 192.168.1.100",
        
        # Delete Fabric Tests  
        "delete fabric OldFabric from 10.2.2.2 username admin password test123",
        "remove fabric TestEnvironment on server 192.168.1.50",
        
        # Navigation Workflow Tests
        "navigate to dashboard page at https://app.example.com username user pass 123",
        "go to settings page on 10.1.1.1",
        "browse to configuration section",
        
        # Form Filling Tests
        "fill form with name John, email john@test.com, age 30",
        "complete registration form at https://signup.com",
        "enter data into contact form",
        
        # Verification Tests
        "verify that page shows 'Welcome User'",
        "check for 'Login Successful' message",
        "validate configuration is saved",
        
        # Invalid BGP ASN Tests
        "create fabric with BGP ASN 23456",  # Reserved
        "setup fabric ASN 99999999999",      # Out of range
    ]
    
    print("🧪 Testing Instruction Analyzer")
    print("=" * 60)
    
    for i, instruction in enumerate(test_instructions, 1):
        print(f"\n{i}. Testing: {instruction}")
        print("-" * 50)
        
        try:
            result = analyzer.analyze_instruction(instruction)
            
            print(f"📋 Workflow Type: {result.workflow_type.value}")
            print(f"📊 Confidence: {result.confidence:.2f}")
            print(f"🔧 Extracted Parameters: {result.extracted_params}")
            
            if result.missing_required_params:
                print(f"❌ Missing Required: {result.missing_required_params}")
            
            if result.validation_errors:
                print(f"⚠️ Validation Errors: {result.validation_errors}")
            
            if result.suggested_defaults:
                print(f"💡 Suggested Defaults: {result.suggested_defaults}")
            
            # Show success/failure
            if result.workflow_type != WorkflowType.UNKNOWN and not result.validation_errors:
                if not result.missing_required_params:
                    print("✅ COMPLETE - Ready for execution")
                else:
                    print("🟡 PARTIAL - Missing required parameters")
            else:
                print("❌ FAILED - Unknown workflow or validation errors")
                
        except Exception as e:
            print(f"💥 ERROR: {e}")
    
    # Test workflow help
    print(f"\n\n📚 Workflow Help Examples")
    print("=" * 60)
    
    for workflow_type in [WorkflowType.CREATE_FABRIC, WorkflowType.LOGIN_ONLY, WorkflowType.MODIFY_FABRIC]:
        help_info = analyzer.get_workflow_help(workflow_type)
        print(f"\n{workflow_type.value.upper()}:")
        print(f"Description: {help_info['description']}")
        print("Parameters:")
        for param in help_info['parameters']:
            required_str = "REQUIRED" if param['required'] else "optional"
            default_str = f" (default: {param.get('default', 'none')})" if 'default' in param else ""
            print(f"  • {param['name']} ({param['type']}) - {required_str}{default_str}")
            print(f"    {param['description']}")

def test_bgp_asn_validation():
    """Test BGP ASN validation specifically"""
    print(f"\n\n🔢 BGP ASN Validation Tests")
    print("=" * 60)
    
    analyzer = InstructionAnalyzer()
    
    test_asns = [
        (1300, "Valid public ASN"),
        (64512, "Valid private ASN (2-byte)"), 
        (65001, "Valid private ASN (2-byte)"),
        (23456, "Reserved ASN - should fail"),
        (99999999999, "Out of range - should fail"),
        (4200000000, "Valid private ASN (4-byte)"),
        (65536, "Valid public ASN"),
        (0, "Invalid - should fail"),
        (4294967295, "Edge case - max value")
    ]
    
    for asn_value, description in test_asns:
        error = analyzer._validate_bgp_asn(asn_value)
        if error:
            print(f"❌ ASN {asn_value}: {error}")
        else:
            print(f"✅ ASN {asn_value}: {description}")

if __name__ == "__main__":
    test_instruction_analyzer()
    test_bgp_asn_validation()
