# Updated test_integration_failures.py
import pytest
import unittest.mock as mock
import tempfile
import os
from unittest.mock import patch, MagicMock
from main import main, load_spec_with_error_handling
from error_handler import ErrorHandler

class TestIntegrationFailures:
    
    def test_missing_spec_file_recovery(self):
        """Test system behavior when spec file is missing"""
        with patch.dict(os.environ, {'SPEC_PATH': 'nonexistent/spec.yaml'}):
            # Should not crash, should use fallback
            try:
                spec = load_spec_with_error_handling('nonexistent/spec.yaml')
                assert spec is not None  # Should return default spec
                
                # Check that we got a valid spec structure (even if default)
                assert isinstance(spec, dict)
                assert 'openapi' in spec or len(spec) == 0  # Either default spec or empty dict
                
                print("✅ Missing spec file handled gracefully")
                
            except Exception as e:
                pytest.fail(f"System crashed instead of graceful recovery: {e}")

    def test_llm_service_unavailable(self):
        """Test system behavior when LLM service is completely unavailable"""
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.side_effect = Exception("Service unavailable")
            
            with patch.dict(os.environ, {
                'SPEC_PATH': 'specs/spec_flawed.yaml',
                'MAX_ATTEMPTS': '2'
            }):
                try:
                    # Should not crash, should use fallback generation
                    main()
                    # If we reach here, the system handled the failure gracefully
                    assert True
                except SystemExit:
                    # Acceptable if system exits gracefully
                    assert True
                except Exception as e:
                    pytest.fail(f"System crashed: {e}")

    def test_mock_api_unavailable(self):
        """Test system behavior when mock API is not running"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Connection refused")
            
            with patch.dict(os.environ, {
                'SPEC_PATH': 'specs/spec_flawed.yaml',
                'MAX_ATTEMPTS': '2'
            }):
                try:
                    main()
                    # Should handle connection errors gracefully
                    assert True
                except Exception as e:
                    pytest.fail(f"System should handle API unavailability: {e}")

    def test_disk_full_scenario(self):
        """Test system behavior when disk is full (cannot write files)"""
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with patch.dict(os.environ, {'MAX_ATTEMPTS': '1'}):
                try:
                    main()
                    # Should handle file write failures gracefully
                    assert True
                except Exception as e:
                    pytest.fail(f"System should handle disk full scenario: {e}")

    def test_malformed_yaml_spec(self):
        """Test system behavior with malformed YAML specification"""
        malformed_yaml = """
        openapi: 3.0.0
        info:
          title: "Test API
          # Missing closing quote - malformed YAML
        paths:
          /users:
            post: {
        """
        
        # Use a more reliable approach for Windows
        import tempfile
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                temp_file = f.name
                f.write(malformed_yaml)
                f.flush()
            
            # File is now closed, should be accessible
            spec = load_spec_with_error_handling(temp_file)
            # Should return default spec or empty dict, not crash
            assert isinstance(spec, dict)
            
        except Exception as e:
            pytest.fail(f"Should handle malformed YAML gracefully: {e}")
        finally:
            # Clean up with better error handling
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except PermissionError:
                    # On Windows, sometimes files are locked briefly
                    import time
                    time.sleep(0.1)
                    try:
                        os.unlink(temp_file)
                    except PermissionError:
                        print(f"Warning: Could not delete temp file {temp_file}")

    def test_corrupted_constraint_model(self):
        """Test system behavior with corrupted constraint model data"""
        corrupted_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": "this should be a dict, not a string"  # Corrupted data
        }
        
        try:
            from constraint_model import APIConstraintModel
            model = APIConstraintModel(corrupted_spec)
            # Should either handle gracefully or raise a controlled error
            assert True
        except Exception as e:
            # Should be a controlled exception, not a system crash
            assert "constraint" in str(e).lower() or "model" in str(e).lower() or "dict" in str(e).lower()
