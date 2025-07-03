from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, validator

class TestInstruction(BaseModel):
    """Raw test instruction from user"""
    prompt: str = Field(..., description="Natural language test description")
    url: str = Field(..., description="Target application URL")
    username: str = Field(default="", description="Login username")
    password: str = Field(default="", description="Login password")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            return f'https://{v}' if v else 'https://example.com'
        return v

class WorkflowStep(BaseModel):
    """Individual step in a test workflow"""
    action: str = Field(..., description="Action type (navigate, click, fill, verify)")
    target: str = Field(..., description="Target element or location")
    value: Optional[str] = Field(default=None, description="Value for fill actions")
    description: str = Field(..., description="Human readable step description")
    timeout: int = Field(default=30000, description="Step timeout in milliseconds")
    retry_count: int = Field(default=3, description="Number of retries for this step")

class TestPlan(BaseModel):
    """Structured test plan with ordered steps"""
    name: str = Field(..., description="Test plan name")
    description: str = Field(..., description="Test plan description")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Ordered list of test steps")
    estimated_duration: int = Field(default=0, description="Estimated duration in seconds")
    created_at: datetime = Field(default_factory=datetime.now)

class StepResult(BaseModel):
    """Result of executing a single step"""
    step_number: int = Field(..., description="Step number in sequence")
    action: str = Field(..., description="Action that was executed")
    target: str = Field(..., description="Target element")
    status: str = Field(..., description="Step status (success/failed/skipped)")
    message: str = Field(..., description="Result message")
    timestamp: float = Field(..., description="Execution timestamp")
    screenshot_path: Optional[str] = Field(default=None, description="Screenshot path if taken")
    error_details: Optional[str] = Field(default=None, description="Error details if failed")

class ExecutionResult(BaseModel):
    """Complete test execution result"""
    success: bool = Field(..., description="Overall execution success")
    steps_executed: int = Field(..., description="Number of steps executed")
    total_steps: int = Field(..., description="Total number of steps in plan")
    execution_details: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed step results")
    message: str = Field(..., description="Overall execution message")
    duration: float = Field(default=0.0, description="Total execution time in seconds")
    created_at: datetime = Field(default_factory=datetime.now)