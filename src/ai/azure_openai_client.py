import base64
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from langchain_openai import AzureChatOpenAI
import openai

logger = logging.getLogger("e2e_testing_mcp")

@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI configuration"""
    client_id: str
    client_secret: str
    app_key: str
    api_base: str
    api_version: str = "2024-07-01-preview"
    idp_endpoint: str = ""
    model: str = "gpt-4o-mini"

class AzureOpenAIClient:
    """Azure OpenAI client with token management"""
    
    def __init__(self, config: AzureOpenAIConfig):
        self.config = config
        self.access_token = None
        self.llm = None
        self._setup_openai()
    
    def _setup_openai(self):
        """Setup OpenAI configuration"""
        openai.api_type = "azure"
        openai.api_version = self.config.api_version
        openai.api_base = self.config.api_base
    
    def _fetch_access_token(self) -> str:
        """Fetch access token from IDP"""
        try:
            payload = "grant_type=client_credentials"
            value = base64.b64encode(
                f"{self.config.client_id}:{self.config.client_secret}".encode("utf-8")
            ).decode("utf-8")
            
            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {value}"
            }
            
            logger.info("Fetching access token from Azure IDP")
            token_response = requests.post(self.config.idp_endpoint, headers=headers, data=payload)
            
            if token_response.status_code != 200:
                raise Exception(f"Failed to fetch token: {token_response.text}")
            
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise Exception("No access token returned from IDP.")
            
            logger.info("Successfully obtained Azure access token")
            return access_token
            
        except Exception as e:
            logger.error(f"Error fetching Azure access token: {str(e)}")
            raise
    
    def _get_llm_client(self) -> AzureChatOpenAI:
        """Get or create LLM client with fresh token"""
        try:
            # Fetch fresh token
            self.access_token = self._fetch_access_token()
            
            # Create LangChain Azure OpenAI client
            self.llm = AzureChatOpenAI(
                deployment_name=self.config.model,
                azure_endpoint=self.config.api_base,
                api_key=self.access_token,
                api_version=self.config.api_version,
                model_kwargs=dict(user=f'{{"appkey": "{self.config.app_key}"}}')
            )
            
            logger.info(f"Azure OpenAI client created with model: {self.config.model}")
            return self.llm
            
        except Exception as e:
            logger.error(f"Error creating Azure OpenAI client: {str(e)}")
            raise
    
    async def parse_test_instructions(self, prompt: str, url: str = "", username: str = "", password: str = "") -> Dict[str, Any]:
        """Parse test instructions using Azure OpenAI"""
        try:
            llm = self._get_llm_client()
            
            # Create structured prompt for test parsing
            system_prompt = """You are an expert E2E test automation engineer. Parse natural language test instructions into structured test steps.

Return a JSON object with this exact structure:
{
  "test_name": "Brief descriptive name for the test",
  "description": "What this test accomplishes",
  "steps": [
    {
      "action": "navigate|click|fill|verify|wait|select",
      "target": "element description or URL",
      "value": "value to enter (for fill actions)",
      "description": "human readable description",
      "locator_strategy": "id|class|text|xpath|css",
      "expected_result": "what should happen after this step"
    }
  ],
  "prerequisites": ["any setup requirements"],
  "expected_outcome": "overall test success criteria"
}

Action types:
- navigate: Go to a URL
- click: Click buttons, links, or elements  
- fill: Enter text in input fields
- verify: Check if something exists or has expected value
- wait: Wait for element or condition
- select: Choose from dropdown or radio buttons

Locator strategies:
- id: Find by element ID
- class: Find by CSS class
- text: Find by visible text content
- xpath: Find by XPath expression
- css: Find by CSS selector"""

            user_prompt = f"""Parse this test instruction into structured steps:

Instruction: {prompt}
Target URL: {url if url else "Not specified"}
Username: {username if username else "Not provided"}
Password: {"[PROVIDED]" if password else "Not provided"}

Generate detailed, actionable test steps that can be executed by browser automation."""

            # Call Azure OpenAI
            logger.info("Calling Azure OpenAI for instruction parsing")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = llm.invoke(messages)
            
            # Parse response
            response_text = response.content.strip()
            logger.debug(f"Azure OpenAI response: {response_text[:200]}...")
            
            # Try to extract JSON from response
            try:
                # Handle cases where response might have markdown formatting
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text
                
                parsed_result = json.loads(json_text)
                logger.info("Successfully parsed Azure OpenAI response")
                return parsed_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Azure OpenAI response: {e}")
                # Fallback to basic parsing
                return self._fallback_parsing(prompt, url, username, password)
                
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {str(e)}")
            # Fallback to basic parsing
            return self._fallback_parsing(prompt, url, username, password)
    
    def _fallback_parsing(self, prompt: str, url: str, username: str, password: str) -> Dict[str, Any]:
        """Fallback parsing when Azure OpenAI fails"""
        logger.warning("Using fallback parsing due to Azure OpenAI error")
        
        steps = []
        prompt_lower = prompt.lower()
        
        # Basic navigation
        if url:
            steps.append({
                "action": "navigate",
                "target": url,
                "value": "",
                "description": f"Navigate to {url}",
                "locator_strategy": "url",
                "expected_result": "Page loads successfully"
            })
        
        # Login steps
        if username and password:
            steps.extend([
                {
                    "action": "fill",
                    "target": "username field",
                    "value": username,
                    "description": "Enter username",
                    "locator_strategy": "id",
                    "expected_result": "Username entered"
                },
                {
                    "action": "fill",
                    "target": "password field", 
                    "value": password,
                    "description": "Enter password",
                    "locator_strategy": "id",
                    "expected_result": "Password entered"
                },
                {
                    "action": "click",
                    "target": "login button",
                    "value": "",
                    "description": "Click login button",
                    "locator_strategy": "text",
                    "expected_result": "User logged in successfully"
                }
            ])
        
        # Parse additional actions
        if "click" in prompt_lower:
            steps.append({
                "action": "click",
                "target": "button or link",
                "value": "",
                "description": "Click specified element",
                "locator_strategy": "text",
                "expected_result": "Element clicked successfully"
            })
        
        if "fill" in prompt_lower or "enter" in prompt_lower:
            steps.append({
                "action": "fill",
                "target": "input field",
                "value": "test data",
                "description": "Fill form field",
                "locator_strategy": "id",
                "expected_result": "Form field filled"
            })
        
        if "verify" in prompt_lower:
            steps.append({
                "action": "verify",
                "target": "page content",
                "value": "",
                "description": "Verify expected content",
                "locator_strategy": "text",
                "expected_result": "Content verified successfully"
            })
        
        return {
            "test_name": f"Test for {url or 'web application'}",
            "description": prompt,
            "steps": steps,
            "prerequisites": [],
            "expected_outcome": "Test completes successfully"
        }