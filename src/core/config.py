# Fixed src/core/config.py (Updated with Azure settings)

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import tempfile
import sys

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # MCP Server Settings
    MCP_SERVER_NAME: str = Field(default="e2e-testing-server", description="MCP server name")
    MCP_SERVER_VERSION: str = Field(default="0.2.0", description="MCP server version")
    
    # Environment Settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Browser Settings
    BROWSER_TYPE: str = Field(default="chromium", description="Browser type (chromium/firefox/webkit)")
    HEADLESS: bool = Field(default=True, description="Run browser in headless mode")
    BROWSER_TIMEOUT: int = Field(default=30000, description="Browser timeout in milliseconds")
    
    # Azure OpenAI Settings
    AZURE_CLIENT_ID: Optional[str] = Field(default=None, description="Azure client ID")
    AZURE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Azure client secret")
    AZURE_APP_KEY: Optional[str] = Field(default=None, description="Azure app key")
    AZURE_API_BASE: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")
    AZURE_API_VERSION: str = Field(default="2024-07-01-preview", description="Azure OpenAI API version")
    AZURE_IDP_ENDPOINT: Optional[str] = Field(default=None, description="Azure IDP endpoint")
    AZURE_MODEL: str = Field(default="gpt-4o-mini", description="Azure OpenAI model")
    
    # Legacy AI Settings (fallback)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Database Settings
    DATABASE_URL: str = Field(default="sqlite:///:memory:", description="Database URL")
    
    # Logging Settings
    LOG_FILE: str = Field(default="", description="Log file path")
    LOG_MAX_SIZE: str = Field(default="10MB", description="Maximum log file size")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of log backup files")
    
    # Paths - Will be set in __init__
    PROJECT_ROOT: Optional[Path] = Field(default=None, description="Project root directory")
    DATA_DIR: Optional[Path] = Field(default=None, description="Data directory")
    LOGS_DIR: Optional[Path] = Field(default=None, description="Logs directory")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set project root
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent
        
        # Try to create directories in project root first
        try:
            self.DATA_DIR = self.PROJECT_ROOT / "data"
            self.LOGS_DIR = self.PROJECT_ROOT / "logs"
            
            # Test if we can write to project directory
            self.DATA_DIR.mkdir(exist_ok=True)
            self.LOGS_DIR.mkdir(exist_ok=True)
            
            # Test write permissions
            test_file = self.DATA_DIR / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            # Update log file path if not set
            if not self.LOG_FILE:
                self.LOG_FILE = str(self.LOGS_DIR / "mcp_server.log")
            
            print(f"Using project directories: {self.DATA_DIR}", file=sys.stderr)
            
        except (OSError, PermissionError) as e:
            print(f"Cannot write to project directory ({e}), using temp directories", file=sys.stderr)
            
            # Fallback to temp directories
            temp_base = Path(tempfile.gettempdir()) / "e2e_testing_mcp"
            
            try:
                self.DATA_DIR = temp_base / "data"
                self.LOGS_DIR = temp_base / "logs"
                
                self.DATA_DIR.mkdir(parents=True, exist_ok=True)
                self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
                
                # Update database URL to use temp directory
                self.DATABASE_URL = f"sqlite:///{self.DATA_DIR}/test_sessions.db"
                
                # Update log file path
                if not self.LOG_FILE:
                    self.LOG_FILE = str(self.LOGS_DIR / "mcp_server.log")
                
                print(f"Using temp directories: {self.DATA_DIR}", file=sys.stderr)
                
            except Exception as temp_error:
                print(f"Cannot create temp directories ({temp_error}), using in-memory only", file=sys.stderr)
                
                # Final fallback - no persistent storage
                self.DATA_DIR = None
                self.LOGS_DIR = None
                self.DATABASE_URL = "sqlite:///:memory:"
                self.LOG_FILE = ""  # No file logging
                
                print("Running in memory-only mode", file=sys.stderr)

    def get_azure_openai_config(self):
        """Get Azure OpenAI configuration"""
        from src.ai.azure_openai_client import AzureOpenAIConfig
        
        if not all([self.AZURE_CLIENT_ID, self.AZURE_CLIENT_SECRET, self.AZURE_APP_KEY, 
                   self.AZURE_API_BASE, self.AZURE_IDP_ENDPOINT]):
            raise ValueError("Missing required Azure OpenAI configuration. Please check your .env file.")
        
        return AzureOpenAIConfig(
            client_id=self.AZURE_CLIENT_ID,
            client_secret=self.AZURE_CLIENT_SECRET,
            app_key=self.AZURE_APP_KEY,
            api_base=self.AZURE_API_BASE,
            api_version=self.AZURE_API_VERSION,
            idp_endpoint=self.AZURE_IDP_ENDPOINT,
            model=self.AZURE_MODEL
        )