import subprocess
import os
import tempfile
from typing import Dict, Any

def execute_test_script(script_file: str) -> Dict[str, Any]:
    """
    Execute a pytest script and return the results
    """
    
    # Check if the script file exists
    if not os.path.exists(script_file):
        return {
            'success': False,
            'output_file': None,
            'error': f"Script file not found: {script_file}",
            'stdout': '',
            'stderr': ''
        }
    
    # Create a temporary file to capture the output
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
        output_file = temp_file.name
    
    try:
        # Create conftest.py if it doesn't exist (for the api_base_url fixture)
        conftest_content = '''
import pytest

@pytest.fixture
def api_base_url():
    return "http://localhost:5000"
'''
        
        if not os.path.exists('conftest.py'):
            with open('conftest.py', 'w') as f:
                f.write(conftest_content)
        
        # Execute the pytest script
        result = subprocess.run(
            ['python', '-m', 'pytest', script_file, '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        # Write output to the temporary file
        with open(output_file, 'w') as f:
            f.write("=== PYTEST EXECUTION RESULTS ===\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write("=== STDOUT ===\n")
            f.write(result.stdout)
            f.write("\n=== STDERR ===\n")
            f.write(result.stderr)
            f.write("\n=== END RESULTS ===\n")
        
        # Determine if the test was successful
        success = result.returncode == 0
        
        return {
            'success': success,
            'output_file': output_file,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        # Handle timeout
        with open(output_file, 'w') as f:
            f.write("=== TIMEOUT ERROR ===\n")
            f.write("Test execution timed out after 30 seconds\n")
        
        return {
            'success': False,
            'output_file': output_file,
            'error': 'Test execution timed out',
            'stdout': '',
            'stderr': 'Timeout after 30 seconds'
        }
        
    except Exception as e:
        # Handle other execution errors
        with open(output_file, 'w') as f:
            f.write("=== EXECUTION ERROR ===\n")
            f.write(f"Error executing test: {str(e)}\n")
        
        return {
            'success': False,
            'output_file': output_file,
            'error': str(e),
            'stdout': '',
            'stderr': str(e)
        }

def cleanup_temp_files(file_pattern: str = "generated_test_*.py"):
    """
    Clean up temporary test files
    """
    import glob
    
    files_to_remove = glob.glob(file_pattern)
    for file_path in files_to_remove:
        try:
            os.remove(file_path)
            print(f"Cleaned up: {file_path}")
        except OSError as e:
            print(f"Error removing {file_path}: {e}")

def setup_test_environment():
    """
    Setup the test environment with necessary fixtures
    """
    conftest_content = '''
import pytest
import requests

@pytest.fixture
def api_base_url():
    """Base URL for the API under test"""
    return "http://localhost:5000"

@pytest.fixture
def api_client(api_base_url):
    """HTTP client configured for the API"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
        
        def get(self, path, **kwargs):
            return requests.get(f"{self.base_url}{path}", **kwargs)
        
        def post(self, path, **kwargs):
            return requests.post(f"{self.base_url}{path}", **kwargs)
        
        def put(self, path, **kwargs):
            return requests.put(f"{self.base_url}{path}", **kwargs)
        
        def delete(self, path, **kwargs):
            return requests.delete(f"{self.base_url}{path}", **kwargs)
    
    return APIClient(api_base_url)
'''
    
    with open('conftest.py', 'w') as f:
        f.write(conftest_content)
    
    print("✅ Test environment setup complete")

if __name__ == "__main__":
    # Test the executor with a simple script
    test_script = '''
import requests
import pytest

def test_simple_request(api_base_url):
    """Simple test to verify executor works"""
    response = requests.get(f"{api_base_url}/")
    print(f"Response status: {response.status_code}")
    assert True  # Always pass for testing
'''
    
    # Write test script
    with open('test_executor.py', 'w') as f:
        f.write(test_script)
    
    # Setup environment
    setup_test_environment()
    
    # Execute test
    result = execute_test_script('test_executor.py')
    
    print("Execution Result:")
    print(f"Success: {result['success']}")
    print(f"Output file: {result['output_file']}")
    
    if result['output_file'] and os.path.exists(result['output_file']):
        with open(result['output_file'], 'r') as f:
            print("Output:")
            print(f.read())
    
    # Cleanup
    cleanup_temp_files("test_executor.py")
    if result['output_file']:
        os.remove(result['output_file'])
