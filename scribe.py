from dotenv import load_dotenv
load_dotenv()

import os
import google.generativeai as genai
import json
import re
import threading
import time
from typing import Dict, Any, Optional

# Import actual constraint model classes
from constraint_model import APIConstraintModel, LearnedConstraint

def llm_call_with_timeout(model, prompt, timeout=60):
    """Call LLM with timeout using threading"""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = model.generate_content(prompt)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        # Thread is still running, timeout occurred
        raise TimeoutError(f"LLM request timed out after {timeout} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def _build_learned_rules_context(constraint_model: APIConstraintModel) -> str:
    """Build context string with learned constraints"""
    if not constraint_model or not getattr(constraint_model, 'learned_constraints', None):
        return ""
    
    context = "\n**LEARNED CONSTRAINTS (MUST FOLLOW):**\n"
    
    high_confidence_rules = [
        constraint for constraint in constraint_model.learned_constraints.values()
        if constraint.confidence_score > 0.7
    ]
    
    if not high_confidence_rules:
        return ""
    
    for constraint in high_confidence_rules:
        context += f"- {constraint.rule_description} (confidence: {constraint.confidence_score:.2f})\n"
        
        # Add specific implementation guidance
        if constraint.constraint_type.value == "required_field":
            context += f"  → MUST include '{constraint.affected_parameter}' in requests to {constraint.endpoint_path}\n"
        elif constraint.constraint_type.value == "format_validation":
            format_rule = constraint.formal_constraint.get('format', 'valid format')
            context += f"  → '{constraint.affected_parameter}' must follow {format_rule} format\n"
    
    context += "\n**IMPORTANT:** Violating these learned rules will cause test failures!\n"
    return context


def _extract_code_from_response(response_text: str) -> str:
    """Extract Python code from LLM response that may contain markdown code blocks using regex."""
    # Regex to find code block: ```python ... ``` or ``` ... ```
    code_pattern = re.compile(r"```(?:python\n)?(.*?)```", re.DOTALL)
    match = code_pattern.search(response_text)
    
    if match:
        return match.group(1).strip()
    else:
        # Fallback for when no code blocks are found
        return response_text.strip()


def _validate_code_completeness(script: str) -> Dict[str, Any]:
    """Validate that the generated script is complete and syntactically correct"""
    issues = []
    
    if not script:
        issues.append("Generated script is empty.")
        return {'is_complete': False, 'issues': issues}

    # Check for basic required elements more flexibly
    required_elements = ['import requests', 'import pytest', 'def test_', 'assert ', 'requests.']
    missing_elements = [elem for elem in required_elements if elem not in script]
    
    if missing_elements:
        issues.extend([f"Missing required element: {elem}" for elem in missing_elements])
    
    # Try to parse the script for syntax errors
    try:
        compile(script, '<generated_script>', 'exec')
    except SyntaxError as e:
        issues.append(f"Syntax error: {str(e)}")
    
    return {'is_complete': not issues, 'issues': issues}


def _complete_incomplete_script(incomplete_script: str, model) -> Optional[str]:
    """Attempt to complete an incomplete script using the LLM."""
    completion_prompt = f"""The following Python test script is incomplete or contains syntax errors. Please fix it and provide only the complete, corrected, and fully functional Python code.

**INCOMPLETE SCRIPT:**
```python
{incomplete_script}
```

**REQUIREMENTS:**
- Complete all unfinished lines (e.g., assignments, assertions).
- Ensure all function definitions are complete.
- Fix any syntax errors.
- Do not add any new logic, just complete the existing code.
- Return ONLY the raw Python code, without any markdown or explanations.
"""
    try:
        print("🔄 Attempting to complete the script...")
        response = llm_call_with_timeout(model, completion_prompt, 60)
        completed_script = _extract_code_from_response(response.text)
        
        validation = _validate_code_completeness(completed_script)
        if validation['is_complete']:
            print("✅ Successfully completed the incomplete script.")
            return completed_script
        else:
            print(f"❌ Completion attempt failed. Issues remain: {validation['issues']}")
            return None
    except Exception as e:
        print(f"❌ Error during script completion: {e}")
        return None


def _generate_enhanced_fallback_script(user_prompt: str, spec_data: Dict[str, Any]) -> str:
    """Generate a comprehensive fallback script with complete assertions."""
    required_fields = ['name', 'username'] 
    if 'paths' in spec_data:
        for path, methods in spec_data['paths'].items():
            if '/users' in path and 'post' in methods:
                schema = methods.get('post', {}).get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {})
                if 'required' in schema:
                    required_fields = schema['required']
                    break
    
    user_data_lines = []
    default_values = {'name': '"John Doe"', 'username': '"johndoe"', 'email': '"john.doe@example.com"'}
    for field in required_fields:
        value = default_values.get(field, '"default_value"')
        user_data_lines.append(f'        "{field}": {value},')
    
    if user_data_lines:
        user_data_lines[-1] = user_data_lines[-1].rstrip(',')
    
    user_data_block = '\n'.join(user_data_lines)
    
    return f'''import requests
import pytest

def test_create_user_fallback(api_base_url):
    """
    Enhanced fallback test for: {user_prompt}
    Generated due to an unrecoverable LLM error.
    """
    user_data = {{
{user_data_block}
    }}
    
    response = requests.post(f"{{api_base_url}}/users", json=user_data)
    assert response.status_code == 201, f"Expected 201, got {{response.status_code}}: {{response.text}}"
    
    try:
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a JSON object"
        assert "id" in response_data, "Response must include an 'id' field"
        print(f"✅ Fallback user created successfully: {{response_data}}")
    except ValueError:
        pytest.fail(f"Response is not valid JSON. Text: {{response.text}}")
    except AssertionError as e:
        pytest.fail(f"Response validation failed: {{e}}")
'''


def generate_test_script(spec_data: Dict[str, Any], user_prompt: str, constraint_model: Optional[APIConstraintModel] = None) -> Dict[str, Any]:
    """Generate a test script with awareness of learned constraints and complete code validation."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        # Fallback gracefully if API key is missing
        print("❌ GOOGLE_API_KEY not set. Generating fallback script.")
        return {
            'script': _generate_enhanced_fallback_script(user_prompt, spec_data),
            'user_prompt': user_prompt,
            'enhanced_spec_used': False,
            'error': "GOOGLE_API_KEY environment variable not set or found.",
            'completion_status': 'fallback'
        }

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    enhanced_spec = spec_data
    learned_rules_context = ""
    
    if constraint_model:
        enhanced_spec = constraint_model.get_enhanced_schema()
        learned_rules_context = _build_learned_rules_context(constraint_model)

    prompt_template = """You are an expert Python test script generator. Your task is to generate a single, complete, and fully-formed pytest test script based on the provided API specification and user requirement.

**API SPECIFICATION:**
{spec}

**USER REQUIREMENT:**
{requirement}
{rules_context}

**CRITICAL REQUIREMENTS:**
1.  **Generate COMPLETE Python code.** Do not truncate or leave any part of the script unfinished.
2.  **Syntax must be perfect.** The script must be ready to execute without any modifications.
3.  **Use `requests` and `pytest`.** Include all necessary imports.
4.  **Use the `api_base_url` fixture** for the base URL.
5.  **Include comprehensive assertions** to validate status codes, and key fields in the JSON response (e.g., `id`, `name`, `email`). Provide meaningful error messages in assertions.

**EXAMPLE OF A PERFECT SCRIPT:**
```python
import requests
import pytest

def test_create_user_example(api_base_url):
    user_data = {{
        "name": "Jane Doe",
        "username": "janedoe",
        "email": "jane.doe@example.com"
    }}
    response = requests.post(f"{{api_base_url}}/users", json=user_data)
    assert response.status_code == 201, f"Expected status code 201, but got {{response.status_code}}. Response: {{response.text}}"
    
    response_data = response.json()
    assert "id" in response_data, "The response JSON must include a user 'id'."
    assert response_data.get("name") == user_data["name"], "The 'name' in the response should match the request."
    print(f"✅ User created successfully with ID: {{response_data.get('id')}}")
```

**YOUR TASK:**
Now, generate the Python code for the user requirement. Return ONLY the raw Python code inside a single markdown block.
"""
    
    prompt = prompt_template.format(
        spec=json.dumps(enhanced_spec, indent=2),
        requirement=user_prompt,
        rules_context=learned_rules_context
    )
    
    try:
        print("🤖 Generating test script...")
        generation_config = {
            "max_output_tokens": 4096,
            "temperature": 0.1,
        }
        
        response = llm_call_with_timeout(model, prompt, 90)  # 90 second timeout
        generated_script = _extract_code_from_response(response.text)
        
        validation_result = _validate_code_completeness(generated_script)
        if not validation_result['is_complete']:
            print(f"❌ Generated script is incomplete: {validation_result['issues']}")
            completed_script = _complete_incomplete_script(generated_script, model)
            if completed_script:
                generated_script = completed_script
            else:
                # Corrected: Gracefully use fallback instead of raising an error
                print("❌ Could not complete script, using fallback.")
                generated_script = _generate_enhanced_fallback_script(user_prompt, enhanced_spec)
        
        print("✅ Final script generated successfully.")
        # Corrected: Return dictionary now includes all required keys
        return {
            'script': generated_script,
            'user_prompt': user_prompt,
            'enhanced_spec_used': constraint_model is not None,
            'completion_status': 'complete'
        }
    
    except Exception as e:
        print(f"❌ An error occurred during script generation: {e}. Using fallback.")
        return {
            'script': _generate_enhanced_fallback_script(user_prompt, enhanced_spec),
            'user_prompt': user_prompt,
            'enhanced_spec_used': False,
            'error': str(e),
            'completion_status': 'fallback'
        }
