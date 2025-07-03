# src/workflows/enhanced_workflow_manager.py
# Read-only file system safe version

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

logger = logging.getLogger("e2e_testing_mcp")

class WorkflowExecutionMode(Enum):
    """Enhanced workflow execution modes"""
    TEMPLATE_ONLY = "template_only"
    AI_ENHANCED = "ai_enhanced" 
    AI_DYNAMIC = "ai_dynamic"
    HYBRID = "hybrid"

@dataclass
class WorkflowTemplate:
    """Enhanced workflow template with DNA Center support"""
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    steps: List[Dict[str, Any]]
    success_criteria: List[str]
    estimated_duration: int
    created_by: str = "system"
    version: str = "1.0"
    failure_recovery: List[Dict[str, Any]] = None

class EnhancedWorkflowManager:
    """Enhanced workflow manager with DNA Center and hybrid AI support - Read-only safe"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        # Don't try to create directories in read-only environments
        self.templates_dir = None  # Force in-memory mode
        
        self.workflow_templates: Dict[str, WorkflowTemplate] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.ai_learning_data: Dict[str, Any] = {}
        
        # Initialize all templates in memory
        try:
            self._initialize_builtin_templates()
            self._initialize_dna_center_templates()
            logger.info("Enhanced workflow manager initialized in read-only safe mode")
        except Exception as e:
            logger.error(f"Failed to initialize workflow manager: {e}")
            raise
    
    def _initialize_dna_center_templates(self):
        """Initialize DNA Center specific workflow templates"""
        
        # Network Site Hierarchy Template (inline definition to avoid file issues)
        network_hierarchy_template = WorkflowTemplate(
            name="network_site_hierarchy",
            description="Navigate to DNA Center's Network Hierarchy page and create organizational structure with Areas and Buildings",
            category="dna_center_design",
            parameters={
                "cluster_ip": {
                    "type": "string", 
                    "required": True, 
                    "description": "DNA Center cluster IP address",
                    "validation": "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$"
                },
                "area_name": {
                    "type": "string", 
                    "required": False, 
                    "default": "SJC",
                    "description": "Name for the Area to be created"
                },
                "building_name": {
                    "type": "string", 
                    "required": False, 
                    "default": "B1",
                    "description": "Name for the Building to be created"
                },
                "address_search": {
                    "type": "string", 
                    "required": False, 
                    "default": "San Jose",
                    "description": "Search term for building address location"
                }
            },
            steps=[
                {
                    "action": "navigate",
                    "target": "https://{cluster_ip}/",
                    "description": "Navigate to DNA Center login page",
                    "timeout": 45000,
                    "expected_result": "DNA Center login page loads"
                },
                {
                    "action": "fill",
                    "target": "username field",
                    "value": "{username}",
                    "description": "Enter DNA Center username",
                    "locator_strategy": "auto",
                    "expected_result": "Username entered"
                },
                {
                    "action": "fill",
                    "target": "password field",
                    "value": "{password}",
                    "description": "Enter DNA Center password",
                    "locator_strategy": "auto",
                    "expected_result": "Password entered"
                },
                {
                    "action": "click",
                    "target": "login button",
                    "description": "Click DNA Center login button",
                    "locator_strategy": "auto",
                    "expected_result": "Login submitted"
                },
                {
                    "action": "wait",
                    "target": "dashboard",
                    "value": "10",
                    "description": "Wait for DNA Center dashboard to load",
                    "expected_result": "Dashboard loaded"
                },
                {
                    "action": "click",
                    "target": "Design menu",
                    "description": "Click on Design in the main navigation menu",
                    "locator_strategy": "auto",
                    "expected_result": "Design dropdown menu appears"
                },
                {
                    "action": "wait",
                    "target": "design dropdown",
                    "value": "3",
                    "description": "Wait for Design dropdown menu to expand",
                    "expected_result": "Design dropdown options visible"
                },
                {
                    "action": "click",
                    "target": "Network Hierarchy",
                    "description": "Click Network Hierarchy from Design dropdown",
                    "locator_strategy": "auto",
                    "expected_result": "Navigate to Network Hierarchy page"
                },
                {
                    "action": "wait",
                    "target": "hierarchy page",
                    "value": "5",
                    "description": "Wait for Network Hierarchy page to load",
                    "expected_result": "Network Hierarchy page loaded"
                },
                {
                    "action": "verify",
                    "target": "hierarchy page loaded",
                    "description": "Verify Network Hierarchy page loads successfully",
                    "expected_result": "Global hierarchy visible"
                },
                {
                    "action": "click",
                    "target": "Global expand",
                    "description": "Expand Global hierarchy",
                    "locator_strategy": "auto",
                    "expected_result": "Global hierarchy expanded"
                },
                {
                    "action": "click",
                    "target": "Global three-dots menu",
                    "description": "Click three-dots menu for Global",
                    "locator_strategy": "auto",
                    "expected_result": "Context menu appears"
                },
                {
                    "action": "click",
                    "target": "Add Area",
                    "description": "Click Add Area option",
                    "locator_strategy": "auto",
                    "expected_result": "Add Area modal appears"
                },
                {
                    "action": "fill",
                    "target": "Area Name field",
                    "value": "{area_name}",
                    "description": "Fill Area Name field",
                    "locator_strategy": "auto",
                    "expected_result": "Area name entered"
                },
                {
                    "action": "click",
                    "target": "Add area button",
                    "description": "Click Add button to create area",
                    "locator_strategy": "auto",
                    "expected_result": "Area created successfully"
                },
                {
                    "action": "wait",
                    "target": "area creation",
                    "value": "5",
                    "description": "Wait for area creation to complete",
                    "expected_result": "Area added successfully message"
                },
                {
                    "action": "click",
                    "target": "Area three-dots menu",
                    "description": "Click three-dots menu for created area",
                    "locator_strategy": "auto",
                    "expected_result": "Area context menu appears"
                },
                {
                    "action": "click",
                    "target": "Add Building",
                    "description": "Click Add Building option",
                    "locator_strategy": "auto",
                    "expected_result": "Add Building modal appears"
                },
                {
                    "action": "fill",
                    "target": "Building Name field",
                    "value": "{building_name}",
                    "description": "Fill Building Name field",
                    "locator_strategy": "auto",
                    "expected_result": "Building name entered"
                },
                {
                    "action": "fill",
                    "target": "Address search field",
                    "value": "{address_search}",
                    "description": "Enter address search term",
                    "locator_strategy": "auto",
                    "expected_result": "Address search results appear"
                },
                {
                    "action": "wait",
                    "target": "address results",
                    "value": "3",
                    "description": "Wait for address search results",
                    "expected_result": "Address options visible"
                },
                {
                    "action": "click",
                    "target": "first address option",
                    "description": "Select first address option",
                    "locator_strategy": "auto",
                    "expected_result": "Address selected"
                },
                {
                    "action": "click",
                    "target": "Add building button",
                    "description": "Click Add button to create building",
                    "locator_strategy": "auto",
                    "expected_result": "Building created successfully"
                },
                {
                    "action": "wait",
                    "target": "building creation",
                    "value": "10",
                    "description": "Wait for building creation to complete",
                    "expected_result": "Site added successfully message"
                },
                {
                    "action": "verify",
                    "target": "complete hierarchy",
                    "description": "Verify complete site hierarchy creation",
                    "expected_result": "Global/{area_name}/{building_name} hierarchy visible"
                }
            ],
            success_criteria=[
                "Successfully navigate to Network Hierarchy page",
                "Area created with success message",
                "Building created with success message", 
                "Complete hierarchy visible",
                "All modals close automatically"
            ],
            estimated_duration=120,
            created_by="dna_center_specialist",
            version="1.0"
        )
        
        self.workflow_templates["network_site_hierarchy"] = network_hierarchy_template
        
        logger.info("Initialized DNA Center workflow templates")
    
    def _initialize_builtin_templates(self):
        """Initialize built-in workflow templates"""
        
        # Enhanced Login Template with DNA Center support
        login_template = WorkflowTemplate(
            name="dna_center_login",
            description="Login to DNA Center with SSL bypass and session management", 
            category="authentication",
            parameters={
                "cluster_ip": {
                    "type": "string", 
                    "required": True, 
                    "description": "DNA Center cluster IP address",
                    "validation": "^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$"
                },
                "username": {
                    "type": "string", 
                    "required": True, 
                    "description": "DNA Center username"
                },
                "password": {
                    "type": "string", 
                    "required": True, 
                    "description": "DNA Center password"
                }
            },
            steps=[
                {
                    "action": "navigate",
                    "target": "https://{cluster_ip}/",
                    "description": "Navigate to DNA Center login page",
                    "timeout": 45000,
                    "expected_result": "DNA Center login page loads"
                },
                {
                    "action": "wait",
                    "target": "page_load",
                    "value": "5",
                    "description": "Wait for login page to fully load",
                    "expected_result": "Login form visible"
                },
                {
                    "action": "fill",
                    "target": "username field",
                    "value": "{username}",
                    "description": "Enter DNA Center username",
                    "locator_strategy": "auto",
                    "expected_result": "Username entered"
                },
                {
                    "action": "fill",
                    "target": "password field",
                    "value": "{password}",
                    "description": "Enter DNA Center password",
                    "locator_strategy": "auto",
                    "expected_result": "Password entered"
                },
                {
                    "action": "click",
                    "target": "login button",
                    "description": "Click DNA Center login button",
                    "locator_strategy": "auto",
                    "expected_result": "Login submitted"
                },
                {
                    "action": "wait",
                    "target": "authentication",
                    "value": "15",
                    "description": "Wait for authentication and dashboard load",
                    "expected_result": "DNA Center dashboard loads"
                },
                {
                    "action": "verify",
                    "target": "successful login",
                    "description": "Verify successful login to DNA Center",
                    "expected_result": "DNA Center home page visible"
                }
            ],
            success_criteria=[
                "Successfully navigate to DNA Center login page",
                "Username and password entered without errors",
                "Login authentication successful",
                "DNA Center dashboard/home page loads"
            ],
            estimated_duration=30
        )
        
        self.workflow_templates["dna_center_login"] = login_template
        
        logger.info("Initialized built-in templates with DNA Center support")
    
    def detect_workflow_from_instruction(self, instruction: str) -> Tuple[Optional[str], float, Dict[str, Any]]:
        """Enhanced workflow detection with DNA Center intelligence"""
        instruction_lower = instruction.lower()
        workflow_scores = {}
        
        # DNA Center specific detection
        if any(term in instruction_lower for term in ["network hierarchy", "site hierarchy", "add area", "add building"]):
            workflow_scores["network_site_hierarchy"] = 0.95
        
        # Login detection (enhanced)
        elif any(term in instruction_lower for term in ["login", "log in", "sign in", "authenticate", "dna center"]):
            workflow_scores["dna_center_login"] = 0.9
        
        # Find best match
        if workflow_scores:
            best_workflow = max(workflow_scores, key=workflow_scores.get)
            confidence = workflow_scores[best_workflow]
            
            # Extract parameters from instruction
            parameters = self._extract_parameters_from_instruction(instruction, best_workflow)
            
            return best_workflow, confidence, parameters
        
        return None, 0.0, {}
    
    def _extract_parameters_from_instruction(self, instruction: str, workflow_name: str) -> Dict[str, Any]:
        """Enhanced parameter extraction with DNA Center specifics"""
        parameters = {}
        instruction_lower = instruction.lower()
        
        # DNA Center IP extraction
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, instruction)
        if ips:
            parameters["cluster_ip"] = ips[0]
        
        # Area name extraction
        area_patterns = [
            r'area[:\s]+["\']([^"\']+)["\']',
            r'area[:\s]+(\w+)',
            r'["\']([A-Z]{2,4})["\']',
        ]
        for pattern in area_patterns:
            matches = re.findall(pattern, instruction, re.IGNORECASE)
            if matches:
                parameters["area_name"] = matches[0]
                break
        
        # Building name extraction  
        building_patterns = [
            r'building[:\s]+["\']([^"\']+)["\']',
            r'building[:\s]+(\w+)',
            r'\b([B]\d+)\b',
        ]
        for pattern in building_patterns:
            matches = re.findall(pattern, instruction, re.IGNORECASE)
            if matches:
                parameters["building_name"] = matches[0]
                break
        
        # Address/location extraction
        location_keywords = ["san jose", "california", "new york", "texas", "florida"]
        for location in location_keywords:
            if location in instruction_lower:
                parameters["address_search"] = location.title()
                break
        
        # Username extraction
        username_patterns = [
            r'username[:\s]+["\']([^"\']+)["\']',
            r'user[:\s]+["\']([^"\']+)["\']',
            r'login[:\s]+["\']([^"\']+)["\']'
        ]
        for pattern in username_patterns:
            matches = re.findall(pattern, instruction, re.IGNORECASE)
            if matches:
                parameters["username"] = matches[0]
                break
        
        return parameters
    
    def generate_workflow_from_template(self, template_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executable workflow from template with enhanced DNA Center support"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Validate required parameters
        missing_params = []
        for param_name, param_config in template.parameters.items():
            if param_config.get("required", False) and param_name not in parameters:
                missing_params.append(param_name)
        
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        
        # Apply default values and validate
        final_parameters = {}
        for param_name, param_config in template.parameters.items():
            if param_name in parameters:
                value = parameters[param_name]
                # Validate parameter if validation pattern exists
                if "validation" in param_config:
                    if not re.match(param_config["validation"], str(value)):
                        raise ValueError(f"Parameter '{param_name}' does not match required format")
                final_parameters[param_name] = value
            elif "default" in param_config:
                final_parameters[param_name] = param_config["default"]
        
        # Generate steps with parameter substitution
        generated_steps = []
        for step in template.steps:
            generated_step = step.copy()
            
            # Substitute parameters in all string fields
            for key in ["target", "value", "description"]:
                if key in generated_step and generated_step[key]:
                    text = generated_step[key]
                    for param_name, param_value in final_parameters.items():
                        text = text.replace(f"{{{param_name}}}", str(param_value))
                    generated_step[key] = text
            
            generated_steps.append(generated_step)
        
        return {
            "test_name": f"{template.description}",
            "description": f"Generated from template: {template.name}",
            "template_name": template_name,
            "template_version": template.version,
            "parameters_used": final_parameters,
            "steps": generated_steps,
            "success_criteria": template.success_criteria,
            "estimated_duration": template.estimated_duration,
            "execution_mode": "template_based"
        }
    
    def get_template(self, template_name: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by name"""
        return self.workflow_templates.get(template_name)
    
    def list_templates(self) -> Dict[str, WorkflowTemplate]:
        """List all available workflow templates"""
        return self.workflow_templates.copy()
    
    def list_templates_by_category(self, category: str) -> Dict[str, WorkflowTemplate]:
        """List templates filtered by category"""
        return {
            name: template for name, template in self.workflow_templates.items() 
            if template.category == category
        }
    
    def save_template(self, template: WorkflowTemplate):
        """Save a workflow template (in-memory only for read-only environments)"""
        self.workflow_templates[template.name] = template
        logger.info(f"Saved workflow template in memory: {template.name}")
    
    def get_workflow_suggestions(self, instruction: str) -> List[Dict[str, Any]]:
        """Get workflow suggestions based on instruction analysis"""
        suggestions = []
        
        # Detect possible workflows
        detected_workflow, confidence, parameters = self.detect_workflow_from_instruction(instruction)
        
        if detected_workflow:
            template = self.get_template(detected_workflow)
            if template:
                suggestions.append({
                    "template_name": detected_workflow,
                    "confidence": confidence,
                    "description": template.description,
                    "estimated_duration": template.estimated_duration,
                    "extracted_parameters": parameters,
                    "missing_parameters": [
                        param for param, config in template.parameters.items()
                        if config.get("required", False) and param not in parameters
                    ]
                })
        
        # Add similar workflows
        for name, template in self.workflow_templates.items():
            if name != detected_workflow:
                similarity = self._calculate_similarity(instruction, template.description)
                if similarity > 0.3:
                    suggestions.append({
                        "template_name": name,
                        "confidence": similarity,
                        "description": template.description,
                        "estimated_duration": template.estimated_duration,
                        "extracted_parameters": {},
                        "missing_parameters": []
                    })
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:5]
    
    def _calculate_similarity(self, instruction: str, template_description: str) -> float:
        """Calculate similarity between instruction and template description"""
        instruction_words = set(instruction.lower().split())
        template_words = set(template_description.lower().split())
        
        if not instruction_words or not template_words:
            return 0.0
        
        intersection = instruction_words.intersection(template_words)
        union = instruction_words.union(template_words)
        
        return len(intersection) / len(union) if union else 0.0