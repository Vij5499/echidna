# error_handler.py
import logging
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum
import traceback

class ErrorSeverity(Enum):
    LOW = "low"           # Minor issues, continue operation
    MEDIUM = "medium"     # Significant issues, degrade gracefully  
    HIGH = "high"         # Critical issues, require intervention
    CRITICAL = "critical" # System-threatening, immediate action needed

class ErrorType(Enum):
    LLM_FAILURE = "llm_failure"
    API_CONNECTION = "api_connection"
    CONSTRAINT_PARSING = "constraint_parsing"
    TEST_EXECUTION = "test_execution"
    FILE_SYSTEM = "file_system"
    CONFIGURATION = "configuration"

class AdaptiveError(Exception):
    def __init__(self, message: str, error_type: ErrorType, 
                 severity: ErrorSeverity, context: Dict[str, Any] = None):
        super().__init__(message)
        self.error_type = error_type
        self.severity = severity
        self.context = context or {}
        self.timestamp = time.time()

class ErrorHandler:
    def __init__(self):
        self.error_history = []
        self.recovery_strategies = {
            ErrorType.LLM_FAILURE: self._handle_llm_failure,
            ErrorType.API_CONNECTION: self._handle_api_connection,
            ErrorType.CONSTRAINT_PARSING: self._handle_constraint_parsing,
            ErrorType.TEST_EXECUTION: self._handle_test_execution,
            ErrorType.FILE_SYSTEM: self._handle_file_system,
            ErrorType.CONFIGURATION: self._handle_configuration
        }
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('adaptive_agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AdaptiveAgent')
    
    def handle_error(self, error: AdaptiveError) -> Optional[Any]:
        """Handle error with appropriate recovery strategy"""
        self.error_history.append(error)
        self.logger.error(f"Error occurred: {error.error_type.value} - {str(error)}")
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {str(error)}")
            self._notify_administrators(error)
        
        # Attempt recovery
        recovery_func = self.recovery_strategies.get(error.error_type)
        if recovery_func:
            return recovery_func(error)
        
        return None
    
    def _handle_llm_failure(self, error: AdaptiveError) -> Optional[str]:
        """Handle LLM service failures with fallback strategies"""
        self.logger.warning("LLM failure detected, attempting recovery...")
        
        # Strategy 1: Use cached response if available
        if 'prompt' in error.context:
            cached_response = self._get_cached_response(error.context['prompt'])
            if cached_response:
                self.logger.info("Using cached LLM response")
                return cached_response
        
        # Strategy 2: Use simplified fallback generation
        if error.context.get('task') == 'test_generation':
            self.logger.info("Using fallback test generation")
            return self._generate_fallback_test(error.context)
        
        # Strategy 3: Graceful degradation
        return self._graceful_degradation(error)
    
    def _handle_api_connection(self, error: AdaptiveError) -> Optional[Any]:
        """Handle API connection failures"""
        self.logger.warning("API connection failure, implementing retry logic...")
        
        max_retries = 3
        base_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                time.sleep(delay)
                
                # Retry the failed operation
                if 'retry_function' in error.context:
                    return error.context['retry_function']()
                    
            except Exception as e:
                self.logger.warning(f"Retry attempt {attempt + 1} failed: {str(e)}")
        
        return None
    
    def _handle_constraint_parsing(self, error: AdaptiveError) -> Optional[Any]:
        """Handle constraint parsing failures"""
        self.logger.warning("Constraint parsing failed, attempting recovery...")
        
        # Try to extract partial constraints
        if 'raw_response' in error.context:
            partial_constraints = self._extract_partial_constraints(
                error.context['raw_response']
            )
            if partial_constraints:
                self.logger.info("Extracted partial constraints successfully")
                return partial_constraints
        
        return None
    
    def _handle_test_execution(self, error: AdaptiveError) -> Optional[Any]:
        """Handle test execution failures"""
        self.logger.warning("Test execution failed, analyzing failure...")
        
        # Categorize the failure
        if 'output' in error.context:
            failure_type = self._categorize_test_failure(error.context['output'])
            return {'failure_type': failure_type, 'recoverable': True}
        
        return None
    
    def _handle_file_system(self, error: AdaptiveError) -> Optional[Any]:
        """Handle file system errors"""
        self.logger.warning("File system error, attempting recovery...")
        
        # Try to recreate missing directories
        if 'missing_directory' in error.context:
            try:
                import os
                os.makedirs(error.context['missing_directory'], exist_ok=True)
                self.logger.info(f"Created missing directory: {error.context['missing_directory']}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to create directory: {str(e)}")
        
        return None
    
    def _handle_configuration(self, error: AdaptiveError) -> Optional[Any]:
        """Handle configuration errors"""
        self.logger.warning("Configuration error detected...")
        
        # Provide default configuration
        if 'missing_config' in error.context:
            default_config = self._get_default_config(error.context['missing_config'])
            self.logger.info(f"Using default configuration for: {error.context['missing_config']}")
            return default_config
        
        return None
    
    def _get_cached_response(self, prompt: str) -> Optional[str]:
        """Get cached LLM response if available"""
        # Implement caching logic here
        return None
    
    def _generate_fallback_test(self, context: Dict[str, Any]) -> str:
        """Generate a basic fallback test when LLM fails"""
        return '''import requests
import pytest

def test_api_endpoint_fallback(api_base_url):
    """Fallback test generated due to LLM failure"""
    response = requests.get(f"{api_base_url}/health")
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    print("Fallback test executed successfully")
'''
    
    def _graceful_degradation(self, error: AdaptiveError) -> Optional[str]:
        """Implement graceful degradation strategies"""
        self.logger.info("Implementing graceful degradation...")
        return "DEGRADED_MODE"
    
    def _extract_partial_constraints(self, raw_response: str) -> Optional[Dict]:
        """Try to extract partial constraint information"""
        # Implement partial constraint extraction logic
        return None
    
    def _categorize_test_failure(self, output: str) -> str:
        """Categorize the type of test failure"""
        if "ConnectionError" in output:
            return "connection_failure"
        elif "AssertionError" in output:
            return "assertion_failure"
        elif "SyntaxError" in output:
            return "syntax_error"
        else:
            return "unknown_failure"
    
    def _get_default_config(self, config_key: str) -> Dict[str, Any]:
        """Provide default configuration values"""
        defaults = {
            'max_retries': 3,
            'timeout': 30,
            'learning_rate': 0.1,
            'confidence_threshold': 0.7
        }
        return defaults.get(config_key, {})
    
    def _notify_administrators(self, error: AdaptiveError):
        """Notify system administrators of critical errors"""
        # Implement notification logic (email, Slack, etc.)
        self.logger.critical(f"ADMIN NOTIFICATION: {str(error)}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about errors encountered"""
        if not self.error_history:
            return {"total_errors": 0}
        
        error_counts = {}
        for error in self.error_history:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "error_breakdown": error_counts,
            "recent_errors": len([e for e in self.error_history 
                                if time.time() - e.timestamp < 3600])  # Last hour
        }

# Global error handler instance
error_handler = ErrorHandler()
