import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import TestInstruction, TestPlan
from src.core.config import Settings

@pytest.fixture
def settings():
    """Test settings fixture"""
    return Settings(
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        DATABASE_URL="sqlite:///:memory:"
    )

@pytest.fixture
def sample_instruction():
    """Sample test instruction fixture"""
    return TestInstruction(
        prompt="Login to the application and navigate to dashboard",
        url="https://example.com",
        username="testuser",
        password="testpass"
    )

@pytest.mark.asyncio
async def test_test_instruction_creation(sample_instruction):
    """Test TestInstruction model creation"""
    assert sample_instruction.prompt == "Login to the application and navigate to dashboard"
    assert sample_instruction.url == "https://example.com"
    assert sample_instruction.username == "testuser"
    assert sample_instruction.password == "testpass"

@pytest.mark.asyncio
async def test_url_validation():
    """Test URL validation in TestInstruction"""
    # Test URL without protocol
    instruction = TestInstruction(
        prompt="Test",
        url="example.com"
    )
    assert instruction.url == "https://example.com"
    
    # Test empty URL
    instruction = TestInstruction(
        prompt="Test",
        url=""
    )
    assert instruction.url == "https://example.com"

@pytest.mark.asyncio 
async def test_test_plan_creation():
    """Test TestPlan model creation"""
    plan = TestPlan(
        name="Test Plan",
        description="Test plan description",
        steps=[
            {"action": "navigate", "target": "https://example.com", "description": "Navigate to site"},
            {"action": "click", "target": "login button", "description": "Click login"}
        ]
    )
    
    assert plan.name == "Test Plan"
    assert len(plan.steps) == 2
    assert plan.steps[0]["action"] == "navigate"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])