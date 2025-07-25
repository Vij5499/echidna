# Updated main.py with correct flow and Phase 3 integration
import yaml
import os
from typing import Optional, Dict, Any, List
from scribe import generate_test_script
from executor import execute_test_script
from interpreter import interpret_failure
from constraint_model import APIConstraintModel, LearnedConstraint
from error_handler import error_handler, AdaptiveError, ErrorType, ErrorSeverity
import json

def load_spec_with_error_handling(spec_path: str) -> dict:
    """Load OpenAPI specification with comprehensive error handling"""
    try:
        with open(spec_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        error = AdaptiveError(
            f"Specification file not found: {spec_path}",
            ErrorType.FILE_SYSTEM,
            ErrorSeverity.HIGH,
            context={'missing_file': spec_path}
        )
        recovery_result = error_handler.handle_error(error)
        if recovery_result:
            return load_default_spec()
        return {}
    except yaml.YAMLError as e:
        error = AdaptiveError(
            f"Error parsing YAML file: {e}",
            ErrorType.CONFIGURATION,
            ErrorSeverity.HIGH,
            context={'yaml_error': str(e), 'file_path': spec_path}
        )
        error_handler.handle_error(error)
        return {}
    except Exception as e:
        error = AdaptiveError(
            f"Unexpected error loading spec: {e}",
            ErrorType.FILE_SYSTEM,
            ErrorSeverity.MEDIUM,
            context={'error': str(e), 'file_path': spec_path}
        )
        error_handler.handle_error(error)
        return {}

def load_default_spec() -> dict:
    """Provide a minimal default specification for emergency fallback"""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Default API", "version": "1.0.0"},
        "paths": {
            "/health": {
                "get": {
                    "responses": {"200": {"description": "Health check"}}
                }
            }
        }
    }

def main():
    """Enhanced main function with Phase 3 pattern discovery integration"""
    try:
        print("🚀 Starting Adaptive API Test Agent...")
        
        # 1. INITIALIZATION PHASE
        config = {
            'spec_path': os.getenv('SPEC_PATH', "specs/spec_enhanced_flawed.yaml"),  # Updated default
            'max_attempts': int(os.getenv('MAX_ATTEMPTS', '5')),
            'user_prompt': os.getenv('USER_PROMPT', "Create a new user with valid data and verify the response")
        }
        
        print(f"📋 Loading specification from {config['spec_path']}")
        spec_data = load_spec_with_error_handling(config['spec_path'])
        
        if not spec_data:
            print("❌ Failed to load specification. Using fallback mode.")
            spec_data = load_default_spec()
        
        # 2. CONSTRAINT MODEL INITIALIZATION (Fixed: Single initialization)
        constraint_model = safe_constraint_model_initialization(spec_data)
        
        if not constraint_model:
            print("⚠️ Proceeding without constraint model (limited functionality)")
            return
        
        # 3. LEARNING LOOP PHASE
        learning_attempts = []
        successful_attempts = 0
        learned_constraints_count = 0  # Track learned constraints
        
        print(f"🎯 Goal: {config['user_prompt']}")
        print(f"🔄 Maximum learning attempts: {config['max_attempts']}")
        print("=" * 60)
        
        for attempt in range(1, config['max_attempts'] + 1):
            print(f"\n🔄 Learning Attempt {attempt}/{config['max_attempts']}")
            
            try:
                # Generate test script
                print("📝 Generating test script with current constraints...")
                generated_script_data = generate_test_script_with_error_handling(
                    spec_data, config['user_prompt'], constraint_model
                )
                
                if 'error' in generated_script_data:
                    print(f"❌ Script generation failed: {generated_script_data['error']}")
                    continue
                
                generated_script = generated_script_data['script']
                script_file = f"generated_test_{attempt}.py"
                
                # Save script
                try:
                    with open(script_file, 'w', encoding='utf-8') as f:
                        f.write(generated_script)
                    print(f"💾 Script saved to {script_file}")
                except Exception as e:
                    error = AdaptiveError(
                        f"Failed to save test script: {e}",
                        ErrorType.FILE_SYSTEM,
                        ErrorSeverity.MEDIUM,
                        context={'script_file': script_file}
                    )
                    error_handler.handle_error(error)
                    continue
                
                # Execute test
                print("🧪 Executing test script...")
                execution_result = execute_test_script_with_error_handling(script_file)
                
                # Track attempt details
                attempt_data = {
                    'attempt_number': attempt,
                    'script_file': script_file,
                    'execution_successful': execution_result['success'],
                    'learned_constraint': None
                }
                
                if execution_result['success']:
                    print("✅ Test passed! No learning needed from this attempt.")
                    successful_attempts += 1
                    _update_successful_constraints(constraint_model, generated_script_data)
                else:
                    print("❌ Test failed. Analyzing failure for learning opportunities...")
                    
                    # Extract request details and interpret failure
                    request_details = _extract_request_details_from_script(generated_script)
                    learned_constraint = interpret_failure_with_error_handling(
                        config['user_prompt'], 
                        generated_script, 
                        request_details,
                        execution_result.get('output_file', '')
                    )
                    
                    if learned_constraint:
                        constraint_id = constraint_model.add_constraint(learned_constraint)
                        attempt_data['learned_constraint'] = learned_constraint
                        learned_constraints_count += 1  # Increment counter
                        
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
                try:
                    if os.path.exists(script_file):
                        os.remove(script_file)
                except Exception as e:
                    error = AdaptiveError(
                        f"Failed to clean up script file: {e}",
                        ErrorType.FILE_SYSTEM,
                        ErrorSeverity.LOW,
                        context={'script_file': script_file}
                    )
                    error_handler.handle_error(error)
                
            except Exception as e:
                error = AdaptiveError(
                    f"Unexpected error in learning attempt {attempt}: {e}",
                    ErrorType.TEST_EXECUTION,
                    ErrorSeverity.MEDIUM,
                    context={'attempt': attempt, 'traceback': str(e)}
                )
                error_handler.handle_error(error)
                continue
        
        # 4. PHASE 3: ADVANCED PATTERN ANALYSIS (Fixed: Correct placement and condition)
        total_learned_constraints = len(constraint_model.learned_constraints)
        if total_learned_constraints > 0:
            try:
                pattern_discovery = analyze_learned_patterns(constraint_model)
            except Exception as e:
                print(f"⚠️ Pattern analysis failed: {e}")
                pattern_discovery = None
        else:
            print("\n🔍 No constraints learned - skipping pattern analysis")
            pattern_discovery = None
        
        # 5. FINAL SUMMARY PHASE
        print_final_summary(learning_attempts, constraint_model, successful_attempts, pattern_discovery)
        
    except Exception as e:
        error = AdaptiveError(
            f"Critical error in main execution: {e}",
            ErrorType.CONFIGURATION,
            ErrorSeverity.CRITICAL,
            context={'traceback': str(e)}
        )
        error_handler.handle_error(error)
        print("❌ Critical error occurred. Check logs for details.")

def analyze_learned_patterns(constraint_model):
    """Analyze learned constraints for cross-endpoint patterns"""
    # Import here to avoid circular imports
    try:
        from pattern_discovery import AdvancedPatternDiscovery
    except ImportError:
        print("⚠️ Pattern discovery module not found. Skipping advanced analysis.")
        return None
    
    print("\n🔬 ADVANCED PATTERN ANALYSIS")
    print("=" * 60)
    
    pattern_discovery = AdvancedPatternDiscovery()
    
    # Analyze patterns in learned constraints
    discovered_patterns = pattern_discovery.analyze_constraint_patterns(constraint_model.learned_constraints)
    
    if discovered_patterns:
        print(f"🎯 Discovered {len(discovered_patterns)} cross-endpoint patterns:")
        
        for pattern in discovered_patterns:
            print(f"\n📊 Pattern: {pattern.pattern_description}")
            print(f"   🎯 Type: {pattern.pattern_type}")
            print(f"   📍 Scope: {pattern.scope.value}")
            print(f"   📊 Confidence: {pattern.confidence:.2f}")
            print(f"   🌐 Endpoints: {len(pattern.affected_endpoints)}")
            
            if pattern.parameter_patterns:
                print(f"   📋 Pattern Details: {pattern.parameter_patterns}")
    else:
        print("🔍 No cross-endpoint patterns discovered yet")
    
    # Generate predictions for potential new endpoints
    if len(constraint_model.learned_constraints) >= 2:
        print(f"\n🔮 PATTERN PREDICTIONS")
        print("=" * 40)
        
        # Example prediction for a new endpoint
        try:
            test_predictions = pattern_discovery.generate_pattern_predictions(
                target_endpoint="/orders",
                target_parameters=["customer_id", "total_amount", "payment_method", "email", "phone"]
            )
            
            if test_predictions:
                print(f"📈 Predictions for '/orders' endpoint:")
                for pred in test_predictions[:3]:  # Show top 3 predictions
                    print(f"   🎯 {pred['description']}")
                    print(f"      📊 Confidence: {pred['confidence']:.2f}")
                    print(f"      💡 Applicability: {pred['applicability_score']:.2f}")
            else:
                print("📈 No pattern-based predictions available yet")
        except Exception as e:
            print(f"⚠️ Error generating predictions: {e}")
    
    # Export pattern knowledge
    try:
        pattern_export = pattern_discovery.export_pattern_knowledge()
        
        # Save pattern analysis
        with open('pattern_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(pattern_export, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📊 Pattern analysis saved to pattern_analysis.json")
    except Exception as e:
        print(f"⚠️ Error saving pattern analysis: {e}")
    
    return pattern_discovery

def print_final_summary(learning_attempts, constraint_model, successful_attempts, pattern_discovery=None):
    """Enhanced final summary with pattern discovery results"""
    print("\n" + "=" * 60)
    print("📊 LEARNING SUMMARY")
    print("=" * 60)
    
    total_constraints = len(constraint_model.learned_constraints)
    
    print(f"🔢 Total learning attempts: {len(learning_attempts)}")
    print(f"✅ Successful tests: {successful_attempts}")
    print(f"🧠 Constraints learned: {total_constraints}")
    print(f"📍 Endpoints covered: {len(constraint_model.endpoint_rules)}")
    
    # Add pattern discovery summary
    if pattern_discovery:
        pattern_count = len(pattern_discovery.discovered_patterns)
        print(f"🔬 Cross-endpoint patterns discovered: {pattern_count}")
    
    # Add error statistics
    error_stats = error_handler.get_error_statistics()
    if error_stats['total_errors'] > 0:
        print(f"\n🔧 ERROR STATISTICS:")
        print(f"   Total errors handled: {error_stats['total_errors']}")
        for error_type, count in error_stats.get('error_breakdown', {}).items():
            print(f"   {error_type}: {count}")
    
    if total_constraints > 0:
        print("\n🎓 LEARNED CONSTRAINTS:")
        for i, (constraint_id, constraint) in enumerate(constraint_model.learned_constraints.items(), 1):
            print(f"  {i}. {constraint.rule_description}")
            print(f"     └─ Confidence: {constraint.confidence_score:.2f}")
    
    # Save learning progress
    save_learning_progress(constraint_model)
    
    print("\n🎯 Learning session complete!")

# Keep all your existing helper functions (they're correct)
def generate_test_script_with_error_handling(spec_data, user_prompt, constraint_model):
    """Generate test script with comprehensive error handling"""
    try:
        return generate_test_script(spec_data, user_prompt, constraint_model)
    except Exception as e:
        error = AdaptiveError(
            f"Test script generation failed: {e}",
            ErrorType.LLM_FAILURE,
            ErrorSeverity.HIGH,
            context={'prompt': user_prompt, 'task': 'test_generation'}
        )
        recovery_result = error_handler.handle_error(error)
        
        if recovery_result and recovery_result != "DEGRADED_MODE":
            return {'script': recovery_result, 'user_prompt': user_prompt, 'enhanced_spec_used': False}
        else:
            return {'error': str(e), 'user_prompt': user_prompt}

def execute_test_script_with_error_handling(script_file):
    """Execute test script with error handling"""
    try:
        return execute_test_script(script_file)
    except Exception as e:
        error = AdaptiveError(
            f"Test execution failed: {e}",
            ErrorType.TEST_EXECUTION,
            ErrorSeverity.MEDIUM,
            context={'script_file': script_file}
        )
        recovery_result = error_handler.handle_error(error)
        
        return {
            'success': False,
            'error': str(e),
            'output_file': None,
            'recovered': recovery_result is not None
        }

def interpret_failure_with_error_handling(user_prompt, failed_script, request_details, failure_context_path):
    """Interpret failure with error handling"""
    try:
        return interpret_failure(user_prompt, failed_script, request_details, failure_context_path)
    except Exception as e:
        error = AdaptiveError(
            f"Failure interpretation failed: {e}",
            ErrorType.CONSTRAINT_PARSING,
            ErrorSeverity.MEDIUM,
            context={'raw_response': failure_context_path}
        )
        recovery_result = error_handler.handle_error(error)
        return recovery_result

def has_converged(recent_attempts: list, window_size: int = 3) -> bool:
    """Check if learning has converged with error handling"""
    try:
        if len(recent_attempts) < window_size:
            return False
        
        recent_learning_events = [attempt.get('learned_constraint') for attempt in recent_attempts[-window_size:]]
        new_constraints_count = sum(1 for constraint in recent_learning_events if constraint is not None)
        
        convergence_threshold = 0
        return new_constraints_count <= convergence_threshold
    except Exception as e:
        error = AdaptiveError(
            f"Error checking convergence: {e}",
            ErrorType.CONFIGURATION,
            ErrorSeverity.LOW,
            context={'attempts': len(recent_attempts)}
        )
        error_handler.handle_error(error)
        return False

def save_learning_progress(constraint_model: APIConstraintModel, output_file: str = "learned_model.json"):
    """Save learning progress with error handling"""
    try:
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
        
    except Exception as e:
        error = AdaptiveError(
            f"Failed to save learning progress: {e}",
            ErrorType.FILE_SYSTEM,
            ErrorSeverity.MEDIUM,
            context={'output_file': output_file}
        )
        error_handler.handle_error(error)

def _extract_request_details_from_script(script: str) -> dict:
    """Extract request details from script with error handling"""
    try:
        request_details = {'request_body': {}}
        
        import re
        json_match = re.search(r'json\s*=\s*(\{[^}]*\})', script)
        if json_match:
            try:
                request_details['request_body'] = eval(json_match.group(1))
            except:
                request_details['request_body'] = json_match.group(1)
        
        return request_details
    except Exception as e:
        error = AdaptiveError(
            f"Failed to extract request details: {e}",\
            ErrorType.CONSTRAINT_PARSING,
            ErrorSeverity.LOW,
            context={'script_length': len(script)}
        )
        error_handler.handle_error(error)
        return {'request_body': {}}

def _update_successful_constraints(constraint_model: APIConstraintModel, script_data: dict):
    """Update constraint confidence with error handling"""
    try:
        if script_data.get('enhanced_spec_used'):
            for constraint in constraint_model.learned_constraints.values():
                if constraint.confidence_score > 0.7:
                    constraint.update_confidence(success=True)
    except Exception as e:
        error = AdaptiveError(
            f"Failed to update constraint confidence: {e}",
            ErrorType.CONSTRAINT_PARSING,
            ErrorSeverity.LOW,
            context={'script_data': script_data}
        )
        error_handler.handle_error(error)

# Keep all your existing helper functions for safe initialization, validation, etc.
# (safe_constraint_model_initialization, _validate_spec_structure, _repair_specification, _get_minimal_default_spec)
def safe_constraint_model_initialization(spec_data: dict) -> Optional[APIConstraintModel]:
    """Safely initialize constraint model with pre-validation"""
    try:
        # Pre-validate the specification structure
        validation_result = _validate_spec_structure(spec_data)
        
        if not validation_result['is_valid']:
            print(f"⚠️ Specification validation failed: {validation_result['issues']}")
            print("🔧 Attempting to repair specification...")
            
            repaired_spec = _repair_specification(spec_data, validation_result['issues'])
            if repaired_spec:
                spec_data = repaired_spec
                print("✅ Specification repaired successfully")
            else:
                print("❌ Could not repair specification, using minimal default")
                spec_data = _get_minimal_default_spec()
        
        # Initialize constraint model
        constraint_model = APIConstraintModel(spec_data)
        print("✅ Constraint model initialized successfully")
        return constraint_model
        
    except Exception as e:
        error = AdaptiveError(
            f"Failed to initialize constraint model: {e}",
            ErrorType.CONFIGURATION,
            ErrorSeverity.HIGH,
            context={'spec_data_type': type(spec_data).__name__, 'spec_keys': list(spec_data.keys()) if isinstance(spec_data, dict) else 'not_dict'}
        )
        recovery_result = error_handler.handle_error(error)
        
        if recovery_result:
            print("✅ Using recovered constraint model")
            return APIConstraintModel(_get_minimal_default_spec())
        
        print("❌ Could not initialize constraint model, proceeding without it")
        return None


def _validate_spec_structure(spec_data: dict) -> Dict[str, Any]:
    """Validate the basic structure of an OpenAPI specification"""
    issues = []
    
    # Check if it's a dictionary
    if not isinstance(spec_data, dict):
        issues.append(f"Specification must be a dictionary, got {type(spec_data).__name__}")
        return {'is_valid': False, 'issues': issues}
    
    # Check for required top-level fields
    required_fields = ['openapi', 'info', 'paths']
    optional_fields = ['servers', 'components', 'security', 'tags']
    
    for field in required_fields:
        if field not in spec_data:
            issues.append(f"Missing required field: {field}")
        elif not isinstance(spec_data[field], (dict, str)):
            if field == 'paths' and not isinstance(spec_data[field], dict):
                issues.append(f"Field '{field}' must be a dictionary")
            elif field in ['openapi'] and not isinstance(spec_data[field], str):
                issues.append(f"Field '{field}' must be a string")
            elif field == 'info' and not isinstance(spec_data[field], dict):
                issues.append(f"Field '{field}' must be a dictionary")
    
    # Validate info section structure
    if 'info' in spec_data and isinstance(spec_data['info'], dict):
        info_required = ['title', 'version']
        for field in info_required:
            if field not in spec_data['info']:
                issues.append(f"Missing required info field: {field}")
    
    # Validate paths section structure
    if 'paths' in spec_data:
        if not isinstance(spec_data['paths'], dict):
            issues.append("Paths section must be a dictionary")
        else:
            # Check path structure
            for path, methods in spec_data['paths'].items():
                if not isinstance(methods, dict):
                    issues.append(f"Path '{path}' methods must be a dictionary")
    
    return {
        'is_valid': len(issues) == 0,
        'issues': issues
    }


def _repair_specification(spec_data: dict, issues: List[str]) -> Optional[dict]:
    """Attempt to repair common specification issues"""
    try:
        repaired_spec = spec_data.copy() if isinstance(spec_data, dict) else {}
        
        # Fix missing required fields
        if "Missing required field: openapi" in issues:
            repaired_spec['openapi'] = "3.0.0"
        
        if "Missing required field: info" in issues:
            repaired_spec['info'] = {"title": "Repaired API", "version": "1.0.0"}
        elif isinstance(repaired_spec.get('info'), dict):
            if "Missing required info field: title" in issues:
                repaired_spec['info']['title'] = "Repaired API"
            if "Missing required info field: version" in issues:
                repaired_spec['info']['version'] = "1.0.0"
        
        if "Missing required field: paths" in issues:
            repaired_spec['paths'] = {
                "/users": {
                    "post": {
                        "summary": "Create user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "username": {"type": "string"}
                                        },
                                        "required": ["name", "username"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "User created"}
                        }
                    }
                }
            }
        
        # Fix paths structure issues
        if "Paths section must be a dictionary" in issues:
            repaired_spec['paths'] = {}
        
        # Validate the repaired spec
        validation = _validate_spec_structure(repaired_spec)
        if validation['is_valid']:
            return repaired_spec
        else:
            print(f"⚠️ Repair unsuccessful, remaining issues: {validation['issues']}")
            return None
            
    except Exception as e:
        print(f"❌ Error during specification repair: {e}")
        return None


def _get_minimal_default_spec() -> dict:
    """Get a minimal but valid OpenAPI specification"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Minimal Default API",
            "version": "1.0.0",
            "description": "Fallback specification for error recovery"
        },
        "paths": {
            "/users": {
                "post": {
                    "summary": "Create a user",
                    "operationId": "createUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "User's name"
                                        },
                                        "username": {
                                            "type": "string", 
                                            "description": "User's username"
                                        }
                                    },
                                    "required": ["name", "username"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created successfully"
                        },
                        "400": {
                            "description": "Bad request"
                        }
                    }
                }
            },
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "Service is healthy"
                        }
                    }
                }
            }
        }
    }

if __name__ == "__main__":
    main()
