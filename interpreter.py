from dotenv import load_dotenv
load_dotenv()

import os
import google.generativeai as genai
import threading
import time
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
import json
import re
from constraint_model import (
    LearnedConstraint, ConstraintType, ConditionalRule, 
    MutualExclusivityRule, FormatDependencyRule, BusinessRule, RateLimitRule
)

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

class EnhancedInferredRule(BaseModel):
    rule_description: str = Field(description="Clear description of the inferred API rule")
    constraint_type: str = Field(description="Type: required_field, conditional_requirement, mutual_exclusivity, format_dependency, business_rule, rate_limiting")
    affected_parameter: str = Field(description="The primary parameter this rule affects")
    endpoint_path: str = Field(description="The API endpoint this rule applies to")
    formal_constraint: Dict[str, Any] = Field(description="Machine-readable constraint definition")
    confidence: float = Field(description="Confidence in this rule (0.0 to 1.0)", default=0.8)
    is_learnable: bool = Field(description="Whether this rule can be applied to future tests", default=True)
    
    # Enhanced constraint details
    conditional_logic: Optional[Dict[str, Any]] = Field(description="Conditional logic if applicable", default=None)
    exclusivity_info: Optional[Dict[str, Any]] = Field(description="Mutual exclusivity information", default=None)
    format_dependency: Optional[Dict[str, Any]] = Field(description="Format dependency details", default=None)
    business_rule_info: Optional[Dict[str, Any]] = Field(description="Business rule specifics", default=None)
    rate_limit_info: Optional[Dict[str, Any]] = Field(description="Rate limiting details", default=None)

def interpret_failure(user_prompt: str, failed_script: str, request_details: Dict[str, Any], failure_context_path: str) -> Optional[LearnedConstraint]:
    """
    Enhanced failure interpretation that extracts sophisticated constraints
    """
    
    print(f"🔍 DEBUG: Starting enhanced failure analysis...")
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
        print("❌ No analyzable error message found")
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
    
    # Create enhanced analysis prompt for sophisticated constraint detection
    prompt = f"""
    You are an expert API constraint analyst. Analyze this API test failure and extract a specific, sophisticated constraint rule.

    **CONTEXT:**
    User Goal: {user_prompt}
    
    **REQUEST DETAILS:**
    HTTP Method: {http_method}
    Endpoint: {endpoint_path}
    Request Data: {json.dumps(request_details.get('request_body', {}), indent=2)}
    
    **FAILURE DETAILS:**
    HTTP Status: {status_code}
    Error Message: {error_message}
    
    **ANALYSIS TASK:**
    Based on the error message, determine what type of sophisticated constraint was violated:

    1. **CONDITIONAL REQUIREMENT**: "if field A has value X, then field B is required"
       - Example: "billing_address required when payment_method is 'credit_card'"
       
    2. **MUTUAL EXCLUSIVITY**: "only one of these fields can be present"
       - Example: "Cannot specify both email and phone, choose one"
       
    3. **FORMAT DEPENDENCY**: "field format depends on another field's value"
       - Example: "email format required when contact_type is 'email'"
       
    4. **BUSINESS RULE**: "value must meet business logic constraints"
       - Example: "price must be greater than 0", "age must be at least 18"
       
    5. **RATE LIMITING**: "too many requests in time window"
       - Example: "Rate limit exceeded: max 100 requests per minute"
       
    6. **SIMPLE REQUIRED FIELD**: "field is always required"
       - Example: "name field is required"

    **CONSTRAINT PATTERN ANALYSIS:**
    Look for these patterns in the error message:
    - "when X is Y, Z is required" → CONDITIONAL_REQUIREMENT
    - "only one of", "cannot specify both" → MUTUAL_EXCLUSIVITY  
    - "invalid format when", "must be valid X when Y" → FORMAT_DEPENDENCY
    - "must be greater than", "invalid value", "range" → BUSINESS_RULE
    - "rate limit", "too many requests", "quota exceeded" → RATE_LIMITING
    - "field is required", "missing required" → REQUIRED_FIELD

    **OUTPUT FORMAT:**
    Return a JSON object with this structure:
    {{
        "rule_description": "Detailed rule description",
        "constraint_type": "conditional_requirement|mutual_exclusivity|format_dependency|business_rule|rate_limiting|required_field",
        "affected_parameter": "primary_field_name",
        "endpoint_path": "{endpoint_path}",
        "formal_constraint": {{"specific": "constraint_details"}},
        "confidence": 0.9,
        "is_learnable": true,
        
        // Include ONE of these based on constraint_type:
        "conditional_logic": {{
            "condition_field": "field_name",
            "condition_operator": "equals|not_equals|greater_than|less_than|contains",
            "condition_value": "value",
            "required_field": "field_name",
            "required_value": "value_or_null"
        }},
        
        "exclusivity_info": {{
            "exclusive_fields": ["field1", "field2"],
            "min_required": 1,
            "max_allowed": 1
        }},
        
        "format_dependency": {{
            "dependent_field": "field_name",
            "dependency_field": "other_field",
            "dependency_value": "trigger_value",
            "required_format": "email|url|phone|date|uuid"
        }},
        
        "business_rule_info": {{
            "field": "field_name",
            "rule_type": "min_value|max_value|range|pattern|custom",
            "constraint_value": "constraint_details",
            "error_message": "business_error_message"
        }},
        
        "rate_limit_info": {{
            "endpoint_pattern": "endpoint_pattern",
            "max_requests": 100,
            "time_window_seconds": 60,
            "scope": "per_user|per_ip|global"
        }}
    }}
    
    **IMPORTANT:** 
    - Only include the constraint type that matches the error
    - Be specific about field names and values
    - Extract exact constraint parameters from the error message
    """
    
    try:
        print("🤖 Sending enhanced prompt to Gemini...")
        response = llm_call_with_timeout(model, prompt, 60)  # 60 second timeout
        
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
        inferred_rule = EnhancedInferredRule(**inferred_data)
        
        if not inferred_rule.is_learnable:
            print(f"⚠️ Rule not learnable: {inferred_rule.rule_description}")
            return None
        
        # Convert to LearnedConstraint with enhanced data
        try:
            constraint_type = ConstraintType(inferred_rule.constraint_type)
        except ValueError:
            print(f"❌ Invalid constraint type: {inferred_rule.constraint_type}")
            return None
        
        # Create the base constraint
        learned_constraint = LearnedConstraint(
            constraint_type=constraint_type,
            affected_parameter=inferred_rule.affected_parameter,
            endpoint_path=inferred_rule.endpoint_path,
            rule_description=inferred_rule.rule_description,
            formal_constraint=inferred_rule.formal_constraint,
            confidence_score=inferred_rule.confidence
        )
        
        # Add sophisticated constraint details based on type
        if constraint_type == ConstraintType.CONDITIONAL_REQUIREMENT and inferred_rule.conditional_logic:
            learned_constraint.conditional_rule = ConditionalRule(
                condition_field=inferred_rule.conditional_logic['condition_field'],
                condition_value=inferred_rule.conditional_logic['condition_value'],
                condition_operator=inferred_rule.conditional_logic['condition_operator'],
                required_field=inferred_rule.conditional_logic['required_field'],
                required_value=inferred_rule.conditional_logic.get('required_value')
            )
        
        elif constraint_type == ConstraintType.MUTUAL_EXCLUSIVITY and inferred_rule.exclusivity_info:
            learned_constraint.exclusivity_rule = MutualExclusivityRule(
                exclusive_fields=inferred_rule.exclusivity_info['exclusive_fields'],
                min_required=inferred_rule.exclusivity_info.get('min_required', 1),
                max_allowed=inferred_rule.exclusivity_info.get('max_allowed', 1)
            )
        
        elif constraint_type == ConstraintType.FORMAT_DEPENDENCY and inferred_rule.format_dependency:
            learned_constraint.format_dependency = FormatDependencyRule(
                dependent_field=inferred_rule.format_dependency['dependent_field'],
                dependency_field=inferred_rule.format_dependency['dependency_field'],
                dependency_value=inferred_rule.format_dependency['dependency_value'],
                required_format=inferred_rule.format_dependency['required_format']
            )
        
        elif constraint_type == ConstraintType.BUSINESS_RULE and inferred_rule.business_rule_info:
            learned_constraint.business_rule = BusinessRule(
                field=inferred_rule.business_rule_info['field'],
                rule_type=inferred_rule.business_rule_info['rule_type'],
                constraint_value=inferred_rule.business_rule_info['constraint_value'],
                error_message=inferred_rule.business_rule_info.get('error_message', 'Business rule violation')
            )
        
        elif constraint_type == ConstraintType.RATE_LIMITING and inferred_rule.rate_limit_info:
            learned_constraint.rate_limit_rule = RateLimitRule(
                endpoint_pattern=inferred_rule.rate_limit_info['endpoint_pattern'],
                max_requests=inferred_rule.rate_limit_info['max_requests'],
                time_window_seconds=inferred_rule.rate_limit_info['time_window_seconds'],
                scope=inferred_rule.rate_limit_info.get('scope', 'per_user')
            )
        
        print(f"✅ Successfully created enhanced learned constraint: {learned_constraint.rule_description}")
        print(f"   🎯 Constraint Type: {constraint_type.value}")
        
        if learned_constraint.conditional_rule:
            print(f"   🔀 Conditional: if {learned_constraint.conditional_rule.condition_field} {learned_constraint.conditional_rule.condition_operator} {learned_constraint.conditional_rule.condition_value}, then {learned_constraint.conditional_rule.required_field} required")
        
        return learned_constraint
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error during enhanced failure interpretation: {e}")
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
