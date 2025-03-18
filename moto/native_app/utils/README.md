# MOTO Native App Utilities

This directory contains utility modules for the MOTO native application.

## Logging Utilities

### Basic Logging

```python
from utils import get_logger

# Get a logger for the current module/component
logger = get_logger("MyComponent")

# Use standard logging methods
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Decorators for Function Logging

```python
from utils import log_operation

# Simple usage - logs entry and exit with default settings
@log_operation
def my_function():
    # function code here
    pass

# Advanced usage with options
@log_operation(log_args=True, log_level="debug", logger_name="custom_logger")
def my_advanced_function(arg1, arg2):
    # function code here
    pass
```

### Context Manager for Block Logging

```python
from utils import LoggingContext

# Simple usage
with LoggingContext("operation_name"):
    # code to log as a block
    pass

# Advanced usage
with LoggingContext("operation_name", logger_name="custom_logger", 
                   log_args=True, log_level="DEBUG"):
    # code to log as a block
    pass
```

### Enabling/Disabling Logging

```python
from utils import enable_logging, enable_console_logging, enable_file_logging

# Completely disable logging
enable_logging(False)

# Disable only console output (keep file logging)
enable_console_logging(False)

# Disable only file output (keep console logging)
enable_file_logging(False)

# Re-enable all logging
enable_logging(True)
```

### Setting Log Levels

```python
import logging
from utils import set_console_level, set_file_level

# Change console logging level
set_console_level(logging.WARNING)  # Only show warnings and errors

# Change file logging level
set_file_level(logging.DEBUG)  # Record everything in log files
```

### Environment Variables

The application reads logging configuration from environment variables, which can be set in a `.env` file:

```ini
# Disable all logging
MOTO_LOGGING_ENABLED=false

# Disable only console logging
MOTO_CONSOLE_LOGGING=false

# Disable only file logging
MOTO_FILE_LOGGING=false

# Set log levels
MOTO_CONSOLE_LOG_LEVEL=warning  # Options: debug, info, warning, error, critical
MOTO_FILE_LOG_LEVEL=debug

# Change log directory
MOTO_LOG_DIR=custom/logs/path
```

Copy the `.env.example` file to `.env` and modify it to configure logging.

## API Client

```python
from utils import APIClient

# Create API client
api = APIClient(
    base_url="https://api.example.com",
    device_id="device-123"
)

# Authenticate
success, response = api.login("username", "password")

# Make API requests
success, data = api.get("users/123")
success, data = api.post("messages", {"content": "Hello"})
success, data = api.put("users/123", {"name": "New Name"})
success, data = api.delete("messages/456")
```

## Runtime Configuration

The logging system can be configured at runtime:

```python
from utils import logger_factory
import logging

# Update logging configuration
logger_factory.update_config({
    "console_log_level": logging.DEBUG,  # Show more detail in console
    "file_log_level": logging.WARNING,   # Only warnings and errors in files
    "log_dir": "custom_logs",            # Change log directory
    "max_file_size": 10 * 1024 * 1024,   # 10MB logs
    "backup_count": 10,                  # Keep 10 backup files
    "enabled": True,                     # Master switch for all logging
    "console_enabled": True,             # Switch for console logging
    "file_enabled": True                 # Switch for file logging
})

# Simple enable/disable functions
logger_factory.enable_logging(False)     # Disable all logging
logger_factory.enable_console_logging(False)  # Disable console logging only
logger_factory.enable_file_logging(False)     # Disable file logging only
```