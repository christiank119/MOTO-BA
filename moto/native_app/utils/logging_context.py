from functools import wraps
import inspect
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from .logger import get_logger

# Type variables for generics
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

# Logger for this module
logger = get_logger("logging_context")

class LoggingContext:
    """
    Context manager for logging the execution of a block of code.
    Tracks entry, exit, duration, and any exceptions.
    """
    
    def __init__(self, context_name: str, logger_name: Optional[str] = None, 
                 log_args: bool = False, log_level: str = "INFO"):
        """
        Initialize logging context.
        
        Args:
            context_name: Name to identify this context in logs
            logger_name: Optional specific logger to use, defaults to context_name
            log_args: Whether to log function arguments
            log_level: Log level to use (DEBUG, INFO, etc.)
        """
        self.context_name = context_name
        self.logger = get_logger(logger_name or context_name)
        self.log_args = log_args
        self.log_level = log_level.upper()
        self.start_time = 0.0
        
    def __enter__(self) -> 'LoggingContext':
        """Log entry into the context"""
        self.start_time = time.time()
        
        log_method = getattr(self.logger, self.log_level.lower())
        log_method(f"ENTER: {self.context_name}")
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log exit from the context with duration and any exception"""
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            # Log exception details
            self.logger.error(
                f"EXIT: {self.context_name} failed after {duration:.4f}s "
                f"with {exc_type.__name__}: {exc_val}"
            )
        else:
            # Log normal completion
            log_method = getattr(self.logger, self.log_level.lower())
            log_method(f"EXIT: {self.context_name} completed in {duration:.4f}s")
            
        # Don't suppress exceptions
        return False

def log_operation(func: F = None, *, logger_name: Optional[str] = None, 
                 log_args: bool = False, log_level: str = "INFO") -> Callable[[F], F]:
    """
    Decorator to log function entry, exit, arguments, and duration.
    
    Args:
        func: The function to decorate
        logger_name: Optional logger name, defaults to function's module name
        log_args: Whether to log function arguments
        log_level: Log level to use (DEBUG, INFO, etc.)
        
    Returns:
        Decorated function with logging
    """
    def decorator(func: F) -> F:
        # Get function's qualname for better log identification
        func_name = func.__qualname__
        
        # Default logger name to the module where the function is defined
        module_name = func.__module__
        logger_to_use = logger_name or module_name
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_to_use)
            log_method = getattr(logger, log_level.lower())
            
            # Build argument log if requested
            arg_log = ""
            if log_args:
                # Get signature to match positional args with parameter names
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Format args/kwargs for logging (exclude self/cls from instance/class methods)
                params = dict(bound_args.arguments)
                if args and inspect.ismethod(func):
                    # If it's a method, remove 'self' or 'cls'
                    params.pop(next(iter(params.keys())), None)
                
                arg_log = f" with args: {params}"
            
            # Log function entry
            log_method(f"CALL: {func_name}{arg_log}")
            
            # Track execution time
            start_time = time.time()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                # Log successful completion
                duration = time.time() - start_time
                log_method(f"RETURN: {func_name} completed in {duration:.4f}s")
                return result
            except Exception as e:
                # Log exception
                duration = time.time() - start_time
                logger.error(
                    f"ERROR: {func_name} failed after {duration:.4f}s "
                    f"with {type(e).__name__}: {str(e)}"
                )
                # Re-raise the exception
                raise
                
        return cast(F, wrapper)
    
    # Support both @log_operation and @log_operation()
    if func is None:
        return decorator
    return decorator(func)