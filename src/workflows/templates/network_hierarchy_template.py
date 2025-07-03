# src/workflows/templates/network_hierarchy_template.py

from typing import Dict, List, Any
from ..enhanced_workflow_manager import WorkflowTemplate

def get_network_hierarchy_template() -> WorkflowTemplate:
    """DNA Center Network Site Hierarchy workflow template"""
    
    return WorkflowTemplate(
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
            },
            "verify_hierarchy": {
                "type": "boolean", 
                "required": False, 
                "default": True,
                "description": "Whether to verify the complete hierarchy creation"
            }
        },
        steps=[
            {
                "action": "verify_starting_point",
                "target": "DNA Center Home Page",
                "description": "Verify we're starting from DNA Center home page",
                "locator_strategy": "url_contains",
                "expected_result": "On DNA Center home page",
                "timeout": 1800000,
                "verification": {
                    "url_contains": "https://{cluster_ip}/",
                    "page_title_contains": "DNA Center"
                }
            },
            {
                "action": "navigate_design_menu",
                "target": "Design menu",
                "description": "Click on Design in the main navigation menu",
                "locator_strategy": "dna_center_nav",
                "expected_result": "Design dropdown menu appears",
                "timeout": 60000,
                "element_selectors": [
                    "a[href*='design']:has-text('Design')",
                    "button:has-text('Design')",
                    "[data-testid='design-menu']",
                    ".main-nav a:has-text('Design')",
                    "nav [role='menuitem']:has-text('Design')"
                ],
                "post_action_wait": 2000
            },
            {
                "action": "wait_design_dropdown",
                "target": "Design dropdown expansion",
                "value": "3",
                "description": "Wait for Design dropdown menu to fully expand",
                "locator_strategy": "visibility",
                "expected_result": "Design dropdown options visible",
                "verification": {
                    "elements_visible": [
                        "text=Network Hierarchy",
                        "a[href*='networkHierarchy']"
                    ]
                }
            },
            {
                "action": "click_network_hierarchy",
                "target": "Network Hierarchy option",
                "description": "Click Network Hierarchy from Design dropdown options",
                "locator_strategy": "dna_center_menu",
                "expected_result": "Navigate to Network Hierarchy page",
                "timeout": 40000,
                "element_selectors": [
                    "a[href*='networkHierarchy']:has-text('Network Hierarchy')",
                    "text=Network Hierarchy",
                    "[data-testid='network-hierarchy-link']",
                    ".dropdown-item:has-text('Network Hierarchy')"
                ]
            },
            {
                "action": "verify_hierarchy_page",
                "target": "Network Hierarchy page",
                "description": "Verify Network Hierarchy page loads successfully",
                "locator_strategy": "url_and_content",
                "expected_result": "Network Hierarchy page loaded",
                "timeout": 60000,
                "verification": {
                    "url_contains": "/dna/design/networkHierarchy",
                    "elements_present": [
                        "text=Global",
                        ".hierarchy-tree",
                        "[data-testid='hierarchy-container']"
                    ]
                }
            },
            {
                "action": "wait_page_load",
                "target": "hierarchy content",
                "value": "5",
                "description": "Wait for Network Hierarchy page content to fully load",
                "locator_strategy": "content_ready",
                "expected_result": "Page content fully loaded"
            },
            {
                "action": "expand_global_hierarchy",
                "target": "Global hierarchy dropdown",
                "description": "Click dropdown arrow next to Global to expand hierarchy",
                "locator_strategy": "hierarchy_expand",
                "expected_result": "Global hierarchy expanded",
                "timeout": 40000,
                "element_selectors": [
                    ".hierarchy-item:has-text('Global') .expand-arrow",
                    ".tree-node:has-text('Global') .dropdown-toggle",
                    "[data-testid='global-expand']",
                    ".hierarchy-tree .global-node .expand-icon"
                ],
                "fallback_actions": [
                    {"action": "click", "target": "text=Global"}
                ]
            },
            {
                "action": "check_hierarchy_content",
                "target": "hierarchy expansion",
                "description": "Verify hierarchy content is present and accessible",
                "locator_strategy": "visibility_check",
                "expected_result": "Hierarchy content visible or ready for creation",
                "verification": {
                    "check_existing_content": True,
                    "proceed_if_empty": True
                }
            },
            {
                "action": "hover_global_menu",
                "target": "Global panel three-dots menu",
                "description": "Hover over 3-dots menu at end of Global panel",
                "locator_strategy": "context_menu",
                "expected_result": "Context menu options become visible",
                "timeout": 60000,
                "element_selectors": [
                    ".hierarchy-item:has-text('Global') .three-dots-menu",
                    ".tree-node:has-text('Global') .context-menu-trigger",
                    "[data-testid='global-context-menu']",
                    ".global-node .more-options"
                ]
            },
            {
                "action": "click_add_area",
                "target": "Add Area option",
                "description": "Click Add Area option from context menu",
                "locator_strategy": "context_menu_item",
                "expected_result": "Add Area modal popup appears",
                "timeout": 60000,
                "element_selectors": [
                    "text=Add Area",
                    ".context-menu-item:has-text('Add Area')",
                    "[data-testid='add-area-option']",
                    ".dropdown-item:has-text('Add Area')"
                ]
            },
            {
                "action": "wait_add_area_modal",
                "target": "Add Area modal",
                "value": "3",
                "description": "Wait for Add Area modal popup to appear",
                "locator_strategy": "modal_appearance",
                "expected_result": "Add Area modal is visible",
                "verification": {
                    "modal_visible": True,
                    "elements_present": [
                        "text=Add Area",
                        "input[placeholder*='Area']",
                        "button:has-text('Add')"
                    ]
                }
            },
            {
                "action": "fill_area_name",
                "target": "Area Name field",
                "value": "{area_name}",
                "description": "Fill Area Name field with specified area name",
                "locator_strategy": "form_field",
                "expected_result": "Area name entered successfully",
                "timeout": 40000,
                "element_selectors": [
                    "input[placeholder*='Area Name']",
                    "input[name*='areaName']",
                    "[data-testid='area-name-input']",
                    ".modal input[type='text']:first",
                    "input[label*='Area']"
                ]
            },
            {
                "action": "click_add_area_button",
                "target": "Add button in area modal",
                "description": "Click Add button to create the area",
                "locator_strategy": "modal_button",
                "expected_result": "Area creation submitted",
                "timeout": 40000,
                "element_selectors": [
                    ".modal button:has-text('Add')",
                    "[data-testid='add-area-submit']",
                    ".modal .btn-primary:has-text('Add')",
                    ".add-area-modal button[type='submit']"
                ]
            },
            {
                "action": "wait_area_success",
                "target": "area creation success",
                "value": "5",
                "description": "Wait for area creation success message",
                "locator_strategy": "success_message",
                "expected_result": "Area added successfully message appears",
                "verification": {
                    "success_message": "Area added successfully",
                    "modal_closes": True
                }
            },
            {
                "action": "verify_area_creation",
                "target": "area creation confirmation",
                "description": "Verify area was created and modal closed",
                "locator_strategy": "verification",
                "expected_result": "Area created successfully and visible in hierarchy",
                "verification": {
                    "elements_present": [
                        "text={area_name}",
                        ".hierarchy-item:has-text('{area_name}')"
                    ]
                }
            },
            {
                "action": "hover_area_menu",
                "target": "Area panel three-dots menu",
                "description": "Hover over 3-dots menu at end of area panel",
                "locator_strategy": "context_menu",
                "expected_result": "Area context menu options become visible",
                "timeout": 30000,
                "element_selectors": [
                    ".hierarchy-item:has-text('{area_name}') .three-dots-menu",
                    ".tree-node:has-text('{area_name}') .context-menu-trigger",
                    "[data-testid='{area_name}-context-menu']"
                ]
            },
            {
                "action": "click_add_building",
                "target": "Add Building option",
                "description": "Click Add Building option from area context menu",
                "locator_strategy": "context_menu_item",
                "expected_result": "Add Building modal popup appears",
                "timeout": 45000,
                "element_selectors": [
                    "text=Add Building",
                    ".context-menu-item:has-text('Add Building')",
                    "[data-testid='add-building-option']",
                    ".dropdown-item:has-text('Add Building')"
                ]
            },
            {
                "action": "wait_add_building_modal",
                "target": "Add Building modal",
                "value": "3",
                "description": "Wait for Add Building modal popup to appear",
                "locator_strategy": "modal_appearance",
                "expected_result": "Add Building modal is visible",
                "verification": {
                    "modal_visible": True,
                    "elements_present": [
                        "text=Add Building",
                        "input[placeholder*='Building']",
                        "input[placeholder*='Address']",
                        "button:has-text('Add')"
                    ]
                }
            },
            {
                "action": "fill_building_name",
                "target": "Building Name field",
                "value": "{building_name}",
                "description": "Fill Building Name field with specified building name",
                "locator_strategy": "form_field",
                "expected_result": "Building name entered successfully",
                "timeout": 30000,
                "element_selectors": [
                    "input[placeholder*='Building Name']",
                    "input[name*='buildingName']",
                    "[data-testid='building-name-input']",
                    ".modal input[type='text']:first"
                ]
            },
            {
                "action": "click_address_search",
                "target": "Address search box",
                "description": "Click on Address search box to focus",
                "locator_strategy": "form_field",
                "expected_result": "Address search box focused",
                "timeout": 30000,
                "element_selectors": [
                    "input[placeholder*='Address']",
                    "input[name*='address']",
                    "[data-testid='address-search-input']",
                    ".address-search input"
                ]
            },
            {
                "action": "fill_address_search",
                "target": "Address search field",
                "value": "{address_search}",
                "description": "Enter search term for building address",
                "locator_strategy": "search_field",
                "expected_result": "Address search term entered",
                "timeout": 40000,
                "post_action_wait": 10000
            },
            {
                "action": "wait_address_results",
                "target": "address search results",
                "value": "5",
                "description": "Wait for address search results to appear",
                "locator_strategy": "search_results",
                "expected_result": "Address search results visible",
                "verification": {
                    "elements_present": [
                        ".search-results",
                        ".address-option",
                        "[data-testid='address-results']"
                    ]
                }
            },
            {
                "action": "select_first_address",
                "target": "first address option",
                "description": "Click on first option from address search results",
                "locator_strategy": "search_result_item",
                "expected_result": "Address selected successfully",
                "timeout": 40000,
                "element_selectors": [
                    ".search-results .address-option:first",
                    ".address-dropdown .option:first",
                    "[data-testid='address-result']:first",
                    ".search-results li:first"
                ]
            },
            {
                "action": "click_add_building_button",
                "target": "Add button in building modal",
                "description": "Click Add button to create the building",
                "locator_strategy": "modal_button",
                "expected_result": "Building creation submitted",
                "timeout": 60000,
                "element_selectors": [
                    ".modal button:has-text('Add')",
                    "[data-testid='add-building-submit']",
                    ".modal .btn-primary:has-text('Add')",
                    ".add-building-modal button[type='submit']"
                ]
            },
            {
                "action": "wait_building_success",
                "target": "building creation success",
                "value": "10",
                "description": "Wait for building creation success message",
                "locator_strategy": "success_message",
                "expected_result": "Site added successfully message appears",
                "verification": {
                    "success_message": "Site added successfully",
                    "modal_closes": True
                }
            },
            {
                "action": "verify_building_creation",
                "target": "building creation confirmation",
                "description": "Verify building was created and modal closed",
                "locator_strategy": "verification",
                "expected_result": "Building created successfully and visible in hierarchy",
                "verification": {
                    "elements_present": [
                        "text={building_name}",
                        ".hierarchy-item:has-text('{building_name}')"
                    ]
                }
            },
            {
                "action": "expand_global_final",
                "target": "Global hierarchy dropdown",
                "description": "Expand Global hierarchy to verify complete structure",
                "locator_strategy": "hierarchy_expand",
                "expected_result": "Global hierarchy fully expanded",
                "condition": "{verify_hierarchy}",
                "element_selectors": [
                    ".hierarchy-item:has-text('Global') .expand-arrow",
                    ".tree-node:has-text('Global') .dropdown-toggle"
                ]
            },
            {
                "action": "expand_area_final",
                "target": "Area hierarchy dropdown",
                "description": "Expand area hierarchy to show building",
                "locator_strategy": "hierarchy_expand",
                "expected_result": "Area hierarchy expanded showing building",
                "condition": "{verify_hierarchy}",
                "element_selectors": [
                    ".hierarchy-item:has-text('{area_name}') .expand-arrow",
                    ".tree-node:has-text('{area_name}') .dropdown-toggle"
                ]
            },
            {
                "action": "capture_hierarchy_screenshot",
                "target": "complete hierarchy view",
                "description": "Take screenshot of complete site hierarchy",
                "locator_strategy": "screenshot",
                "expected_result": "Screenshot captured successfully",
                "condition": "{verify_hierarchy}",
                "screenshot_options": {
                    "full_page": False,
                    "element": ".hierarchy-container",
                    "filename": "network_hierarchy_{area_name}_{building_name}.png"
                }
            },
            {
                "action": "verify_complete_hierarchy",
                "target": "site hierarchy path",
                "description": "Verify complete hierarchy path Global/{area_name}/{building_name}",
                "locator_strategy": "hierarchy_verification",
                "expected_result": "Complete site hierarchy verified",
                "verification": {
                    "hierarchy_path": "Global/{area_name}/{building_name}",
                    "elements_visible": [
                        "text=Global",
                        "text={area_name}",
                        "text={building_name}"
                    ]
                }
            }
        ],
        success_criteria=[
            "Successfully navigate to Network Hierarchy page at /dna/design/networkHierarchy",
            "Area '{area_name}' created with 'Area added successfully' message",
            "Building '{building_name}' created with 'Site added successfully' message", 
            "Complete hierarchy 'Global/{area_name}/{building_name}' visible in expanded view",
            "Screenshot captured showing the full site hierarchy",
            "All modals close automatically after successful operations"
        ],
        estimated_duration=120,  # 2 minutes
        created_by="dna_center_specialist",
        version="1.0",
        failure_recovery=[
            {
                "condition": "Navigation menu not found",
                "action": "refresh_page_and_retry",
                "max_retries": 2
            },
            {
                "condition": "Modal does not appear",
                "action": "click_again_after_wait", 
                "wait_time": 3000,
                "max_retries": 3
            },
            {
                "condition": "Address search returns no results",
                "action": "try_alternative_search_terms",
                "alternatives": ["California", "CA", "United States"]
            },
            {
                "condition": "Duplicate name error",
                "action": "append_timestamp_to_name",
                "format": "{original_name}_{timestamp}"
            }
        ]
    )