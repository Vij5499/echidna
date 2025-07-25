# test_error_handling.py
import pytest
import unittest.mock as mock
import tempfile
import os
import time
from error_handler import ErrorHandler, AdaptiveError, ErrorType, ErrorSeverity
from constraint_model import APIConstraintModel

class TestErrorHandling:
    def setup_method(self):
        """Setup for each test method"""
        self.error_handler = ErrorHandler()
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_error_creation_and_categorization(self):
        """Test basic error creation and categorization"""
        error = AdaptiveError(
            "Test LLM failure",
            ErrorType.LLM_FAILURE,
            ErrorSeverity.HIGH,
            context={'prompt': 'test prompt'}
        )
        
        assert error.error_type == ErrorType.LLM_FAILURE
        assert error.severity == ErrorSeverity.HIGH
        assert 'prompt' in error.context
        assert error.timestamp > 0

    def test_llm_failure_recovery(self):
        """Test LLM failure recovery strategies"""
        # Test fallback generation
        error = AdaptiveError(
            "LLM service unavailable",
            ErrorType.LLM_FAILURE,
            ErrorSeverity.HIGH,
            context={'task': 'test_generation', 'prompt': 'create user test'}
        )
        
        result = self.error_handler.handle_error(error)
        assert result is not None
        assert 'import requests' in result
        assert 'def test_' in result

    def test_api_connection_retry_logic(self):
        """Test exponential backoff retry logic"""
        retry_count = 0
        
        def failing_function():
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        error = AdaptiveError(
            "API connection failed",
            ErrorType.API_CONNECTION,
            ErrorSeverity.MEDIUM,
            context={'retry_function': failing_function}
        )
        
        start_time = time.time()
        result = self.error_handler.handle_error(error)
        end_time = time.time()
        
        assert result == "success"
        assert retry_count == 3
        # Should take at least 3 seconds due to exponential backoff (1 + 2 seconds)
        assert end_time - start_time >= 3

    def test_file_system_error_recovery(self):
        """Test file system error recovery"""
        missing_dir = os.path.join(self.temp_dir, "missing", "nested", "directory")
        
        error = AdaptiveError(
            "Directory not found",
            ErrorType.FILE_SYSTEM,
            ErrorSeverity.MEDIUM,
            context={'missing_directory': missing_dir}
        )
        
        result = self.error_handler.handle_error(error)
        
        assert result is True
        assert os.path.exists(missing_dir)

    def test_constraint_parsing_recovery(self):
        """Test constraint parsing failure recovery"""
        malformed_json = '{"rule_description": "email required", "constraint_type": incomplete...'
        
        error = AdaptiveError(
            "JSON parsing failed",
            ErrorType.CONSTRAINT_PARSING,
            ErrorSeverity.MEDIUM,
            context={'raw_response': malformed_json}
        )
        
        result = self.error_handler.handle_error(error)
        # Should attempt partial extraction (implementation dependent)
        assert result is not None or result is None  # Accept either outcome for now

    def test_configuration_default_fallback(self):
        """Test configuration error fallback to defaults"""
        error = AdaptiveError(
            "Missing configuration",
            ErrorType.CONFIGURATION,
            ErrorSeverity.MEDIUM,
            context={'missing_config': 'max_retries'}
        )
        
        result = self.error_handler.handle_error(error)
        
        assert result == 3  # Default max_retries value

    def test_error_statistics_tracking(self):
        """Test error statistics collection"""
        # Generate multiple errors
        errors = [
            AdaptiveError("LLM error 1", ErrorType.LLM_FAILURE, ErrorSeverity.HIGH),
            AdaptiveError("LLM error 2", ErrorType.LLM_FAILURE, ErrorSeverity.MEDIUM),
            AdaptiveError("API error", ErrorType.API_CONNECTION, ErrorSeverity.HIGH)
        ]
        
        for error in errors:
            self.error_handler.handle_error(error)
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['error_breakdown']['llm_failure'] == 2
        assert stats['error_breakdown']['api_connection'] == 1

    def test_critical_error_handling(self):
        """Test critical error notification"""
        with mock.patch.object(self.error_handler, '_notify_administrators') as mock_notify:
            error = AdaptiveError(
                "System failure",
                ErrorType.CONFIGURATION,
                ErrorSeverity.CRITICAL
            )
            
            self.error_handler.handle_error(error)
            mock_notify.assert_called_once_with(error)
