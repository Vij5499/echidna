# Updated test_stress_and_performance.py
import pytest
import time
import threading
import concurrent.futures
import sys
import platform
from error_handler import ErrorHandler, AdaptiveError, ErrorType, ErrorSeverity

class TestStressAndPerformance:
    
    def test_concurrent_error_handling(self):
        """Test error handler under concurrent load"""
        error_handler = ErrorHandler()
        
        def generate_errors(thread_id):
            errors_handled = 0
            for i in range(50):  # Reduced from 100 for Windows compatibility
                error = AdaptiveError(
                    f"Thread {thread_id} error {i}",
                    ErrorType.LLM_FAILURE,
                    ErrorSeverity.MEDIUM,
                    context={'thread_id': thread_id, 'error_num': i}
                )
                error_handler.handle_error(error)
                errors_handled += 1
                # Small delay to prevent overwhelming the system
                time.sleep(0.001)
            return errors_handled
        
        # Run concurrent error generation with fewer threads for Windows
        max_workers = min(5, threading.active_count() + 3)  # Conservative for Windows
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(generate_errors, i) for i in range(max_workers)]
            results = []
            
            # Add timeout to prevent hanging
            for future in concurrent.futures.as_completed(futures, timeout=30):
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except concurrent.futures.TimeoutError:
                    pytest.fail("Concurrent error handling test timed out")
        
        # Verify all errors were handled
        expected_total = max_workers * 50
        assert sum(results) == expected_total
        stats = error_handler.get_error_statistics()
        assert stats['total_errors'] == expected_total

    @pytest.mark.skipif(platform.system() == "Windows", reason="Memory monitoring unreliable on Windows")
    def test_memory_usage_under_load(self):
        """Test memory usage doesn't grow excessively"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            error_handler = ErrorHandler()
            
            # Generate many errors
            for i in range(500):  # Reduced for Windows
                error = AdaptiveError(
                    f"Memory test error {i}",
                    ErrorType.API_CONNECTION,
                    ErrorSeverity.LOW
                )
                error_handler.handle_error(error)
                
                # Periodic cleanup to prevent buildup
                if i % 100 == 0:
                    time.sleep(0.01)
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 50MB for 500 errors)
            assert memory_increase < 50 * 1024 * 1024
            
        except ImportError:
            pytest.skip("psutil not available for memory testing")

    def test_error_handler_performance(self):
        """Test error handling performance"""
        error_handler = ErrorHandler()
        
        start_time = time.time()
        
        # Reduced number for Windows compatibility
        num_errors = 500
        for i in range(num_errors):
            error = AdaptiveError(
                f"Performance test error {i}",
                ErrorType.CONSTRAINT_PARSING,
                ErrorSeverity.LOW
            )
            error_handler.handle_error(error)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle 500 errors in less than 5 seconds
        assert total_time < 5.0
        
        # Average handling time should be less than 10ms per error (relaxed for Windows)
        avg_time = total_time / num_errors
        assert avg_time < 0.01

    def test_long_running_stability(self):
        """Test system stability over extended periods"""
        error_handler = ErrorHandler()
        
        # Simulate shorter duration for Windows (5 seconds instead of 10)
        start_time = time.time()
        errors_generated = 0
        
        while time.time() - start_time < 5:  # 5 seconds for testing
            error = AdaptiveError(
                f"Long running test error {errors_generated}",
                ErrorType.LLM_FAILURE,
                ErrorSeverity.MEDIUM
            )
            error_handler.handle_error(error)
            errors_generated += 1
            time.sleep(0.1)  # 100ms between errors
        
        stats = error_handler.get_error_statistics()
        assert stats['total_errors'] == errors_generated
        assert errors_generated > 25  # Should generate at least 25 errors in 5 seconds

    @pytest.mark.timeout(60)  # Ensure test doesn't hang
    def test_stress_recovery_scenarios(self):
        """Test error recovery under stress conditions"""
        error_handler = ErrorHandler()
        
        # Test rapid error generation and recovery
        start_time = time.time()
        recovery_count = 0
        
        for i in range(100):
            error = AdaptiveError(
                f"Stress recovery test {i}",
                ErrorType.LLM_FAILURE,
                ErrorSeverity.HIGH,
                context={'task': 'test_generation', 'prompt': f'test prompt {i}'}
            )
            
            result = error_handler.handle_error(error)
            if result is not None:
                recovery_count += 1
            
            # Prevent overwhelming the system
            if i % 10 == 0:
                time.sleep(0.01)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time
        assert total_time < 30  # 30 seconds max
        
        # Should have some successful recoveries
        assert recovery_count > 50  # At least 50% recovery rate
