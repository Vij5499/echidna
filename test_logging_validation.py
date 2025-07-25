# Updated test_logging_validation.py
import logging
import tempfile
import os
import time
from error_handler import ErrorHandler, AdaptiveError, ErrorType, ErrorSeverity

def test_log_file_creation_and_content():
    """Test that logs are properly created and contain expected content"""
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, 'test_adaptive_agent.log')
    
    try:
        # Create a new logger specifically for this test
        test_logger = logging.getLogger('TestAdaptiveAgent')
        test_logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        for handler in test_logger.handlers[:]:
            handler.close()
            test_logger.removeHandler(handler)
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        test_logger.addHandler(file_handler)
        
        # Create error handler and replace its logger
        error_handler = ErrorHandler()
        error_handler.logger = test_logger
        
        # Generate test errors
        errors = [
            AdaptiveError("Test error 1", ErrorType.LLM_FAILURE, ErrorSeverity.HIGH),
            AdaptiveError("Test error 2", ErrorType.API_CONNECTION, ErrorSeverity.MEDIUM),
            AdaptiveError("Critical test error", ErrorType.CONFIGURATION, ErrorSeverity.CRITICAL)
        ]
        
        for error in errors:
            error_handler.handle_error(error)
        
        # CRITICAL: Properly close the file handler before reading
        file_handler.flush()
        file_handler.close()
        test_logger.removeHandler(file_handler)
        
        # Small delay to ensure file is released on Windows
        time.sleep(0.1)
        
        # Verify log file exists and contains expected content
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        assert "Test error 1" in log_content
        assert "Test error 2" in log_content
        assert "CRITICAL ERROR" in log_content
        assert "llm_failure" in log_content
        assert "api_connection" in log_content
        
    finally:
        # Clean up manually with better error handling
        try:
            if os.path.exists(log_file):
                os.unlink(log_file)
        except PermissionError:
            # On Windows, sometimes need to wait a bit longer
            time.sleep(0.5)
            try:
                os.unlink(log_file)
            except PermissionError:
                print(f"Warning: Could not delete log file {log_file}")
        
        try:
            os.rmdir(temp_dir)
        except OSError:
            # Directory might not be empty, that's okay
            import shutil
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                print(f"Warning: Could not delete temp directory {temp_dir}")

def test_error_statistics_collection():
    """Test that error statistics are properly collected"""
    error_handler = ErrorHandler()
    
    # Generate multiple errors
    errors = [
        AdaptiveError("LLM error 1", ErrorType.LLM_FAILURE, ErrorSeverity.HIGH),
        AdaptiveError("LLM error 2", ErrorType.LLM_FAILURE, ErrorSeverity.MEDIUM),
        AdaptiveError("API error", ErrorType.API_CONNECTION, ErrorSeverity.HIGH),
        AdaptiveError("Config error", ErrorType.CONFIGURATION, ErrorSeverity.LOW)
    ]
    
    for error in errors:
        error_handler.handle_error(error)
    
    stats = error_handler.get_error_statistics()
    
    assert stats['total_errors'] == 4
    assert stats['error_breakdown']['llm_failure'] == 2
    assert stats['error_breakdown']['api_connection'] == 1
    assert stats['error_breakdown']['configuration'] == 1

def test_log_handler_cleanup():
    """Test that log handlers are properly cleaned up"""
    # This test ensures we don't have lingering file handles
    test_logger = logging.getLogger('CleanupTestLogger')
    
    # Create and immediately close a handler
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    
    try:
        handler = logging.FileHandler(temp_file.name)
        test_logger.addHandler(handler)
        
        # Use the handler
        test_logger.info("Test message")
        
        # Clean up properly
        handler.flush()
        handler.close()
        test_logger.removeHandler(handler)
        
        # Should be able to delete the file now
        os.unlink(temp_file.name)
        
        # Test passes if we get here without exceptions
        assert True
        
    except Exception:
        # Clean up in case of failure
        try:
            os.unlink(temp_file.name)
        except:
            pass
        raise
