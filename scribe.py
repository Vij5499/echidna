from dotenv import load_dotenv
load_dotenv()

import os
import google.generativeai as genai
import json
import re
from typing import Dict, Any, List, Optional
from constraint_model import APIConstraintModel, LearnedConstraint

def _extract_code_from_response(response_text: str) -> str:
    """Extract Python code from LLM response that may contain markdown code blocks"""
    print(f"🔍 DEBUG: Extracting code from response ({len(response_text)} chars)")
    print(f"   First 200 chars: {response_text[:200]}")
    
    # Define the code block marker by constructing it safely
    triple_backtick = "`" * 3
    
    if triple_backtick in response_text:
        print("   Found code block markers")
        # Split by code block markers
        parts = response_text.split(triple_backtick)
        
        # Look for python code block (parts come in pairs: before_code, code, after_code)
        for i in range(1, len(parts), 2):  # Check odd indices which contain code
            prev_part = parts[i-1] if i > 0 else ""
            code_content = parts[i]
            
            print(f"   Checking code block {i}: prev='{prev_part[-50:]}' code_start='{code_content[:50]}'")
            
            # Clean the code content - REMOVE THE "python" PREFIX
            clean_code = code_content.strip()
            
            # Remove "python" if it's at the start of the code block
            if clean_code.startswith('python\n'):
                clean_code = clean_code[7:]  # Remove "python\n"
            elif clean_code.startswith('python '):
                clean_code = clean_code[7:]  # Remove "python "
            elif clean_code.startswith('python'):
                # Check if next character is not alphanumeric (likely end of "python" keyword)
                if len(clean_code) > 6 and not clean_code[6].isalnum():
                    clean_code = clean_code[6:]
            
            # Further clean any remaining whitespace
            clean_code = clean_code.strip()
            
            # Check if this looks like Python code
            if ("import" in clean_code and "def test_" in clean_code) or i == 1:
                print(f"   Selected code block: {len(clean_code)} chars")
                print(f"   Code starts with: {clean_code[:100]}")
                return clean_code
        
        # If no python block found, return the first code block (cleaned)
        if len(parts) >= 3:
            clean_code = parts[1].strip()
            # Clean this one too
            if clean_code.startswith('python\n'):
                clean_code = clean_code[7:]
            elif clean_code.startswith('python '):
                clean_code = clean_code[7:]
            elif clean_code.startswith('python'):
                if len(clean_code) > 6 and not clean_code[6].isalnum():
                    clean_code = clean_code[6:]
            clean_code = clean_code.strip()
            print(f"   Using first code block: {len(clean_code)} chars")
            return clean_code
    
    # If no code blocks found, try to clean the raw response
    print("   No code blocks found, cleaning raw response")
    
    # Remove common markdown artifacts
    cleaned = response_text.strip()
    
    # Remove markdown code block indicators
    python_code_start = triple_backtick + "python"
    if cleaned.startswith(python_code_start):
        cleaned = cleaned[len(python_code_start):]
    elif cleaned.startswith(triple_backtick):
        cleaned = cleaned[3:]
    
    # Remove trailing backticks
    if cleaned.endswith(triple_backtick):
        cleaned = cleaned[:-3]
    
    # Remove leading "python" if it's on its own line or with space
    if cleaned.startswith('python\n'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('python '):
        cleaned = cleaned[7:]
    
    # If the result still starts with just "python", it's malformed
    lines = cleaned.split('\n')
    if len(lines) > 0 and lines[0].strip() == 'python':
        # Remove the first line if it's just "python"
        cleaned = '\n'.join(lines[1:])
    
    cleaned = cleaned.strip()
    print(f"   Final cleaned code: {len(cleaned)} chars, starts with: '{cleaned[:50]}'")
    return cleaned


def _build_learned_rules_context(constraint_model: APIConstraintModel) -> str:
    """Build context string with learned constraints"""
    if not constraint_model.learned_constraints:
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

def _generate_fallback_script(user_prompt: str) -> str:
    """Generate a basic fallback script if LLM fails"""
    return '''import requests
import pytest

def test_create_user(api_base_url):
    """
    Fallback test for user creation
    """
    user_data = {
        "name": "John Doe",
        "username": "johndoe"
    }
    
    response = requests.post(f"{api_base_url}/users", json=user_data)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    response_data = response.json()
    assert "id" in response_data
'''


def generate_test_script(spec_data: Dict[str, Any], user_prompt: str, constraint_model: Optional[APIConstraintModel] = None) -> Dict[str, Any]:
    """
    Generate test script with awareness of learned constraints
    """
    
    # Configure Gemini
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Get enhanced specification if constraint model is provided
    if constraint_model:
        enhanced_spec = constraint_model.get_enhanced_schema()
        learned_rules_context = _build_learned_rules_context(constraint_model)
    else:
        enhanced_spec = spec_data
        learned_rules_context = ""
    
    # Build the enhanced prompt - MUCH MORE EXPLICIT
    prompt_template = """You are a Python test script generator. Generate a COMPLETE pytest test script.

API SPECIFICATION:
{spec}

USER REQUIREMENT: {requirement}

{rules_context}

REQUIREMENTS:
1. Generate COMPLETE Python code - no truncation
2. Use api_base_url fixture from conftest.py (do NOT define your own fixture)
3. Include ALL required fields from specification
4. Add proper error handling and assertions
5. Make actual HTTP requests to test the API

GENERATE THIS EXACT STRUCTURE (complete it fully):

import requests
import pytest

def test_create_user(api_base_url):
    user_data = {{
        "name": "John Doe",
        "username": "johndoe"
        # Add more fields as needed based on specification
    }}
    
    response = requests.post(f"{{api_base_url}}/users", json=user_data)
    assert response.status_code == 201, f"Expected 201, got {{response.status_code}}: {{response.text}}"
    
    # Verify response data
    response_data = response.json()
    assert "id" in response_data
    assert response_data["name"] == user_data["name"]

OUTPUT: Return ONLY the complete Python code. No explanations, no markdown, no truncation."""
    
    prompt = prompt_template.format(
        spec=json.dumps(enhanced_spec, indent=2),
        requirement=user_prompt,
        rules_context=learned_rules_context
    )
    
    try:
        print("🤖 Generating test script...")
        
        # Configure the model for longer responses
        generation_config = {
            "max_output_tokens": 2000,  # Allow longer responses
            "temperature": 0.1,  # More deterministic
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        print(f"🤖 Raw LLM response ({len(response.text)} chars):")
        print("=" * 30)
        print(response.text[:400])  # Show more of the response
        print("=" * 30)
        
        generated_script = _extract_code_from_response(response.text)
        
        # Final validation - ensure the script looks valid and complete
        if not generated_script or len(generated_script.strip()) < 100:
            print("❌ Generated script is too short, using fallback")
            generated_script = _generate_fallback_script(user_prompt)
        elif not ('import' in generated_script and 'def test_' in generated_script):
            print("❌ Generated script missing required elements, using fallback")
            generated_script = _generate_fallback_script(user_prompt)
        elif 'assert response.status_code' not in generated_script:
            print("❌ Generated script missing assertions, using fallback")
            generated_script = _generate_fallback_script(user_prompt)
        
        print(f"✅ Final script ({len(generated_script)} chars):")
        print("=" * 20)
        print(generated_script[:300])
        print("=" * 20)
        
        return {
            'script': generated_script,
            'user_prompt': user_prompt,
            'enhanced_spec_used': constraint_model is not None
        }
        
    except Exception as e:
        print(f"❌ Error generating test script: {e}")
        return {
            'script': _generate_fallback_script(user_prompt),
            'user_prompt': user_prompt,
            'enhanced_spec_used': False,
            'error': str(e)
        }

