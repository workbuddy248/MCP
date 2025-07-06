# src/core/instruction_analyzer.py

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("e2e_testing_mcp")

class WorkflowType(Enum):
    """Supported workflow types"""
    LOGIN_ONLY = "login_only_workflow"           # Just login and stop
    NETWORK_SITE_HIERARCHY = "network_site_hierarchy_workflow"  # Login + Network Site Hierarchy flow
    INVENTORY_PROVISION = "inventory_provision_workflow"        # Login + Inventory Assign & provision workflow
    GET_FABRIC = "get_fabric_workflow"             # Login + Get Fabric
    CREATE_FABRIC = "create_fabric_workflow"     # Login + Create Fabric
    MODIFY_FABRIC = "modify_fabric_workflow"     # Login + Modify Fabric  
    DELETE_FABRIC = "delete_fabric_workflow"     # Login + Delete Fabric
    NAVIGATION = "navigation_workflow"           # Login + Navigate to page
    FORM_FILLING = "form_filling_workflow"       # Login + Fill forms
    VERIFICATION = "verification_workflow"       # Login + Verify content
    UNKNOWN = "unknown_workflow"

class WorkflowComposition(Enum):
    """Workflow composition types"""
    SINGLE_STEP = "single"          # Just one action
    LOGIN_THEN_ACTION = "login+"    # Login first, then action
    MULTI_STEP = "multi"            # Multiple related actions

@dataclass
class WorkflowParameter:
    """Parameter definition for workflow validation"""
    name: str
    required: bool
    param_type: str  # "string", "int", "float", "bool"
    default_value: Any = None
    validation_rule: Optional[str] = None
    description: str = ""

@dataclass
class AnalyzedInstruction:
    """Result of instruction analysis"""
    workflow_type: WorkflowType
    confidence: float
    extracted_params: Dict[str, Any]
    missing_required_params: List[str]
    validation_errors: List[str]
    suggested_defaults: Dict[str, Any]
    raw_instruction: str

class InstructionAnalyzer:
    """Analyzes user instructions to extract workflow type and parameters"""
    
    def __init__(self):
        self.workflow_patterns = self._initialize_workflow_patterns()
        self.workflow_parameters = self._initialize_workflow_parameters()
        
    def _initialize_workflow_patterns(self) -> Dict[WorkflowType, List[str]]:
        """Initialize regex patterns for workflow type detection
        
        These patterns help identify what the user wants to do:
        - LOGIN_ONLY: Just authenticate and stop
        - GET_FABRIC: Login + get network fabric
        - CREATE_FABRIC: Login + create network fabric  
        - MODIFY_FABRIC: Login + modify existing fabric
        - DELETE_FABRIC: Login + delete fabric
        - NAVIGATION: Login + go to specific page
        - FORM_FILLING: Login + fill specific forms
        - VERIFICATION: Login + check something
        """
        return {
            WorkflowType.LOGIN_ONLY: [
                r'\blogin\s+only\b',
                r'\bjust\s+login\b',
                r'\bonly\s+authenticate\b',
                r'\bconnect\s+to\s+server\b',
                r'\baccess\s+server\b'
            ],
            WorkflowType.NETWORK_SITE_HIERARCHY: [
                r'\bnetwork\s+site\s+hierarchy\b',
                r'\bsite\s+hierarchy\b',
                r'\bcreate\s+site\s+hierarchy\b',
                r'\bsetup\s+site\s+hierarchy\b',
                r'\bhierarchy\s+workflow\b',
                r'\bnetwork\s+hierarchy\b',
                r'\bsite\s+management\b',
                r'\btest\s+network\s+site\s+hierarchy\b'
            ],
            WorkflowType.INVENTORY_PROVISION: [
                r'\binventory\s+provision\b',
                r'\bprovision\s+inventory\b',
                r'\binventory\s+workflow\b',
                r'\bprovision\s+devices\b',
                r'\bdevice\s+provisioning\b',
                r'\btest\s+inventory\s+provision\b',
                r'\bprovision\s+network\s+devices\b'
            ],
            WorkflowType.GET_FABRIC: [
                r'\bget\s+fabric\b',
                r'\bfetch\s+fabric\b',
                r'\bpresent\s+fabric\b',
                r'\bfabric\s+exists\b'
            ],
            WorkflowType.CREATE_FABRIC: [
                r'\bcreate\s+fabric\b',
                r'\bfabric\s+workflow\b',
                r'\bsetup\s+fabric\b',
                r'\bnew\s+fabric\b',
                r'\bfabric\s+creation\b',
                r'\bbuild\s+fabric\b',
                r'\btest\s+create\s+fabric\b' 
            ],
            WorkflowType.MODIFY_FABRIC: [
                r'\bmodify\s+fabric\b',
                r'\bupdate\s+fabric\b',
                r'\bchange\s+fabric\b',
                r'\bedit\s+fabric\b',
                r'\bfabric\s+modification\b'
            ],
            WorkflowType.DELETE_FABRIC: [
                r'\bdelete\s+fabric\b',
                r'\bremove\s+fabric\b',
                r'\bdestroy\s+fabric\b',
                r'\bfabric\s+deletion\b'
            ],
            WorkflowType.NAVIGATION: [
                r'\bnavigate\s+to\b',
                r'\bgo\s+to\b',
                r'\bopen\s+page\b',
                r'\bbrowse\s+to\b',
                r'\bvisit\s+page\b'
            ],
            WorkflowType.FORM_FILLING: [
                r'\bfill\s+form\b',
                r'\benter\s+data\b',
                r'\bsubmit\s+form\b',
                r'\bcomplete\s+form\b',
                r'\binput\s+values\b'
            ],
            WorkflowType.VERIFICATION: [
                r'\bverify\b',
                r'\bcheck\b',
                r'\bvalidate\b',
                r'\bconfirm\b',
                r'\btest\s+that\b'
            ]
        }
    
    def _initialize_workflow_parameters(self) -> Dict[WorkflowType, List[WorkflowParameter]]:
        """Initialize parameter definitions for each workflow type
        
        Note: CREATE_FABRIC, MODIFY_FABRIC, DELETE_FABRIC automatically include login
        LOGIN_ONLY is for just authentication without further actions
        """
        return {
            WorkflowType.LOGIN_ONLY: [
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target server URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=True,
                    param_type="string",
                    description="Login username"
                ),
                WorkflowParameter(
                    name="password",
                    required=True,
                    param_type="string",
                    description="Login password"
                )
            ],
            WorkflowType.NETWORK_SITE_HIERARCHY: [
                # Login parameters (required)
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target server URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=True,
                    param_type="string",
                    description="Login username"
                ),
                WorkflowParameter(
                    name="password",
                    required=True,
                    param_type="string",
                    description="Login password"
                ),
                # Site hierarchy parameters
                WorkflowParameter(
                    name="area_name",
                    required=True,
                    param_type="string",
                    description="Area name for site hierarchy"
                ),
                WorkflowParameter(
                    name="building_name",
                    required=True,
                    param_type="string",
                    description="Building name for site hierarchy"
                ),
                # Optional parameters with defaults
                WorkflowParameter(
                    name="site_type",
                    required=False,
                    param_type="string",
                    default_value="office",
                    description="Type of site (office, datacenter, branch)"
                ),
                WorkflowParameter(
                    name="floor_count",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of floors in building"
                )
            ],
            WorkflowType.INVENTORY_PROVISION: [
                # Login parameters (only required parameters)
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target server URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=True,
                    param_type="string",
                    description="Login username"
                ),
                WorkflowParameter(
                    name="password",
                    required=True,
                    param_type="string",
                    description="Login password"
                ),
                # Optional parameters
                WorkflowParameter(
                    name="provision_type",
                    required=False,
                    param_type="string",
                    default_value="auto",
                    description="Provisioning type (auto, manual, template)"
                ),
                WorkflowParameter(
                    name="device_filter",
                    required=False,
                    param_type="string",
                    default_value="all",
                    description="Device filter criteria"
                )
            ],
             WorkflowType.GET_FABRIC: [
                # Login + fabric get parameters
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target server URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=True,
                    param_type="string",
                    description="Login username"
                ),
                WorkflowParameter(
                    name="password",
                    required=True,
                    param_type="string",
                    description="Login password"
                ),
                WorkflowParameter(
                    name="fabric_name",
                    required=True,
                    param_type="string",
                    description="Name of fabric to get"
                )
            ],
            WorkflowType.CREATE_FABRIC: [
                # Login parameters (required for fabric creation)
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target server URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=True,
                    param_type="string",
                    description="Login username"
                ),
                WorkflowParameter(
                    name="password",
                    required=True,
                    param_type="string",
                    description="Login password"
                ),
                # Fabric creation parameters
                WorkflowParameter(
                    name="bgp_asn",
                    required=True,
                    param_type="int",
                    validation_rule="bgp_asn_range",
                    description="BGP ASN number (4096-4294967295 or 0.1-65536.65536, excluding 23456)"
                ),
                WorkflowParameter(
                    name="fabric_name",
                    required=False,
                    param_type="string",
                    default_value="DefaultFabric",
                    description="Name for the fabric"
                ),
                WorkflowParameter(
                    name="pools",
                    required=False,
                    param_type="bool",
                    default_value=False,
                    description="Whether to create pools"
                ),
                WorkflowParameter(
                    name="spine_device_group",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of spine device groups"
                ),
                WorkflowParameter(
                    name="leaf_device_group",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of leaf device groups"
                ),
                WorkflowParameter(
                    name="border_device_group",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of border device groups"
                ),
                WorkflowParameter(
                    name="border_spine_device_group",
                    required=False,
                    param_type="int",
                    default_value=0,
                    description="Number of border + spine device groups"
                ),
                WorkflowParameter(
                    name="spine_devices",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of spine devics"
                ),
                WorkflowParameter(
                    name="leaf_devices",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of leaf devices"
                ),
                WorkflowParameter(
                    name="border_devices",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of border devices"
                ),
                WorkflowParameter(
                    name="border_spine_devices",
                    required=False,
                    param_type="int",
                    default_value=0,
                    description="Number of border + spine devices"
                )                
            ],
            WorkflowType.MODIFY_FABRIC: [
                # Login + fabric modification parameters
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target server URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=True,
                    param_type="string",
                    description="Login username"
                ),
                WorkflowParameter(
                    name="password",
                    required=True,
                    param_type="string",
                    description="Login password"
                ),
                WorkflowParameter(
                    name="fabric_name",
                    required=True,
                    param_type="string",
                    description="Name of fabric to modify"
                ),
                WorkflowParameter(
                    name="modifications",
                    required=True,
                    param_type="dict",
                    description="Modifications to apply"
                ),
                WorkflowParameter(
                    name="spine_device_group",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of spine device groups"
                ),
                WorkflowParameter(
                    name="leaf_device_group",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of leaf device groups"
                ),
                WorkflowParameter(
                    name="border_device_group",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of border device groups"
                ),
                WorkflowParameter(
                    name="border_spine_device_group",
                    required=False,
                    param_type="int",
                    default_value=0,
                    description="Number of border + spine device groups"
                ),
                WorkflowParameter(
                    name="spine_devices",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of spine devics"
                ),
                WorkflowParameter(
                    name="leaf_devices",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of leaf devices"
                ),
                WorkflowParameter(
                    name="border_devices",
                    required=False,
                    param_type="int",
                    default_value=1,
                    description="Number of border devices"
                ),
                WorkflowParameter(
                    name="border_spine_devices",
                    required=False,
                    param_type="int",
                    default_value=0,
                    description="Number of border + spine devices"
                )
            ],
            WorkflowType.DELETE_FABRIC: [
                # Login + fabric deletion parameters
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target server URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=True,
                    param_type="string",
                    description="Login username"
                ),
                WorkflowParameter(
                    name="password",
                    required=True,
                    param_type="string",
                    description="Login password"
                ),
                WorkflowParameter(
                    name="fabric_name",
                    required=True,
                    param_type="string",
                    description="Name of fabric to delete"
                )
            ],
            WorkflowType.NAVIGATION: [
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target URL or page"
                ),
                WorkflowParameter(
                    name="username",
                    required=False,
                    param_type="string",
                    description="Username if login required"
                ),
                WorkflowParameter(
                    name="password",
                    required=False,
                    param_type="string",
                    description="Password if login required"
                ),
                WorkflowParameter(
                    name="target_page",
                    required=False,
                    param_type="string",
                    description="Specific page to navigate to"
                )
            ],
            WorkflowType.FORM_FILLING: [
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target form URL"
                ),
                WorkflowParameter(
                    name="username",
                    required=False,
                    param_type="string",
                    description="Username if login required"
                ),
                WorkflowParameter(
                    name="password",
                    required=False,
                    param_type="string",
                    description="Password if login required"
                ),
                WorkflowParameter(
                    name="form_data",
                    required=True,
                    param_type="dict",
                    description="Form field data"
                )
            ],
            WorkflowType.VERIFICATION: [
                WorkflowParameter(
                    name="url",
                    required=True,
                    param_type="string",
                    description="Target URL to verify"
                ),
                WorkflowParameter(
                    name="username",
                    required=False,
                    param_type="string",
                    description="Username if login required"
                ),
                WorkflowParameter(
                    name="password",
                    required=False,
                    param_type="string",
                    description="Password if login required"
                ),
                WorkflowParameter(
                    name="expected_content",
                    required=True,
                    param_type="string",
                    description="Content to verify"
                )
            ]
        }
    
    def analyze_instruction(self, instruction: str) -> AnalyzedInstruction:
        """Analyze instruction to extract workflow type and parameters"""
        logger.info(f"Analyzing instruction: {instruction[:100]}...")
        
        # Step 1: Detect workflow type
        workflow_type, confidence = self._detect_workflow_type(instruction)
        
        # Step 2: Extract parameters
        extracted_params = self._extract_parameters(instruction, workflow_type)
        
        # Step 3: Validate parameters
        validation_errors, missing_params, suggested_defaults = self._validate_parameters(
            workflow_type, extracted_params
        )
        
        result = AnalyzedInstruction(
            workflow_type=workflow_type,
            confidence=confidence,
            extracted_params=extracted_params,
            missing_required_params=missing_params,
            validation_errors=validation_errors,
            suggested_defaults=suggested_defaults,
            raw_instruction=instruction
        )
        
        logger.info(f"Analysis result: {workflow_type.value} (confidence: {confidence:.2f})")
        return result
    
    def _detect_workflow_type(self, instruction: str) -> Tuple[WorkflowType, float]:
        """Detect workflow type using pattern matching"""
        instruction_lower = instruction.lower()
        scores = {}
        
        for workflow_type, patterns in self.workflow_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, instruction_lower):
                    matches += 1
                    # Weight based on pattern specificity
                    if "fabric" in pattern:
                        score += 0.8  # High weight for fabric-specific patterns
                    elif len(pattern.split()) > 2:
                        score += 0.6  # Medium weight for multi-word patterns
                    else:
                        score += 0.4  # Lower weight for single words
            
            if matches > 0:
                # Normalize score based on number of patterns and matches
                normalized_score = min(score / len(patterns), 1.0)
                scores[workflow_type] = normalized_score
        
        if not scores:
            return WorkflowType.UNKNOWN, 0.0
        
        # Return highest scoring workflow type
        best_workflow = max(scores, key=scores.get)
        best_score = scores[best_workflow]
        
        return best_workflow, best_score
    
    def _extract_parameters(self, instruction: str, workflow_type: WorkflowType) -> Dict[str, Any]:
        """Extract parameters from instruction based on workflow type"""
        params = {}
        
        # Common parameter extraction patterns
        params.update(self._extract_common_params(instruction))
        
        # Workflow-specific parameter extraction
        if workflow_type == WorkflowType.CREATE_FABRIC:
            params.update(self._extract_fabric_params(instruction))
        elif workflow_type == WorkflowType.FORM_FILLING:
            params.update(self._extract_form_params(instruction))
        elif workflow_type == WorkflowType.VERIFICATION:
            params.update(self._extract_verification_params(instruction))
        elif workflow_type == WorkflowType.NETWORK_SITE_HIERARCHY:
            params.update(self._extract_site_hierarchy_params(instruction))
        elif workflow_type == WorkflowType.INVENTORY_PROVISION:
            params.update(self._extract_inventory_provision_params(instruction))
        
        return params
    
    def _extract_common_params(self, instruction: str) -> Dict[str, Any]:
        """Extract common parameters like URL, username, password"""
        params = {}
        
        # URL extraction (IP:port or domain)
        url_patterns = [
            r'(?:https?://)?([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?::[0-9]+)?)',
            r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::[0-9]+)?)',
            r'on\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?::[0-9]+)?)',
            r'at\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(?::[0-9]+)?)'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, instruction)
            if match:
                url = match.group(1)
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                params["url"] = url
                break
        
        # Username extraction
        username_patterns = [
            r'username\s*[-:=]\s*([a-zA-Z0-9_]+)',
            r'user\s*[-:=]\s*([a-zA-Z0-9_]+)',
            r'login\s*[-:=]\s*([a-zA-Z0-9_]+)'
        ]
        
        for pattern in username_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                params["username"] = match.group(1)
                break
        
        # Password extraction
        password_patterns = [
            r'password\s*[-:=]\s*([a-zA-Z0-9_!@#$%^&*]+)',
            r'pass\s*[-:=]\s*([a-zA-Z0-9_!@#$%^&*]+)',
            r'pwd\s*[-:=]\s*([a-zA-Z0-9_!@#$%^&*]+)'
        ]
        
        for pattern in password_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                params["password"] = match.group(1)
                break
        
        return params
    
    def _extract_site_hierarchy_params(self, instruction: str) -> Dict[str, Any]:
        """Extract site hierarchy specific parameters"""
        params = {}
        
        # Area name extraction
        area_patterns = [
            r'area\s+name\s*[-:=]\s*([a-zA-Z0-9_\s-]+)',
            r'area\s*[-:=]\s*([a-zA-Z0-9_\s-]+)',
            r'site\s+area\s*[-:=]\s*([a-zA-Z0-9_\s-]+)'
        ]
        
        for pattern in area_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                area_name = match.group(1).strip()
                # Remove quotes if present
                area_name = area_name.strip('\'"')
                params["area_name"] = area_name
                break
        
        # Building name extraction
        building_patterns = [
            r'building\s+name\s*[-:=]\s*([a-zA-Z0-9_\s-]+)',
            r'building\s*[-:=]\s*([a-zA-Z0-9_\s-]+)',
            r'site\s+building\s*[-:=]\s*([a-zA-Z0-9_\s-]+)'
        ]
        
        for pattern in building_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                building_name = match.group(1).strip()
                # Remove quotes if present
                building_name = building_name.strip('\'"')
                params["building_name"] = building_name
                break
        
        # Site type extraction
        site_type_patterns = [
            r'site\s+type\s*[-:=]\s*([a-zA-Z0-9_-]+)',
            r'type\s*[-:=]\s*([a-zA-Z0-9_-]+)',
            r'(?:office|datacenter|branch|warehouse|retail)',
        ]
        
        for pattern in site_type_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                site_type = match.group(1).strip().lower()
                if site_type in ['office', 'datacenter', 'branch', 'warehouse', 'retail']:
                    params["site_type"] = site_type
                break
        
        # Floor count extraction
        floor_match = re.search(r'([0-9]+)\s+floors?', instruction, re.IGNORECASE)
        if floor_match:
            params["floor_count"] = int(floor_match.group(1))
        
        return params
    
    def _extract_inventory_provision_params(self, instruction: str) -> Dict[str, Any]:
        """Extract inventory provision specific parameters"""
        params = {}
        
        # Provision type extraction
        provision_patterns = [
            r'provision\s+type\s*[-:=]\s*([a-zA-Z0-9_-]+)',
            r'provisioning\s*[-:=]\s*([a-zA-Z0-9_-]+)',
            r'(?:auto|manual|template)\s+provision',
        ]
        
        for pattern in provision_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                provision_type = match.group(1).strip().lower()
                if provision_type in ['auto', 'manual', 'template']:
                    params["provision_type"] = provision_type
                break
        
        # Device filter extraction
        filter_patterns = [
            r'device\s+filter\s*[-:=]\s*([a-zA-Z0-9_\s-]+)',
            r'filter\s*[-:=]\s*([a-zA-Z0-9_\s-]+)',
            r'devices\s*[-:=]\s*([a-zA-Z0-9_\s-]+)'
        ]
        
        for pattern in filter_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                device_filter = match.group(1).strip()
                params["device_filter"] = device_filter
                break
        
        return params
    
    def _extract_fabric_params(self, instruction: str) -> Dict[str, Any]:
        """Extract fabric-specific parameters"""
        params = {}
        
        # BGP ASN extraction
        bgp_patterns = [
            r'BGP\s+ASN\s*[-:=]\s*([0-9]+(?:\.[0-9]+)?)',
            r'ASN\s*[-:=]\s*([0-9]+(?:\.[0-9]+)?)',
            r'autonomous\s+system\s*[-:=]\s*([0-9]+(?:\.[0-9]+)?)'
        ]
        
        for pattern in bgp_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                asn_str = match.group(1)
                try:
                    if '.' in asn_str:
                        # Handle dotted notation (e.g., 65001.1)
                        high, low = map(int, asn_str.split('.'))
                        asn_value = (high << 16) + low
                    else:
                        asn_value = int(asn_str)
                    params["bgp_asn"] = asn_value
                except ValueError:
                    logger.warning(f"Invalid BGP ASN format: {asn_str}")
                break
        
        # Fabric name extraction
        fabric_name_patterns = [
            r'fabric\s+name\s*[-:=]\s*([a-zA-Z0-9_-]+)',
            r'name\s*[-:=]\s*([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in fabric_name_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                params["fabric_name"] = match.group(1)
                break
        
        # Pools detection
        if re.search(r'\bwith\s+pools?\b|\bpools?\b', instruction, re.IGNORECASE):
            params["pools"] = True
        
        # Spine/Leaf count extraction
        spine_match = re.search(r'([0-9]+)\s+spines?', instruction, re.IGNORECASE)
        if spine_match:
            params["spine_count"] = int(spine_match.group(1))
        
        leaf_match = re.search(r'([0-9]+)\s+leafs?', instruction, re.IGNORECASE)
        if leaf_match:
            params["leaf_count"] = int(leaf_match.group(1))
        
        return params
    
    def _extract_form_params(self, instruction: str) -> Dict[str, Any]:
        """Extract form-related parameters"""
        params = {}
        
        # Look for field:value patterns
        field_patterns = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*[-:=]\s*([^,\n]+)'
        matches = re.findall(field_patterns, instruction)
        
        if matches:
            form_data = {}
            for field, value in matches:
                if field.lower() not in ['username', 'password', 'url']:
                    form_data[field.strip()] = value.strip()
            
            if form_data:
                params["form_data"] = form_data
        
        return params
    
    def _extract_verification_params(self, instruction: str) -> Dict[str, Any]:
        """Extract verification-specific parameters"""
        params = {}
        
        # Extract expected content
        content_patterns = [
            r'verify\s+(?:that\s+)?["\']([^"\']+)["\']',
            r'check\s+(?:for\s+)?["\']([^"\']+)["\']',
            r'should\s+(?:show\s+)?["\']([^"\']+)["\']',
            r'contains\s+["\']([^"\']+)["\']'
        ]
        
        for pattern in content_patterns:
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match:
                params["expected_content"] = match.group(1)
                break
        
        return params
    
    def _validate_parameters(self, workflow_type: WorkflowType, params: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """Validate extracted parameters against workflow requirements"""
        validation_errors = []
        missing_params = []
        suggested_defaults = {}
        
        if workflow_type not in self.workflow_parameters:
            return validation_errors, missing_params, suggested_defaults
        
        param_definitions = self.workflow_parameters[workflow_type]
        
        for param_def in param_definitions:
            param_name = param_def.name
            
            if param_def.required and param_name not in params:
                missing_params.append(param_name)
            elif param_name not in params and param_def.default_value is not None:
                suggested_defaults[param_name] = param_def.default_value
            elif param_name in params:
                # Validate parameter value
                validation_error = self._validate_parameter_value(
                    param_name, params[param_name], param_def
                )
                if validation_error:
                    validation_errors.append(validation_error)
        
        return validation_errors, missing_params, suggested_defaults
    
    def _validate_parameter_value(self, param_name: str, value: Any, param_def: WorkflowParameter) -> Optional[str]:
        """Validate a single parameter value"""
        
        # Type validation
        if param_def.param_type == "int" and not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                return f"Parameter '{param_name}' must be an integer, got: {type(value).__name__}"
        
        # BGP ASN validation
        if param_def.validation_rule == "bgp_asn_range":
            return self._validate_bgp_asn(value)
        
        return None
    
    def _validate_bgp_asn(self, asn_value: int) -> Optional[str]:
        """Validate BGP ASN number according to RFC standards"""
        
        # Reserved ASN (23456) - not allowed
        if asn_value == 23456:
            return "BGP ASN 23456 is reserved and not allowed"
        
        # Private ASN ranges (2-byte)
        if 64512 <= asn_value <= 65534:
            return None  # Valid private ASN
        
        # Private ASN ranges (4-byte)
        if 4200000000 <= asn_value <= 4294967294:
            return None  # Valid private ASN
        
        # Public ASN ranges
        if (1 <= asn_value <= 64511) or (65536 <= asn_value <= 4199999999):
            return None  # Valid public ASN
        
        # Check dotted notation range (0.1 to 65536.65536)
        if 1 <= asn_value <= 4294967295:
            # Convert to dotted notation for validation
            high = asn_value >> 16
            low = asn_value & 0xFFFF
            
            if 0 <= high <= 65536 and 1 <= low <= 65536:
                return None  # Valid in dotted notation range
        
        return f"BGP ASN {asn_value} is outside valid ranges. Must be 1-64511, 64512-65534 (private), 65536-4199999999 (public), or 4200000000-4294967294 (private 4-byte)"
    
    def get_workflow_help(self, workflow_type: WorkflowType) -> Dict[str, Any]:
        """Get help information for a specific workflow type"""
        if workflow_type not in self.workflow_parameters:
            return {"error": f"Unknown workflow type: {workflow_type.value}"}
        
        param_definitions = self.workflow_parameters[workflow_type]
        
        help_info = {
            "workflow_type": workflow_type.value,
            "description": f"Parameters for {workflow_type.value}",
            "parameters": []
        }
        
        for param_def in param_definitions:
            param_info = {
                "name": param_def.name,
                "required": param_def.required,
                "type": param_def.param_type,
                "description": param_def.description
            }
            
            if param_def.default_value is not None:
                param_info["default"] = param_def.default_value
            
            if param_def.validation_rule:
                param_info["validation"] = param_def.validation_rule
            
            help_info["parameters"].append(param_info)
        
        return help_info