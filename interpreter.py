from dotenv import load_dotenv
load_dotenv()

import os
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import json
import re
from constraint_model import LearnedConstraint, ConstraintType

class InferredRule(BaseModel):
    rule_description: str = Field(description="Clear description of the inferred API rule")
    constraint_type: str = Field(description="Type: required_field, format_validation, dependency_rule, value_constraint")
    affected_parameter: str = Field(description="The parameter this rule affects")
    endpoint_path: str = Field(description="The API endpoint this rule applies to")
    formal_constraint: Dict[str, Any] = Field(description="Machine-readable constraint definition")
    confidence: float = Field(description="Confidence in this rule (0.0 to 1.0)", default=0.8)
    is_learnable: bool = Field(description="Whether this rule can be applied to future tests", default=True)

def interpret_failure(user_prompt: str, failed_script: str, request_details: Dict[str, Any], failure_context_path: str) -> Optional[LearnedConstraint]:
    """
    Enhanced failure interpretation that extracts structured constraints
    """
    
    print(f"🔍 DEBUG: Starting failure analysis...")
    print(f"   Failure file: {failure_context_path}")
    
    # Read failure details
    try:
        with open(failure_context_path, 'r') as f:
            failure_output = f.read()
        print(f"✅ Successfully read failure output ({len(failure_output)} chars)")
    except FileNotFoundError:
        print(f"❌ Failure context file not found: {failure_context_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading failure file: {e}")
        return None

    print(f"🔍 DEBUG: Failure output preview:")
    print("=" * 50)
    print(failure_output[:1000])  # Show first 1000 characters
    print("=" * 50)
    
    # Extract HTTP request and response details
    http_method, endpoint_path, status_code, error_message = _extract_failure_details(failure_output, failed_script)
    
    print(f"🔍 DEBUG: Extracted details:")
    print(f"   Method: {http_method}")
    print(f"   Endpoint: {endpoint_path}")
    print(f"   Status: {status_code}")
    print(f"   Error: {error_message}")
    
    if not error_message:
        print("❌ No analyzable error message found - trying alternative extraction...")
        error_message = _alternative_error_extraction(failure_output)
        print(f"🔍 Alternative extraction result: {error_message}")
    
    if not error_message:
        print("❌ Still no error message found after all attempts")
        print("🔍 Full failure output for manual inspection:")
        print(failure_output)
        return None
    
    # Only proceed with 4xx errors (client errors)
    if status_code and not status_code.startswith('4'):
        print(f"⚠️ Skipping non-client error (status: {status_code})")
        return None
    
    print(f"✅ Found analyzable error message: {error_message}")
    
    # Configure Gemini
    try:
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini configured successfully")
    except Exception as e:
        print(f"❌ Error configuring Gemini: {e}")
        return None
    
    # Create enhanced analysis prompt
    prompt = f"""
    You are an expert API testing analyst. Analyze this API test failure and extract a specific, actionable rule.

    **CONTEXT:**
    User Goal: {user_prompt}
    
    **REQUEST DETAILS:**
    HTTP Method: {http_method}
    Endpoint: {endpoint_path}
    Request Data: {request_details.get('request_body', 'N/A')}
    
    **FAILURE DETAILS:**
    HTTP Status: {status_code}
    Error Message: {error_message}
    
    **ANALYSIS TASK:**
    Based on the error message "{error_message}", determine what API constraint was violated.
    
    Common patterns:
    - "Missing required fields" or "field is required" → required_field constraint
    - "invalid format" → format_validation constraint  
    - "must be X when Y" → dependency_rule constraint
    - "value must be between" → value_constraint
    
    **OUTPUT FORMAT:**
    Return a JSON object with this exact structure:
    {{
        "rule_description": "Specific rule description (e.g., 'email field is required for POST /users')",
        "constraint_type": "required_field",
        "affected_parameter": "email",
        "endpoint_path": "{endpoint_path}",
        "formal_constraint": {{"required": true}},
        "confidence": 0.9,
        "is_learnable": true
    }}
    
    **IMPORTANT:** 
    - Only analyze client errors (4xx). 
    - Return {{"is_learnable": false}} for connection errors, server errors, or unclear failures.
    - Be specific about the parameter name and constraint type.
    - If the error mentions multiple missing fields, focus on one that's not in the original request.
    """
    
    try:
        print("🤖 Sending prompt to Gemini...")
        response = model.generate_content(prompt)
        
        print(f"🤖 LLM Response received ({len(response.text)} chars):")
        print("=" * 30)
        print(response.text[:500])
        print("=" * 30)
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if not json_match:
            print("❌ No JSON found in LLM response")
            return None
            
        json_str = json_match.group()
        print(f"🔍 Extracted JSON: {json_str}")
        
        inferred_data = json.loads(json_str)
        
        # Validate the inferred rule
        inferred_rule = InferredRule(**inferred_data)
        
        if not inferred_rule.is_learnable:
            print(f"⚠️ Rule not learnable: {inferred_rule.rule_description}")
            return None
        
        # Convert to LearnedConstraint
        try:
            constraint_type = ConstraintType(inferred_rule.constraint_type)
        except ValueError:
            print(f"❌ Invalid constraint type: {inferred_rule.constraint_type}")
            return None
        
        learned_constraint = LearnedConstraint(
            constraint_type=constraint_type,
            affected_parameter=inferred_rule.affected_parameter,
            endpoint_path=inferred_rule.endpoint_path,
            rule_description=inferred_rule.rule_description,
            formal_constraint=inferred_rule.formal_constraint,
            confidence_score=inferred_rule.confidence
        )
        
        print(f"✅ Successfully created learned constraint: {learned_constraint.rule_description}")
        return learned_constraint
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error during failure interpretation: {e}")
        return None

def _extract_failure_details(failure_output: str, failed_script: str) -> tuple:
    """Extract HTTP method, endpoint, status code, and error message from failure output"""
    
    print("🔍 Starting detail extraction...")
    
    # Extract HTTP method and endpoint from script
    http_method = "POST"  # Default
    endpoint_path = "/users"  # Default
    
    # Look for requests.post, requests.get, etc. in the script
    method_match = re.search(r'requests\.(get|post|put|patch|delete)', failed_script)
    if method_match:
        http_method = method_match.group(1).upper()
        print(f"   Found method: {http_method}")
    
    # Look for endpoint in URL
    url_matches = [
        re.search(r'f?["\'].*?/([\w/\-]+)["\']', failed_script),
        re.search(r'/users', failed_script),
        re.search(r'api_base_url.*?["\']/([\w/\-]+)["\']', failed_script)
    ]
    
    for match in url_matches:
        if match:
            if hasattr(match, 'group') and len(match.groups()) > 0:
                endpoint_path = "/" + match.group(1)
            else:
                endpoint_path = "/users"  # fallback
            print(f"   Found endpoint: {endpoint_path}")
            break
    
    # Extract status code - FIXED: Look for the actual response status, not expected status
    status_code = None
    status_patterns = [
        r'got\s+(\d{3})',  # "got 400" - This should be first priority
        r'AssertionError.*?got\s+(\d{3})',  # AssertionError with got status
        r'<Response\s*\[(\d{3})',  # <Response [400
        r'status_code.*?(\d{3}).*?{',  # status_code: 400 followed by error JSON
        r'Expected.*?got\s+(\d{3})',  # Expected 201, got 400
    ]
    
    for pattern in status_patterns:
        match = re.search(pattern, failure_output)
        if match:
            status_code = match.group(1)
            print(f"   Found status code: {status_code}")
            break
    
    # Extract error message with multiple strategies
    error_message = None
    
    # Strategy 1: JSON error messages
    json_patterns = [
        r'"error":\s*"([^"]*)"',  # "error": "message"
        r"'error':\s*'([^']*)'",  # 'error': 'message'
        r'\{[^}]*"(?:error|message|detail)":\s*"([^"]*)"[^}]*\}',  # Full JSON
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, failure_output, re.IGNORECASE)
        if match:
            error_message = match.group(1)
            print(f"   Found JSON error: {error_message}")
            break
    
    # Strategy 2: AssertionError messages
    if not error_message:
        assert_patterns = [
            r'AssertionError:\s*(.+?)(?:\n|$)',
            r'assert\s+.*?,\s*f?"([^"]*)"',
            r'AssertionError.*?:\s*(.+)'
        ]
        
        for pattern in assert_patterns:
            match = re.search(pattern, failure_output)
            if match:
                error_message = match.group(1).strip()
                print(f"   Found assertion error: {error_message}")
                break
    
    print(f"🔍 Final extracted details: {http_method}, {endpoint_path}, {status_code}, {error_message}")
    return http_method, endpoint_path, status_code, error_message

    
    print(f"🔍 Final extracted details: {http_method}, {endpoint_path}, {status_code}, {error_message}")
    return http_method, endpoint_path, status_code, error_message

def _alternative_error_extraction(failure_output: str) -> Optional[str]:
    """Alternative error extraction for edge cases"""
    
    print("🔍 Trying alternative error extraction...")
    
    # Look for any quoted error-like strings
    error_patterns = [
        r'"([^"]*(?:required|missing|invalid|must|cannot|expected)[^"]*)"',
        r"'([^']*(?:required|missing|invalid|must|cannot|expected)[^']*)'",
        r'Error:\s*(.+?)(?:\n|$)',
        r'Exception:\s*(.+?)(?:\n|$)',
        r'FAILED.*?-\s*(.+?)(?:\n|$)',
        r'(\w+Error: .+?)(?:\n|$)'
    ]
    
    for i, pattern in enumerate(error_patterns):
        match = re.search(pattern, failure_output, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            print(f"   Alternative pattern {i+1} found: {result}")
            return result
    
    print("   No alternative patterns matched")
    return None
