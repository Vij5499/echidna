import argparse
import yaml
import os
from dotenv import load_dotenv
import google.generativeai as genai
from scribe import generate_test_script
from executor import run_test
from interpreter import interpret_failure

def list_models():
    """Lists available Gemini models that support content generation."""
    print("--- Available Gemini Models (for content generation) ---")
    try:
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"- {model.name}")
    except Exception as e:
        print(f"Could not list models. Is your API key configured correctly? Error: {e}")

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Echidna - An Adaptive API Test Agent (Phase 2)")
    parser.add_argument("--spec", help="Path to the OpenAPI spec file (.yaml or.json).")
    parser.add_argument("--prompt", help="The testing goal in natural language.")
    parser.add_argument("--list-models", action="store_true", help="List available Gemini models and exit.")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in.env file.")
        return
    genai.configure(api_key=api_key)

    if args.list_models:
        list_models()
        return

    if not args.spec or not args.prompt:
        parser.error("--spec and --prompt are required unless using --list-models.")

    print("--- Echidna Agent Initializing ---")
    
    try:
        with open(args.spec, 'r') as f:
            # This dictionary is now our dynamic, "Extensible Model"
            api_model = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading or parsing the specification file: {e}")
        return

    max_attempts = 3
    last_script_generated = ""

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")

        # Step 1: Generate script based on the *current* state of our model
        print("Generating test script...")
        generated_test = generate_test_script(yaml.dump(api_model), args.prompt)
        last_script_generated = generated_test.script
        
        if "# Generation failed" in last_script_generated:
            print("❌ Scribe failed to generate a valid script. Halting.")
            break

        # Step 2: Execute the test
        success, stdout, stderr = run_test(generated_test.script, generated_test.file_name)

        if success:
            print("\n--- Result ---")
            print("✅ Test Passed!")
            print(stdout)
            break # Exit the loop on success

        # Step 3: If failed, begin the learning process
        print("\n--- Result ---")
        print("❌ Test Failed. Analyzing failure...")
        
        if os.path.exists("failure_context.json"):
            inferred_rule = interpret_failure(args.prompt, last_script_generated)

            if inferred_rule.is_learnable:
                print(f"🧠 New Rule Learned: {inferred_rule.rule_description}")
                
                # Step 4: Update the model (The "Rule Maker" step)
                # We append the learned rule to the API's main description.
                # This passes the new knowledge back to the Scribe in the next loop.
                if 'description' not in api_model['info']:
                    api_model['info']['description'] = ""
                api_model['info']['description'] += f"\n\nIMPORTANT LEARNED RULE: {inferred_rule.rule_description}"
                
                os.remove("failure_context.json") # Clean up for the next attempt
            else:
                print("Encountered a non-learnable error (e.g., 5xx server error or script bug). Halting.")
                print(f"Reason: {inferred_rule.rule_description}")
                break
        else:
            print("Test failed without a specific API error context (e.g., a Python error in the script). Halting.")
            print("--- STDOUT ---")
            print(stdout)
            print("--- STDERR ---")
            print(stderr)
            break
    else: # This 'else' belongs to the 'for' loop, runs if the loop completes without 'break'
        print("\n--- Final Result ---")
        print("❌ Agent could not achieve a passing test after all attempts.")

if __name__ == "__main__":
    main()