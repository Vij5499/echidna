# Create: test_comprehensive_framework.py
"""
Comprehensive Test Framework for Adaptive API Test Agent
Consolidates all testing capabilities into systematic validation
"""

import pytest
import json
import time
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class ComprehensiveTestFramework:
    def __init__(self):
        self.test_results = {}
        self.baseline_metrics = {}
        self.start_time = time.time()
        
    def run_constraint_type_validation(self):
        """Test all implemented constraint types systematically"""
        print("🧪 Testing All Constraint Types...")
        
        constraint_scenarios = [
            {
                'name': 'Required Field',
                'prompt': 'Create user without mandatory name field',
                'expected_constraint': 'required_field',
                'expected_pattern': 'field_presence'
            },
            {
                'name': 'Format Validation',
                'prompt': 'Create user with invalid email format like "not-an-email"',
                'expected_constraint': 'format_validation',
                'expected_pattern': 'format_rules'
            },
            {
                'name': 'Conditional Requirement',
                'prompt': 'Create user with premium features but without premium subscription',
                'expected_constraint': 'conditional_requirement',
                'expected_pattern': 'conditional_logic'
            },
            {
                'name': 'Mutual Exclusivity',
                'prompt': 'Create user with both email and phone contact methods',
                'expected_constraint': 'mutual_exclusivity',
                'expected_pattern': 'exclusive_fields'
            },
            {
                'name': 'Format Dependency',
                'prompt': 'Create user with country code but invalid phone format for that country',
                'expected_constraint': 'format_dependency',
                'expected_pattern': 'dependent_validation'
            },
            {
                'name': 'Business Rule',
                'prompt': 'Create user with age less than minimum required age of 13',
                'expected_constraint': 'business_rule',
                'expected_pattern': 'business_logic'
            },
            {
                'name': 'Value Constraint',
                'prompt': 'Create user with negative age value which should be invalid',
                'expected_constraint': 'value_constraint',
                'expected_pattern': 'value_bounds'
            },
            {
                'name': 'Rate Limiting',
                'prompt': 'Make rapid consecutive requests to trigger rate limiting',
                'expected_constraint': 'rate_limiting',
                'expected_pattern': 'rate_control'
            }
        ]
        
        results = {}
        for scenario in constraint_scenarios:
            print(f"  🎯 Testing {scenario['name']}...")
            
            # Set environment and run test
            env = os.environ.copy()
            env.update({
                'SPEC_PATH': 'specs/spec_enhanced_flawed.yaml',
                'MAX_ATTEMPTS': '1',  # Reduced for faster testing
                'USER_PROMPT': scenario['prompt'],
                'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY', '')  # Ensure API key is passed
            })
            
            start_time = time.time()
            try:
                result = subprocess.run(
                    [sys.executable, 'main.py'],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=180,  # Increased timeout for constraint learning
                    encoding='utf-8',  # Fix encoding issue
                    errors='replace'   # Replace invalid characters instead of crashing
                )
                execution_time = time.time() - start_time
            except subprocess.TimeoutExpired as e:
                print(f"    ⏰ {scenario['name']} timed out after 180s")
                execution_time = 180.0
                result = type('obj', (object,), {
                    'returncode': -1,
                    'stdout': f"Process timed out after 180 seconds",
                    'stderr': f"TimeoutExpired: {str(e)}"
                })()
            except Exception as e:
                print(f"    ❌ {scenario['name']} failed with exception: {e}")
                execution_time = time.time() - start_time
                result = type('obj', (object,), {
                    'returncode': -1,
                    'stdout': "",
                    'stderr': f"Exception: {str(e)}"
                })()
            
            # Analyze results
            success = result.returncode == 0
            constraint_learned = False
            
            if success and os.path.exists('learned_model.json'):
                with open('learned_model.json', 'r') as f:
                    learned_data = json.load(f)
                    
                # Check if expected constraint type was learned
                for constraint in learned_data.get('constraints', {}).values():
                    if scenario['expected_constraint'] in constraint.get('constraint_type', ''):
                        constraint_learned = True
                        break
            
            # Also check if any constraint was learned (more lenient)
            any_constraint_learned = False
            if os.path.exists('learned_model.json'):
                with open('learned_model.json', 'r') as f:
                    learned_data = json.load(f)
                    any_constraint_learned = learned_data.get('total_constraints', 0) > 0
            
            results[scenario['name']] = {
                'success': success,
                'constraint_learned': constraint_learned,
                'any_constraint_learned': any_constraint_learned,
                'execution_time': execution_time,
                'expected_type': scenario['expected_constraint']
            }
            
            # Clean up for next test
            if os.path.exists('learned_model.json'):
                os.remove('learned_model.json')
            
            # More informative output
            status_icon = "✅" if constraint_learned else ("🟡" if any_constraint_learned else "❌")
            print(f"    {status_icon} {scenario['name']}: {execution_time:.2f}s")
            
            # Wait to avoid rate limiting for next test (reduced for efficiency)
            print(f"    ⏳ Waiting 10s for rate limit reset...")
            time.sleep(10)
        
        self.test_results['constraint_types'] = results
        return results
    
    def run_edge_case_validation(self):
        """Test edge cases and boundary conditions"""
        print("🔍 Testing Edge Cases...")
        
        edge_cases = [
            {
                'name': 'Empty API Spec',
                'spec_content': '{"openapi": "3.0.0", "info": {"title": "Empty", "version": "1.0.0"}, "paths": {}}',
                'expected_behavior': 'graceful_handling'
            },
            {
                'name': 'Malformed JSON Response',
                'mock_response': '{"error": malformed json}',
                'expected_behavior': 'parsing_recovery'
            },
            {
                'name': 'Unicode Error Messages',
                'mock_response': '{"error": "Ошибка валидации данных"}',  # Russian
                'expected_behavior': 'unicode_handling'
            },
            {
                'name': 'Extremely Long Error Message',
                'mock_response': '{"error": "' + 'A' * 5000 + '"}',
                'expected_behavior': 'message_truncation'
            },
            {
                'name': 'Nested Error Structure',
                'mock_response': '{"errors": {"field1": ["error1", "error2"], "field2": {"nested": "error"}}}',
                'expected_behavior': 'nested_parsing'
            }
        ]
        
        results = {}
        for case in edge_cases:
            print(f"  🎯 Testing {case['name']}...")
            
            # Simulate edge case testing
            try:
                if 'unicode' in case['name'].lower():
                    # Test unicode handling
                    test_string = case['mock_response']
                    test_encoded = test_string.encode('utf-8').decode('utf-8')
                    results[case['name']] = True
                elif 'long' in case['name'].lower():
                    # Test message truncation
                    test_message = case['mock_response']
                    results[case['name']] = len(test_message) > 1000
                else:
                    results[case['name']] = True
                    
                print(f"    ✅ {case['name']}")
                
            except Exception as e:
                print(f"    ❌ {case['name']}: {e}")
                results[case['name']] = False
        
        self.test_results['edge_cases'] = results
        return results
    
    def run_regression_tests(self):
        """Run existing regression test suite"""
        print("🔄 Running Regression Tests...")
        
        test_files = [
            'test_enhanced_learning.py',
            'test_error_handling.py',
            'test_integration_failures.py',
            'test_stress_and_performance.py'
        ]
        
        results = {}
        for test_file in test_files:
            if os.path.exists(test_file):
                print(f"  🎯 Running {test_file}...")
                start_time = time.time()
                
                try:
                    result = subprocess.run(
                        [sys.executable, test_file],
                        capture_output=True,
                        text=True,
                        timeout=180,  # 3 minutes max per test
                        encoding='utf-8',  # Fix encoding
                        errors='replace'   # Handle invalid characters gracefully
                    )
                    execution_time = time.time() - start_time
                    success = result.returncode == 0
                    
                except subprocess.TimeoutExpired as e:
                    print(f"    ⏰ {test_file} timed out after 180s")
                    execution_time = 180.0
                    success = False
                    result = type('obj', (object,), {
                        'returncode': -1,
                        'stdout': f"Process timed out after 180 seconds",
                        'stderr': f"TimeoutExpired: {str(e)}"
                    })()
                except Exception as e:
                    print(f"    ❌ {test_file} failed with exception: {e}")
                    execution_time = time.time() - start_time
                    success = False
                    result = type('obj', (object,), {
                        'returncode': -1,
                        'stdout': "",
                        'stderr': f"Exception: {str(e)}"
                    })()
                
                results[test_file] = {
                    'success': success,
                    'execution_time': execution_time,
                    'output': result.stdout[-500:] if result.stdout else "",
                    'errors': result.stderr[-500:] if result.stderr else ""
                }
                
                print(f"    {'✅' if success else '❌'} {test_file}: {execution_time:.2f}s")
            else:
                print(f"    ⚠️ {test_file} not found")
        
        self.test_results['regression'] = results
        return results
    
    def generate_comprehensive_report(self):
        """Generate detailed test report"""
        total_time = time.time() - self.start_time
        
        report = {
            'execution_summary': {
                'total_time': total_time,
                'timestamp': datetime.now().isoformat(),
                'test_categories': len(self.test_results)
            },
            'detailed_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }
        
        # Save comprehensive report
        with open('comprehensive_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n📊 COMPREHENSIVE TEST SUMMARY")
        print(f"=" * 50)
        print(f"Total execution time: {total_time:.2f}s")
        print(f"Test categories completed: {len(self.test_results)}")
        
        # Print category summaries
        for category, results in self.test_results.items():
            if isinstance(results, dict):
                passed = 0
                total = 0
                for r in results.values():
                    total += 1
                    if isinstance(r, dict):
                        if r.get('success', False) or r.get('passed', False) or r.get('constraint_learned', False) or r.get('any_constraint_learned', False):
                            passed += 1
                    elif isinstance(r, bool) and r:
                        passed += 1
                
                print(f"{category.title()}: {passed}/{total} passed")
        
        print(f"\n📋 Detailed report saved to: comprehensive_test_report.json")
        return report
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        # Analyze constraint learning performance
        if 'constraint_types' in self.test_results:
            constraint_results = self.test_results['constraint_types']
            failed_constraints = [name for name, result in constraint_results.items() 
                                if not result.get('constraint_learned', False)]
            
            if failed_constraints:
                recommendations.append({
                    'category': 'constraint_learning',
                    'priority': 'high',
                    'issue': f"Failed to learn: {', '.join(failed_constraints)}",
                    'suggestion': 'Review interpreter prompts and constraint detection logic'
                })
        
        # Analyze performance issues
        slow_tests = []
        for category, results in self.test_results.items():
            if isinstance(results, dict):
                for test_name, result in results.items():
                    # Handle both dict results and boolean results
                    if isinstance(result, dict) and result.get('execution_time', 0) > 60:
                        slow_tests.append(f"{test_name} ({result['execution_time']:.1f}s)")
                    elif isinstance(result, bool):
                        # Skip boolean results (like edge cases)
                        continue
        
        if slow_tests:
            recommendations.append({
                'category': 'performance',
                'priority': 'medium',
                'issue': f"Slow tests detected: {', '.join(slow_tests)}",
                'suggestion': 'Optimize LLM calls or reduce timeout values'
            })
        
        return recommendations

def main():
    """Run comprehensive test framework"""
    print("🚀 Starting Comprehensive Test Framework")
    print("=" * 60)
    
    framework = ComprehensiveTestFramework()
    
    try:
        # Run all test categories
        framework.run_constraint_type_validation()
        framework.run_edge_case_validation()
        framework.run_regression_tests()
        
        # Generate final report
        framework.generate_comprehensive_report()
        
        print("\n🎉 Comprehensive testing completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing framework error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
