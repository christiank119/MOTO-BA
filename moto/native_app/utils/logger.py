import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any

class LoggerFactory:
    """
    Central logging utility for the MOTO native application.
    Provides standardized logging configuration across all modules.
    """
    
    # Singleton instance
    _instance: Optional['LoggerFactory'] = None
    
    # Default configuration
    DEFAULT_CONFIG = {
        "log_level": logging.INFO,
        "console_log_level": logging.INFO,
        "file_log_level": logging.DEBUG,
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "log_dir": "logs",
        "max_file_size": 5 * 1024 * 1024,  # 5 MB
        "backup_count": 5,
        "enabled": True,                   # Master switch for logging
        "console_enabled": True,           # Enable/disable console logging
        "file_enabled": True               # Enable/disable file logging
    }
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern for LoggerFactory"""
        if cls._instance is None:
            cls._instance = super(LoggerFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the logger factory with optional custom configuration"""
        if self._initialized:
            return
            
        # Merge default config with custom config
        self._config = self.DEFAULT_CONFIG.copy()
        if config:
            self._config.update(config)
            
        # Create log directory if it doesn't exist
        log_dir = self._config["log_dir"]
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Set up root logger with null handler
        logging.getLogger().addHandler(logging.NullHandler())
        
        # Flag to avoid re-initialization
        self._initialized = True
        
        # Root console handler is shared by all loggers
        self._console_handler = self._create_console_handler()
    
    def _create_console_handler(self) -> Optional[logging.Handler]:
        """Create and configure console handler if enabled"""
        if not self._config["console_enabled"] or not self._config["enabled"]:
            return None
            
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self._config["console_log_level"])
        console_handler.setFormatter(logging.Formatter(
            self._config["log_format"],
            self._config["date_format"]
        ))
        return console_handler
        
    def _create_file_handler(self, logger_name: str) -> Optional[logging.Handler]:
        """Create and configure file handler for specific logger if enabled"""
        if not self._config["file_enabled"] or not self._config["enabled"]:
            return None
            
        # Create a specific log file for this logger
        log_file = os.path.join(
            self._config["log_dir"],
            f"{logger_name}.log"
        )
        
        # Rotating file handler with size limits
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self._config["max_file_size"],
            backupCount=self._config["backup_count"]
        )
        file_handler.setLevel(self._config["file_log_level"])
        file_handler.setFormatter(logging.Formatter(
            self._config["log_format"],
            self._config["date_format"]
        ))
        return file_handler
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a configured logger for the specified module/component.
        
        Args:
            name: The name of the logger (usually __name__ or class name)
            
        Returns:
            A configured logger instance
        """
        # Get or create the logger
        logger = logging.getLogger(name)
        
        # Only configure if this is the first time getting this logger
        if not logger.handlers:
            if not self._config["enabled"]:
                # If logging is disabled, use a very high level to suppress all logs
                logger.setLevel(logging.CRITICAL + 10)
                logger.addHandler(logging.NullHandler())
                logger.propagate = False
                return logger
                
            # Set the overall logger level to the lowest of console/file
            min_level = min(
                self._config["console_log_level"] if self._config["console_enabled"] else logging.CRITICAL,
                self._config["file_log_level"] if self._config["file_enabled"] else logging.CRITICAL
            )
            logger.setLevel(min_level)
            
            # Add console handler if configured
            if self._console_handler:
                logger.addHandler(self._console_handler)
            
            # Add file handler if configured
            file_handler = self._create_file_handler(name)
            if file_handler:
                logger.addHandler(file_handler)
            
            # Prevent propagation to root logger to avoid duplicate logs
            logger.propagate = False
            
        return logger
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update the logging configuration.
        
        Args:
            config: Dictionary with configuration values to update
        """
        # Update configuration
        self._config.update(config)
        
        # Create log directory if needed and logging is enabled
        if self._config["enabled"] and self._config["file_enabled"]:
            log_dir = self._config["log_dir"]
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        
        # Handle console handler updates
        if self._config["enabled"] and self._config["console_enabled"]:
            if self._console_handler:
                self._console_handler.setLevel(self._config["console_log_level"])
            else:
                # Create a new console handler if it was previously disabled
                self._console_handler = self._create_console_handler()
        elif self._console_handler:
            # Remove console handler reference if logging is disabled
            self._console_handler = None
    
    def enable_logging(self, enable: bool = True) -> None:
        """
        Enable or disable all logging.
        
        Args:
            enable: True to enable logging, False to disable
        """
        self.update_config({"enabled": enable})
    
    def enable_console_logging(self, enable: bool = True) -> None:
        """
        Enable or disable console logging only.
        
        Args:
            enable: True to enable console logging, False to disable
        """
        self.update_config({"console_enabled": enable})
    
    def enable_file_logging(self, enable: bool = True) -> None:
        """
        Enable or disable file logging only.
        
        Args:
            enable: True to enable file logging, False to disable
        """
        self.update_config({"file_enabled": enable})

# Global factory instance with default configuration
logger_factory = LoggerFactory()

def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger from the factory.
    
    Args:
        name: The name for the logger
        
    Returns:
        A configured logger
    """
    return logger_factory.get_logger(name)

# Convenience functions for enabling/disabling logging
def enable_logging(enable: bool = True) -> None:
    """Enable or disable all logging"""
    logger_factory.enable_logging(enable)

def enable_console_logging(enable: bool = True) -> None:
    """Enable or disable console logging"""
    logger_factory.enable_console_logging(enable)

def enable_file_logging(enable: bool = True) -> None:
    """Enable or disable file logging"""
    logger_factory.enable_file_logging(enable)

def set_console_level(level) -> None:
    """Set console logging level"""
    logger_factory.update_config({"console_log_level": level})

def set_file_level(level) -> None:
    """Set file logging level"""
    logger_factory.update_config({"file_log_level": level})