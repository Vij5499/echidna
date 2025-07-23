import google.generativeai as genai
from pydantic import BaseModel, Field
import json
import os

class InferredRule(BaseModel):
    """A model for a new rule learned from an API failure."""
    rule_description: str = Field(description="A human-readable description of the rule that was violated. For example, 'The parameter X is required.'")
    is_learnable: bool = Field(description="True if this is a client-side error (4xx) that can be fixed, False for server errors (5xx) or other issues.")

def interpret_failure(user_prompt: str, failed_script: str, failure_context_path: str = "failure_context.json") -> InferredRule:
    """Analyzes a failed test's context to infer the broken rule."""
    
    try:
        with open(failure_context_path, 'r') as f:
            context = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return InferredRule(rule_description="No failure context file found or file is invalid.", is_learnable=False)

    system_prompt = """
    You are a senior API diagnostician. Your job is to analyze a failed API test and determine the root cause.
    You will be given the original goal, the script that failed, and the HTTP error response.
    Focus on client-side errors (4xx status codes). Infer the specific API constraint that was likely violated.
    For example, if the error is '{"error": "field 'email' is required"}', the inferred rule is "The 'email' field is a required parameter for this request."
    If the error is a 5xx server error, it is not learnable.
    """

    human_prompt = f"""
    Original Goal: "{user_prompt}"
    
    Failed Script:
    ---
    {failed_script}
    ---

    Failure Context (from the API response):
    ---
    Status Code: {context.get('status_code')}
    Response Body: {json.dumps(context.get('response_body'))}
    ---

    Based on this, what API rule was violated?
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            system_prompt + human_prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        response_json = json.loads(response.text)
        return InferredRule(**response_json)

    except Exception as e:
        print(f"An error occurred during failure interpretation: {e}")
        return InferredRule(rule_description=f"Failed to interpret error: {e}", is_learnable=False)