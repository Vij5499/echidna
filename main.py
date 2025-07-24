import yaml
import os
from scribe import generate_test_script
from executor import execute_test_script
from interpreter import interpret_failure
from constraint_model import APIConstraintModel, LearnedConstraint
import json

def load_spec(spec_path: str) -> dict:
    """Load OpenAPI specification from YAML file"""
    try:
        with open(spec_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Specification file not found: {spec_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return {}

def has_converged(recent_attempts: list, window_size: int = 3) -> bool:
    """
    Check if the learning has converged (no new constraints learned recently)
    """
    if len(recent_attempts) < window_size:
        return False
    
    # Check if recent attempts produced new learnable constraints
    recent_learning_events = [attempt.get('learned_constraint') for attempt in recent_attempts[-window_size:]]
    new_constraints_count = sum(1 for constraint in recent_learning_events if constraint is not None)
    
    # Converged if we haven't learned anything new in recent attempts
    convergence_threshold = 0  # No new constraints
    return new_constraints_count <= convergence_threshold

def save_learning_progress(constraint_model: APIConstraintModel, output_file: str = "learned_model.json"):
    """Save the learned model to a file"""
    progress_data = {
        'total_constraints': len(constraint_model.learned_constraints),
        'constraints': {},
        'endpoint_coverage': list(constraint_model.endpoint_rules.keys())
    }
    
    for constraint_id, constraint in constraint_model.learned_constraints.items():
        progress_data['constraints'][constraint_id] = {
            'rule_description': constraint.rule_description,
            'constraint_type': constraint.constraint_type.value,
            'affected_parameter': constraint.affected_parameter,
            'endpoint_path': constraint.endpoint_path,
            'confidence_score': constraint.confidence_score,
            'success_count': constraint.success_count,
            'failure_count': constraint.failure_count
        }
    
    with open(output_file, 'w') as f:
        json.dump(progress_data, f, indent=2)
    
    print(f"📊 Learning progress saved to {output_file}")

def main():
    """
    Main learning loop with enhanced constraint management
    """
    print("🚀 Starting Adaptive API Test Agent...")
    
    # Configuration
    spec_path = "specs/spec_flawed.yaml"  # Use the flawed spec to test learning
    max_attempts = 5
    user_prompt = "Create a new user with valid data and verify the response"
    
    # Load initial specification and create constraint model
    print(f"📋 Loading specification from {spec_path}")
    spec_data = load_spec(spec_path)
    
    if not spec_data:
        print("❌ Failed to load specification. Exiting.")
        return
    
    # Initialize the constraint model
    constraint_model = APIConstraintModel(spec_data)
    
    # Track learning progress
    learning_attempts = []
    
    print(f"🎯 Goal: {user_prompt}")
    print(f"🔄 Maximum learning attempts: {max_attempts}")
    print("=" * 60)
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Learning Attempt {attempt}/{max_attempts}")
        
        # Generate test script with current knowledge
        print("📝 Generating test script with current constraints...")
        generated_script_data = generate_test_script(spec_data, user_prompt, constraint_model)
        
        if 'error' in generated_script_data:
            print(f"❌ Script generation failed: {generated_script_data['error']}")
            continue
        
        generated_script = generated_script_data['script']
        script_file = f"generated_test_{attempt}.py"
        
        # Save script to file
        with open(script_file, 'w') as f:
            f.write(generated_script)
        
        print(f"💾 Script saved to {script_file}")
        
        # Execute the test
        print("🧪 Executing test script...")
        execution_result = execute_test_script(script_file)
        
        # Track attempt details
        attempt_data = {
            'attempt_number': attempt,
            'script_file': script_file,
            'execution_successful': execution_result['success'],
            'learned_constraint': None
        }
        
        if execution_result['success']:
            print("✅ Test passed! No learning needed from this attempt.")
            # Update confidence scores for applied constraints
            _update_successful_constraints(constraint_model, generated_script_data)
        else:
            print("❌ Test failed. Analyzing failure for learning opportunities...")
            
            # Extract request details from the generated script
            request_details = _extract_request_details_from_script(generated_script)
            
            # Interpret the failure
            learned_constraint = interpret_failure(
                user_prompt, 
                generated_script, 
                request_details,
                execution_result['output_file']
            )
            
            if learned_constraint:
                # Add the constraint to our model
                constraint_id = constraint_model.add_constraint(learned_constraint)
                attempt_data['learned_constraint'] = learned_constraint
                
                print(f"🧠 New constraint learned: {learned_constraint.rule_description}")
                print(f"   📍 Endpoint: {learned_constraint.endpoint_path}")
                print(f"   🎯 Parameter: {learned_constraint.affected_parameter}")
                print(f"   📊 Confidence: {learned_constraint.confidence_score:.2f}")
            else:
                print("🤔 No learnable constraint found from this failure.")
        
        learning_attempts.append(attempt_data)
        
        # Check for convergence
        if has_converged(learning_attempts):
            print("\n🎉 Learning has converged! The model has stabilized.")
            break
        
        # Show current learning state
        total_constraints = len(constraint_model.learned_constraints)
        print(f"📈 Current knowledge: {total_constraints} learned constraints")
        
        # Clean up script file
        if os.path.exists(script_file):
            os.remove(script_file)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 LEARNING SUMMARY")
    print("=" * 60)
    
    total_constraints = len(constraint_model.learned_constraints)
    successful_attempts = sum(1 for attempt in learning_attempts if attempt['execution_successful'])
    
    print(f"🔢 Total learning attempts: {len(learning_attempts)}")
    print(f"✅ Successful tests: {successful_attempts}")
    print(f"🧠 Constraints learned: {total_constraints}")
    print(f"📍 Endpoints covered: {len(constraint_model.endpoint_rules)}")
    
    if total_constraints > 0:
        print("\n🎓 LEARNED CONSTRAINTS:")
        for i, (constraint_id, constraint) in enumerate(constraint_model.learned_constraints.items(), 1):
            print(f"  {i}. {constraint.rule_description}")
            print(f"     └─ Confidence: {constraint.confidence_score:.2f}")
    
    # Save the learned model
    save_learning_progress(constraint_model)
    
    # Generate final enhanced specification
    enhanced_spec = constraint_model.get_enhanced_schema()
    with open("enhanced_specification.yaml", 'w') as f:
        yaml.dump(enhanced_spec, f, default_flow_style=False, sort_keys=False)
    
    print(f"📋 Enhanced specification saved to enhanced_specification.yaml")
    print("\n🎯 Learning session complete!")

def _extract_request_details_from_script(script: str) -> dict:
    """Extract request details from the generated script for analysis"""
    request_details = {'request_body': {}}
    
    # Look for JSON data in the script
    import re
    json_match = re.search(r'json\s*=\s*(\{[^}]*\})', script)
    if json_match:
        try:
            request_details['request_body'] = eval(json_match.group(1))
        except:
            request_details['request_body'] = json_match.group(1)
    
    return request_details

def _update_successful_constraints(constraint_model: APIConstraintModel, script_data: dict):
    """Update confidence scores for constraints that led to successful tests"""
    if script_data.get('enhanced_spec_used'):
        # Find constraints that were likely applied in this successful test
        for constraint in constraint_model.learned_constraints.values():
            if constraint.confidence_score > 0.7:  # Only update high-confidence constraints
                constraint.update_confidence(success=True)

if __name__ == "__main__":
    main()
