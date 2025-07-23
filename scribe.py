import google.generativeai as genai
from pydantic import BaseModel, Field
import yaml
import os
from dotenv import load_dotenv
import json

# Load environment variables from the.env file
load_dotenv()
# Configure the Gemini client with the API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# This Pydantic model remains the same. It's our contract for what we expect back.
class GeneratedTestScript(BaseModel):
    """A model to hold the generated pytest script."""
    file_name: str = Field(description="The suggested filename for the test, e.g., 'test_user_creation.py'")
    script: str = Field(description="The complete, executable pytest script as a Python string.")
    explanation: str = Field(description="A brief, human-readable explanation of what the generated test does.")

def generate_test_script(api_spec_content: str, user_prompt: str) -> GeneratedTestScript:
    """Generates a pytest script from an API spec and a user prompt using Google Gemini."""
    
    prompt = f"""
    You are an expert QA Automation Engineer specializing in API testing with Python and pytest.
    Your task is to generate a single, complete, and executable pytest script based on the provided OpenAPI specification and a user's testing goal.
    The script must be self-contained and use the 'requests' library to make API calls. It should include at least one test function starting with 'test_' and make assertions to verify the expected outcome.

    Return your response as a JSON object that conforms to this schema:
    {{
        "file_name": "string",
        "script": "string",
        "explanation": "string"
    }}

    *** IMPORTANT INSTRUCTION ***
    The script MUST handle HTTP errors. Use a try/except block for the API call. If a 'requests.exceptions.HTTPError' occurs and the status code is a 4xx client error, the script must write the status code and the JSON response body to a file named 'failure_context.json' before re-raising the exception. This is critical for learning from failures.

    Here is the OpenAPI specification:
    ---
    {api_spec_content}
    ---
    
    Here is the user's testing goal: "{user_prompt}"

    Now, generate the JSON object containing the pytest script.
    """

    try:
        # Initialize the Gemini model with the updated, correct name
        model = genai.GenerativeModel('gemini-2.5-flash') # <-- THIS LINE IS UPDATED
        
        # Send the prompt to the model
        response = model.generate_content(prompt)

        # Clean up the response to ensure it's valid JSON
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        
        # Parse the JSON string into a Python dictionary
        response_json = json.loads(cleaned_response_text)
        
        # Use the Pydantic model to validate and structure the data
        return GeneratedTestScript(**response_json)

    except Exception as e:
        print(f"An error occurred while calling the Google Gemini API: {e}")
        # Return a default or empty object to prevent crashes
        return GeneratedTestScript(file_name="error_test.py", script=f"# Generation failed due to: {e}", explanation=f"Error: {e}")