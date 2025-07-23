import subprocess
import os

def run_test(script_content: str, file_name: str) -> tuple[bool, str, str]:
    """
    Saves a script to a file and runs it with pytest.
    Returns a tuple of (success_status, stdout, stderr).
    """
    
    # Save the generated script to a temporary file
    with open(file_name, "w") as f:
        f.write(script_content)

    print(f"\n--- Running generated test: {file_name} ---")
    
    # Execute pytest using a subprocess to run it in the shell
    result = subprocess.run(
        ["pytest", file_name, "-v"],
        capture_output=True,
        text=True
    )

    # Clean up the temporary file after execution
    os.remove(file_name)

    # Pytest returns exit code 0 for success, anything else is a failure
    success = result.returncode == 0
    return success, result.stdout, result.stderr