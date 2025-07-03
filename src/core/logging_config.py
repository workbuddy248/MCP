# Fixed src/core/logging_config.py - Handle read-only filesystem

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

def setup_logging(settings) -> logging.Logger:
    """Set up structured logging for the application"""
    
    # Create logger
    logger = logging.getLogger("e2e_testing_mcp")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Console handler (always available)
    console_handler = logging.StreamHandler(sys.stderr)  # Use stderr for MCP
    console_handler.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (only if we can write files)
    if settings.LOG_FILE and settings.LOGS_DIR:
        try:
            log_file_path = Path(settings.LOG_FILE)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_write = log_file_path.parent / "test_write.tmp"
            test_write.write_text("test")
            test_write.unlink()
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file_path,
                maxBytes=_parse_size(settings.LOG_MAX_SIZE),
                backupCount=settings.LOG_BACKUP_COUNT
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"File logging enabled: {log_file_path}")
            
        except (OSError, PermissionError) as e:
            logger.warning(f"File logging disabled due to permissions: {e}")
    else:
        logger.info("File logging disabled - using console only")
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    
    logger.info("Logging system initialized")
    return logger

def _parse_size(size_str: str) -> int:
    """Parse size string like '10MB' into bytes"""
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)