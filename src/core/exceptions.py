class E2ETestingError(Exception):
    """Base exception for E2E testing server"""
    pass

class ValidationError(E2ETestingError):
    """Validation error"""
    pass

class BrowserError(E2ETestingError):
    """Browser automation error"""
    pass

class AuthenticationError(E2ETestingError):
    """Authentication error"""
    pass

class WorkflowError(E2ETestingError):
    """Workflow execution error"""
    pass

class ConfigurationError(E2ETestingError):
    """Configuration error"""
    pass