# src/workflows/workflow_step_definitions.py

from typing import Dict, List
from src.core.instruction_analyzer import WorkflowType

class WorkflowStepDefinitions:
    """
    Contains detailed English workflow descriptions that will be passed to Azure OpenAI
    to generate specific Playwright automation steps.
    
    These are high-level workflow descriptions, not specific selectors.
    Azure OpenAI will convert these into detailed Playwright steps.
    """
    
    @classmethod
    def get_workflow_definition(cls, workflow_type: WorkflowType) -> Dict[str, any]:
        """Get workflow definition for Azure OpenAI context"""
        
        definitions = {
            WorkflowType.LOGIN_ONLY: cls._get_login_only_definition(),
            WorkflowType.GET_FABRIC: cls._get_fabric_definition(),
            WorkflowType.CREATE_FABRIC: cls._create_fabric_definition(),
            WorkflowType.MODIFY_FABRIC: cls._modify_fabric_definition(),
            WorkflowType.DELETE_FABRIC: cls._delete_fabric_definition(),
            WorkflowType.NAVIGATION: cls._get_navigation_definition(),
            WorkflowType.FORM_FILLING: cls._get_form_filling_definition(),
            WorkflowType.VERIFICATION: cls._get_verification_definition(),
            WorkflowType.NETWORK_SITE_HIERARCHY: cls._get_network_site_hierarchy_definition(),
            WorkflowType.INVENTORY_PROVISION: cls._get_inventory_provision_definition(),
        }
        
        return definitions.get(workflow_type, cls._get_default_definition())
    
    @classmethod
    def _get_login_only_definition(cls) -> Dict[str, any]:
        """Login only workflow definition"""
        return {
            "workflow_name": "Login Only",
            "description": "Authenticate to the server and verify login success",
            "timeout_per_step": 300000,  # 5 minutes per step
            "retry_attempts": 3,
            "english_steps": [
                "Navigate to the login page at the provided URL",
                "Wait for the login page to fully load and become interactive",
                "Locate the username input field (look for input field with placeholder 'username', 'user', 'email' or similar)",
                "Clear the username field and enter the provided username",
                "Locate the password input field (look for input field with type 'password' or placeholder 'password')",
                "Clear the password field and enter the provided password",
                "Find the login button (look for button with text 'Login', 'Sign In', 'Submit', or similar)",
                "Click the login button to submit the form",
                "Wait for login to complete and page to redirect or refresh",
                "Verify successful login by checking for welcome message, dashboard, or absence of login form",
                "Take a screenshot to confirm successful login state"
            ],
            "success_criteria": [
                "Page successfully loads without SSL errors",
                "Username and password fields are found and filled",
                "Login button is clickable and responds",
                "Login attempt results in successful authentication", 
                "User is redirected to authenticated area (dashboard, home page, etc.)",
                "No error messages about invalid credentials"
            ],
            "common_selectors_guidance": [
                "Username field: input[type='text'], input[name*='user'], input[placeholder*='user'], #username, #email",
                "Password field: input[type='password'], input[name*='pass'], #password",
                "Login button: button[type='submit'], input[type='submit'], button:contains('Login'), button:contains('Sign')"
            ],
            "error_handling": [
                "If SSL certificate error appears, look for 'Advanced' or 'Proceed' buttons to bypass",
                "If CAPTCHA appears, stop execution and report manual intervention needed",
                "If 'Invalid credentials' error appears, verify parameters and retry with same credentials",
                "If page doesn't load within timeout, refresh and retry",
                "If elements are not found, wait longer and try alternative selectors"
            ]
        }
    
    @classmethod
    def _get_network_site_hierarchy_definition(cls) -> Dict[str, any]:
        """Network site hierarchy workflow definition"""
        return {
            "workflow_name": "Network Site Hierarchy Management",
            "description": "Login to network management system and create/manage site hierarchy with area and building information",
            "timeout_per_step": 300000,  # 5 minutes per step
            "retry_attempts": 3,
            "english_steps": [
                # Login steps
                "if not logged in Navigate to the login page at the provided URL",
                "Wait for the login page to fully load and become interactive",
                "Locate the username input field (look for input field with placeholder 'username', 'user', 'email' or similar)",
                "Clear the username field and enter the provided username",
                "Locate the password input field (look for input field with type 'password' or placeholder 'password')",
                "Clear the password field and enter the provided password",
                "Find the login button (look for button with text 'Login', 'Sign In', 'Submit', or similar)",
                "Click the login button to submit the form",
                "Wait for login to complete and page to redirect or refresh",
                "Verify successful login by checking for welcome message, dashboard, or absence of login form",
                "Take a screenshot to confirm successful login state"
                
                # Navigate to site hierarchy management
                "Look for the main navigation menu (usually at top or left side)",
                "Find and click on 'Design' then on 'Network Hierarchy', wait till the page loads completely",
                "click on the arrow dropdown next to Global, Look for any value in dropdown or any child value for Global",
                "if no value present, hover over to the 3 dots icon kind of at the end of the Global and select or click on Add Area",
                "then Add Area pop up will be there and enter the Area name provided and click on Add button to submit"
                "Wait for the Area to be added successfully"
                "then Navigate to the dropdown of newly added Area and hover over the 3 dots icon kind of at the end of Area added and click on Add building",
                "then Add building pop up will be there and enter the building name provided and click on Add button to submit"
                "Wait for the building to be added successfully"
                
                # Submit and verify
                "Look for success confirmation message, progress completion, or site appearing in hierarchy",
                "Verify the site hierarchy was created by checking the sites list or hierarchy view",
                "Take a screenshot of the successful site hierarchy creation confirmation"
            ],
            "success_criteria": [
                "Successfully login to the network management system",
                "Navigate to site hierarchy management section without errors",
                "Site creation form loads and accepts all required parameters",
                "Area name and building name are accepted and validated",
                "Site hierarchy creation process completes successfully",
                "Confirmation message or site appears in hierarchy interface",
                "No error messages during the entire process"
            ],
            "common_selectors_guidance": [
                "Sites menu: a:contains('Site'), button:contains('Site'), [data-*='site'], nav a[href*='site']",
                "Hierarchy menu: a:contains('Hierarchy'), button:contains('Hierarchy'), [data-*='hierarchy']",
                "Create button: button:contains('Create'), button:contains('New'), button:contains('Add'), .btn-primary",
                "Area field: input[name*='area'], input[placeholder*='area'], #area-name, #area",
                "Building field: input[name*='building'], input[placeholder*='building'], #building-name, #building",
                "Submit button: button[type='submit'], button:contains('Create'), button:contains('Save'), .btn-success"
            ],
            "error_handling": [
                "If area name validation fails, verify the area name format and retry",
                "If building name validation fails, check for special characters and retry",
                "If site hierarchy creation times out, wait longer and check for background processing",
                "If 'site already exists' error, modify area or building name and retry",
                "If navigation fails, look for alternative menu paths or refresh page",
                "If form submission fails, check for required fields and fill missing data"
            ],
            "parameters": {
                "url": "Network management system URL",
                "username": "Login username",
                "password": "Login password",
                "area_name": "Area name for site hierarchy (required)",
                "building_name": "Building name for site hierarchy (required)",
                "site_type": "Type of site (optional, defaults to 'office')",
                "floor_count": "Number of floors in building (optional, defaults to 1)"
            }
        }
    
    @classmethod
    def _get_inventory_provision_definition(cls) -> Dict[str, any]:
        """Inventory provision workflow definition"""
        return {
            "workflow_name": "Inventory Provision",
            "description": "Login to network management system and provision network devices from inventory",
            "timeout_per_step": 300000,  # 5 minutes per step
            "retry_attempts": 3,
            "english_steps": [
                # Login steps
                "if not logged in Navigate to the login page at the provided URL",
                "Wait for the login page to fully load and become interactive",
                "Locate the username input field (look for input field with placeholder 'username', 'user', 'email' or similar)",
                "Clear the username field and enter the provided username",
                "Locate the password input field (look for input field with type 'password' or placeholder 'password')",
                "Clear the password field and enter the provided password",
                "Find the login button (look for button with text 'Login', 'Sign In', 'Submit', or similar)",
                "Click the login button to submit the form",
                "Wait for login to complete and page to redirect or refresh",
                "Verify successful login by checking for welcome message, dashboard, or absence of login form",
                "Take a screenshot to confirm successful login state"
                
                # Navigate to inventory & provision devices
                "Look for the main navigation menu (usually at top or left side)",
                "Find and click on 'Provision' or similar menu item",
                "then click on Inventory to navigate to the inventory management page",
                "Wait for the inventory management page to load completely",
                "select all the checkboxes of all devices then hover over the Actions button or option to open the dropdown",
                "from the dropdown select 'Provision' or similar option and then click on Assign device to Site",
                "Wait for the Assign device to Site interface to load completely",
                "look for Assign all option and click on it and wait for it to load the site hierarchy"
                "select the building name from the site hierarchy and click on Save",
                "come back to Assign device to Site interface and click on Next button",
                "click on Next button again to proceed to the next step",
                "if whats New pop up is shown, then select Do not show me this again and then click on Close button and then click Next again",
                "then you should reach the div.device-assign-site where you should see 3 options Now, later, Preview & Deploy Recommended, select Preview & Deploy Recommended",
                "click on preview button then Wait for the config preview interface to load completely",
                "then you should see Pending Operations and Device Compliance check showing as success",
                "click the Next button on this page, wait till it loads and the Deploy button is completely enabled to click on it take a screenshot",
                "then click on deploy button and then click on Submit button to submit the workflow and wait for it to load and it will take you to the Inventory page again",
                "then keep refreshing the devices till the Provisioning Status as Success",
                "Take a screenshot of the successful inventory provision confirmation",
                "select all the checkboxes of all devices again and then hover over the Actions button or option to open the dropdown",
                "from the dropdown select 'Provision' or similar option and then click on Provision device option",
                "wait for Advance Configuration page to load and click on Next button",
                "then wait for Summary page to load and then click on Next button",
                "then wait for Provision Device page to load with options 'Now', 'Later', 'Preview and Deploy (Recommended) and select Now option",
                "then click on Apply button and wait for Provision Device page to load",
                "check all the 3 checks are Success and then click on Next button and wait for it to load completely",
                "wait for deploy button to enable and then click on it",
                "then click on Submit button to submit the workflow and wait for it to load and it will take you to the Inventory page again",
                "then keep refreshing the devices till the Provisioning Status as Success",
                "Take a screenshot of the successful inventory provision confirmation"

            ],
            "success_criteria": [
                "Successfully login to the network management system",
                "Navigate to inventory provision section without errors",
                "Provisioning interface loads and is accessible",
                "Provisioning process starts successfully",
                "Devices are provisioned without critical errors",
                "Provisioning completion is confirmed",
                "No critical error messages during the process"
            ],
            "common_selectors_guidance": [
                "Inventory menu: a:contains('Inventory'), button:contains('Inventory'), [data-*='inventory'], nav a[href*='inventory']",
                "Provision menu: a:contains('Provision'), button:contains('Provision'), [data-*='provision']",
                "Start button: button:contains('Start'), button:contains('Provision'), button:contains('Execute'), .btn-primary",
                "Progress indicator: .progress, .progress-bar, [data-*='progress'], .spinner",
                "Status message: .status, .alert, .message, [data-*='status']",
                "Device list: .device-list, .inventory-list, table[data-*='device'], .device-table"
            ],
            "error_handling": [
                "If provisioning fails to start, check device availability and network connectivity",
                "If provisioning times out, wait longer as device provisioning can take extended time",
                "If some devices fail to provision, check individual device status and retry failed devices",
                "If inventory is empty, verify devices are properly added to inventory first",
                "If provisioning interface is not accessible, check user permissions and role access",
                "If provisioning process hangs, monitor system resources and network connectivity"
            ],
            "parameters": {
                "url": "Network management system URL",
                "username": "Login username",
                "password": "Login password",
                "provision_type": "Provisioning type (optional, defaults to 'auto')",
                "device_filter": "Device filter criteria (optional, defaults to 'all')"
            }
        }
    
    @classmethod  
    def _get_fabric_definition(cls) -> Dict[str, any]:
        """get fabric workflow definition"""
        return {
            "workflow_name": "get Network Fabric", 
            "description": "Login and get an existing network fabric",
            "timeout_per_step": 300000,
            "retry_attempts": 3,
            "english_steps": [
                # Login steps
                "if not logged in Navigate to the login page at the provided URL",
                "Wait for the login page to fully load and become interactive",
                "Locate the username input field (look for input field with placeholder 'username', 'user', 'email' or similar)",
                "Clear the username field and enter the provided username",
                "Locate the password input field (look for input field with type 'password' or placeholder 'password')",
                "Clear the password field and enter the provided password",
                "Find the login button (look for button with text 'Login', 'Sign In', 'Submit', or similar)",
                "Click the login button to submit the form",
                "Wait for login to complete and page to redirect or refresh",
                "Verify successful login by checking for welcome message, dashboard, or absence of login form",
                "Take a screenshot to confirm successful login state"
                
                # Navigate and get
                "Look for the main navigation menu (usually at top or left side)",
                "Find and click on 'Provision' or similar menu item",
                "then click on Fabric Sites under SDA Access to navigate to fabric dashoard page",
                "Wait for the page to load completely",
                "look for the heading 'Fabric Sites' and under that heading look for 'SUMMARY' and under that look at the count above Fabric Sites text",
                "take a screenshot, then go ahead and click on the count above Fabric Sites text",
                "it will navigate you to summarised Fabric Sites page there you should see a table with no footer",
                "in the table look for column header name with Fabric Site text",
                "under that column you should see the Fabric Name if that matches with provided fabric Name by user",
                "then take the screenshot"
                "Confirm Fabric exists and was found successfully"
            ],
            "success_criteria": [
                "Target fabric is found in the page",
                "Fabric Sites count is 1",
                "get process completes successfully", 
                "Fabric Name is present on the page",
                "No errors during deletion process"
            ]
        }
    
    @classmethod
    def _create_fabric_definition(cls) -> Dict[str, any]:
        """Create fabric workflow definition"""
        return {
            "workflow_name": "Create Network Fabric",
            "description": "Login to network management system and create a new network fabric with specified parameters",
            "timeout_per_step": 300000,  # 5 minutes per step
            "retry_attempts": 3,
            "english_steps": [
                # Login steps
                "if not logged in Navigate to the login page at the provided URL",
                "Wait for the login page to fully load and become interactive",
                "Locate the username input field (look for input field with placeholder 'username', 'user', 'email' or similar)",
                "Clear the username field and enter the provided username",
                "Locate the password input field (look for input field with type 'password' or placeholder 'password')",
                "Clear the password field and enter the provided password",
                "Find the login button (look for button with text 'Login', 'Sign In', 'Submit', or similar)",
                "Click the login button to submit the form",
                "Wait for login to complete and page to redirect or refresh",
                "Verify successful login by checking for welcome message, dashboard, or absence of login form",
                "Take a screenshot to confirm successful login state"
                
                # Navigate to fabric creation
                "Look for the main navigation menu (usually at top or left side)",
                "Find and click on 'Provision' menu item",
                "then in SD Acccess click Zero Trust Overview and wait for it to load completely",
                "look for Network Segmentation Protocol and click on BGP EVPN toggle to enable it",
                "go to bottom of the page and select Start my journey with creation of network fabric option and click on Start My Journey ",
                "Modify Journey Map would pop up then click on Confirm and wait for it to load completely",
                "once Zero Trust Overview page loads again, check if BGP EVPN is shown with green tick success icon",
                "Find and click on 'Provision' menu item",
                "then in SD Access click on 'Fabric Sites' to navigate to the Create fabric Page",
                "click on Create Fabric Sites and Device Groups button to open the Create Fabric Site popup",
                "click on Lets Do it button to create the fabric",
                "select building from Hierarchy option and click Save and Next"
                "Wait for the Manage Device Groups page to load completely then click Save and Next",
                "in the Assign Devices to Device Groups page select on first device in the list by clicking on the checkbox",
                "then click on Assign Device group button and Search for the border and select it and then click on Save",
                "select on second device in the list by clicking on the checkbox",
                "then click on Assign Device group button and Search for the leaf and select it and then click on Save",
                "in the Assign Devices to Device Groups page select on third device in the list by clicking on the checkbox",
                "then click on Assign Device group button and Search for the Spine and select it and then click on Save",
                "once all are assigned then click on Save and Next",
                "Wait for the Specify Fabric Site Settings page to load completely",
                "then populate the fields in fabric attributes like BGP ASN with user provided or deafult",
                "Look for 'BGP ASN', 'ASN', 'Autonomous System Number', or similar field",
                "Enter the provided BGP ASN number in the ASN field",
                "If pools option exists and pools parameter is true, in the fabric Resource Pools section click on pool dropdown and select the first pool available for IPV4 and IPV6",
                "If there are additional required fields, fill them with if user has provided values or else leave them as it is with auto populated values by UI",
                "once the required fields are filled click on Next button",
                "wait for Summary page to load completely and take a screenshot",
                "click on the Next button"
                "In the provision fabric Site page select Preview and deploy (Recommended) option and then click on Deploy button",
                "In perform Intial checks page after it loads, check all the check have passed and click on Next button",
                "wait for it to load completely then you should be in Step 3 Preview Configuration page, select first device and wait for it to load completely the Configuration to be deployed and take a screenshot",
                "select the second device and wait for it to load completely the Configuration to be deployed and take a screenshot",
                "select the third device and wait for it to load completely the Configuration to be deployed and take a screenshot",
                "then click on deploy button, then on deploy page click on Submit button",
                "wait for Creating Fabric site loader to finish and take a screenshot when you see 'Done! You have created a Fabric Site'",
                "then click on View All Fabric Sites option on the page and wait for it to load completely",
                "you will land up on Fabric Sites dashboard page, take a screen shot and verify that the fabric site is created successfully"
            ],
            "success_criteria": [
                "Successfully login to the network management system",
                "Navigate to fabric management section without errors",
                "Fabric creation form loads and accepts all required parameters",
                "BGP ASN validation passes (must be valid ASN number)",
                "Fabric creation process completes successfully",
                "Confirmation message or fabric appears in management interface",
                "No error messages during the entire process"
            ],
            "common_selectors_guidance": [
                "Fabric menu: a:contains('Fabric'), button:contains('Fabric'), [data-*='fabric'], nav a[href*='fabric']",
                "Create button: button:contains('Create'), button:contains('New'), button:contains('Add'), .btn-primary",
                "BGP ASN field: input[name*='asn'], input[name*='bgp'], input[placeholder*='ASN'], #bgp-asn",
                "Fabric name: input[name*='name'], input[name*='fabric'], #fabric-name, #name",
                "Submit button: button[type='submit'], button:contains('Create'), button:contains('Save'), .btn-success"
            ],
            "error_handling": [
                "If BGP ASN validation fails, verify the ASN number is in valid range and retry",
                "If fabric creation times out, wait longer and check for background processing",
                "If 'fabric already exists' error, modify fabric name and retry",
                "If navigation fails, look for alternative menu paths or refresh page",
                "If form submission fails, check for required fields and fill missing data"
            ],
            "parameters": {
                "url": "Network management system URL",
                "username": "Login username", 
                "password": "Login password",
                "bgp_asn": "BGP Autonomous System Number (required)",
                "fabric_name": "Name for the new fabric (optional, defaults to 'DefaultFabric')",
                "pools": "Whether to enable pools (optional, defaults to false)",
                "spine_count": "Number of spine switches (optional, defaults to 2)",
                "leaf_count": "Number of leaf switches (optional, defaults to 4)"
            }
        }
    
    @classmethod
    def _modify_fabric_definition(cls) -> Dict[str, any]:
        """Modify fabric workflow definition"""
        return {
            "workflow_name": "Modify Network Fabric",
            "description": "Login and modify an existing network fabric configuration",
            "timeout_per_step": 300000,
            "retry_attempts": 3,
            "english_steps": [
                # Login steps
                "Navigate to the network management system and perform login",
                "Verify successful authentication and dashboard access",
                
                # Navigate to fabric management
                "Navigate to the fabric management section",
                "Wait for the list of existing fabrics to load",
                "Find the fabric with the specified name in the fabrics list",
                "Click on the fabric name or 'Edit' button for the target fabric",
                
                # Modify fabric
                "Wait for the fabric configuration/edit page to load",
                "Review current fabric settings and identify fields to modify",
                "Apply the specified modifications to fabric configuration",
                "Validate all changes before saving",
                "Submit the fabric modifications",
                "Wait for update process to complete",
                "Verify modifications were applied successfully"
            ],
            "success_criteria": [
                "Target fabric is found and accessible",
                "Fabric modification form loads correctly",
                "All specified modifications are applied",
                "Update process completes without errors",
                "Modified configuration is saved and active"
            ]
        }
    
    @classmethod  
    def _delete_fabric_definition(cls) -> Dict[str, any]:
        """Delete fabric workflow definition"""
        return {
            "workflow_name": "Delete Network Fabric", 
            "description": "Login and delete an existing network fabric",
            "timeout_per_step": 300000,
            "retry_attempts": 3,
            "english_steps": [
                # Login steps
                "Navigate to the network management system and perform login",
                "Verify successful authentication and access to dashboard",
                
                # Navigate and delete
                "Navigate to the fabric management section",
                "Wait for the list of existing fabrics to load completely",
                "Locate the fabric with the specified name to delete",
                "Look for delete option (delete button, trash icon, context menu)",
                "Click on delete option for the target fabric",
                "If confirmation dialog appears, confirm the deletion",
                "Wait for deletion process to complete",
                "Verify the fabric no longer appears in the fabrics list",
                "Confirm deletion was successful"
            ],
            "success_criteria": [
                "Target fabric is found in the list",
                "Delete action is available and functional",
                "Deletion process completes successfully", 
                "Fabric is removed from management interface",
                "No errors during deletion process"
            ]
        }
    
    @classmethod
    def _get_navigation_definition(cls) -> Dict[str, any]:
        """Navigation workflow definition"""
        return {
            "workflow_name": "Page Navigation",
            "description": "Navigate to specific pages within the application",
            "timeout_per_step": 300000,
            "retry_attempts": 3,
            "english_steps": [
                "If authentication is required, perform login first",
                "Navigate to the specified target page or section",
                "Wait for the target page to load completely",
                "Verify the correct page loaded by checking page title or content",
                "Take screenshot of final page state"
            ],
            "success_criteria": [
                "Target page loads without errors",
                "Page content matches expected navigation target",
                "All page elements are rendered correctly"
            ]
        }
    
    @classmethod
    def _get_form_filling_definition(cls) -> Dict[str, any]:
        """Form filling workflow definition"""
        return {
            "workflow_name": "Form Filling and Submission",
            "description": "Fill and submit forms with provided data",
            "timeout_per_step": 300000,
            "retry_attempts": 3,
            "english_steps": [
                "If authentication is required, perform login first",
                "Navigate to the page containing the target form",
                "Wait for the form to load completely",
                "Identify all form fields that need to be filled",
                "Fill each form field with the corresponding data from form_data parameter",
                "Validate that all required fields are completed",
                "Submit the form by clicking submit button",
                "Wait for form submission to process",
                "Verify successful submission (success message, redirect, etc.)"
            ],
            "success_criteria": [
                "Form loads and is interactive",
                "All required fields can be filled",
                "Form submits without validation errors",
                "Success confirmation is received"
            ]
        }
    
    @classmethod
    def _get_verification_definition(cls) -> Dict[str, any]:
        """Verification workflow definition"""
        return {
            "workflow_name": "Content Verification",
            "description": "Verify that expected content exists on the page",
            "timeout_per_step": 300000,
            "retry_attempts": 3,
            "english_steps": [
                "If authentication is required, perform login first",
                "Navigate to the target page for verification",
                "Wait for the page to load completely",
                "Search for the expected content on the page",
                "Verify the content exists and is visible",
                "Take screenshot showing the verified content",
                "Report verification results"
            ],
            "success_criteria": [
                "Target page loads successfully",
                "Expected content is found on the page",
                "Content is visible and accessible",
                "Verification completes without errors"
            ]
        }
    
    @classmethod
    def _get_default_definition(cls) -> Dict[str, any]:
        """Default workflow definition for unknown workflows"""
        return {
            "workflow_name": "Generic Workflow",
            "description": "Basic web automation workflow",
            "timeout_per_step": 300000,
            "retry_attempts": 3,
            "english_steps": [
                "Navigate to the target URL",
                "Perform any required authentication",
                "Execute the requested actions based on the instruction",
                "Verify the actions completed successfully"
            ],
            "success_criteria": [
                "Page loads successfully",
                "Requested actions complete without errors",
                "Expected results are achieved"
            ]
        }
    
    @classmethod
    def get_azure_openai_context(cls, workflow_type: WorkflowType, parameters: Dict[str, any]) -> str:
        """
        Generate context string for Azure OpenAI to convert English steps to Playwright steps
        """
        definition = cls.get_workflow_definition(workflow_type)
        
        context = f"""
WORKFLOW CONTEXT FOR PLAYWRIGHT AUTOMATION:

Workflow: {definition['workflow_name']}
Description: {definition['description']}

IMPORTANT CONSTRAINTS:
- Each step timeout: {definition['timeout_per_step']}ms (5 minutes)
- Maximum retry attempts: {definition['retry_attempts']}
- Application may be slow to load, always wait adequately
- Use robust element selection strategies with fallbacks

ENGLISH WORKFLOW STEPS:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(definition['english_steps'])])}

SUCCESS CRITERIA:
{chr(10).join([f"- {criteria}" for criteria in definition['success_criteria']])}

COMMON ELEMENT SELECTORS (use as guidance):
{chr(10).join(definition.get('common_selectors_guidance', []))}

ERROR HANDLING GUIDANCE:
{chr(10).join(definition.get('error_handling', []))}

PARAMETERS PROVIDED:
{chr(10).join([f"- {key}: {value}" for key, value in parameters.items()])}

INSTRUCTIONS:
You are an Advanced level expert in automation and E2E testing for UI and come in top 1% of the world for expertise in playwright testing, automation, coding for all languages. your task is to Convert these English steps into detailed Playwright actions steps with the following JSON structure:
{{
  "test_name": "Brief descriptive name",
  "description": "What this test accomplishes", 
  "steps": [
    {{
      "action": "navigate|click|fill|verify|wait|select|hover",
      "target": "detailed element description",
      "value": "value to enter (for fill actions)",
      "description": "human readable description",
      "locator_strategy": "auto",
      "expected_result": "what should happen",
      "timeout": 300000,
      "retry_count": 3
    }}
  ],
  "prerequisites": ["any setup requirements"],
  "expected_outcome": "overall test success criteria"
}}

Focus on:
1. Robust element identification (try multiple selector strategies)
2. Adequate waiting between steps (minimum 2-3 seconds)
3. Error handling for slow-loading applications
4. Clear validation at each step
5. Detailed descriptions for debugging
"""
        
        return context