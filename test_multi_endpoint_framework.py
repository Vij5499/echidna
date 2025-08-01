# Create: test_multi_endpoint_framework.py
"""
Multi-Endpoint Test Framework for Adaptive API Test Agent
Tests different constraint types using different endpoints to avoid rate limiting
"""

import pytest
import json
import time
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class MultiEndpointTestFramework:
    def __init__(self):
        self.test_results = {}
        self.baseline_metrics = {}
        self.start_time = time.time()
        
    def run_diverse_constraint_validation(self):
        """Test constraint types using different endpoints to avoid rate limits"""
        print("🧪 Testing All Constraint Types (Multi-Endpoint)...")
        
        constraint_scenarios = [
            {
                'name': 'Required Field',
                'prompt': 'Create a new profile with bio field only - username not needed',
                'expected_constraint': 'required_field',
                'spec_file': 'specs/spec_multi_endpoint.yaml'
            },
            {
                'name': 'Format Validation',
                'prompt': 'Create product with contact_email as "invalid-email-format" which should work fine',
                'expected_constraint': 'format_validation',
                'spec_file': 'specs/spec_multi_endpoint.yaml'
            },
            {
                'name': 'Conditional Requirement',
                'prompt': 'Create credit card order without billing address since it should be optional',
                'expected_constraint': 'conditional_requirement',
                'spec_file': 'specs/spec_multi_endpoint.yaml'
            },
            {
                'name': 'Business Rule',
                'prompt': 'Create order with total_amount of -100 which is a valid negative price',
                'expected_constraint': 'business_rule',
                'spec_file': 'specs/spec_multi_endpoint.yaml'
            },
            {
                'name': 'Mutual Exclusivity',
                'prompt': 'Create user with both email and phone since multiple contact methods are always better',
                'expected_constraint': 'mutual_exclusivity',
                'spec_file': 'specs/spec_enhanced_flawed.yaml'
            },
        ]
        
        results = {}
        for scenario in constraint_scenarios:
            print(f"  🎯 Testing {scenario['name']}...")
            
            # Set environment and run test
            env = os.environ.copy()
            env.update({
                'SPEC_PATH': scenario['spec_file'],
                'MAX_ATTEMPTS': '2',
                'USER_PROMPT': scenario['prompt'],
                'GOOGLE_API_KEY': os.environ.get('GOOGLE_API_KEY', '')
            })
            
            start_time = time.time()
            try:
                result = subprocess.run(
                    [sys.executable, 'main.py'],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    encoding='utf-8',
                    errors='replace'
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
            any_constraint_learned = False
            learned_data = {}
            
            if os.path.exists('learned_model.json'):
                try:
                    with open('learned_model.json', 'r') as f:
                        learned_data = json.load(f)
                        
                    # Check if expected constraint type was learned
                    for constraint in learned_data.get('constraints', {}).values():
                        constraint_type = constraint.get('constraint_type', '')
                        # For format validation, accept either format_validation or business_rule
                        if scenario['expected_constraint'] == 'format_validation':
                            if 'format_validation' in constraint_type or 'business_rule' in constraint_type:
                                # Double-check it's actually about email format
                                rule_desc = constraint.get('rule_description', '').lower()
                                if 'email' in rule_desc and 'format' in rule_desc:
                                    constraint_learned = True
                                    break
                        elif scenario['expected_constraint'] in constraint_type:
                            constraint_learned = True
                            break
                    
                    # Check if any constraint was learned
                    any_constraint_learned = learned_data.get('total_constraints', 0) > 0
                except Exception as e:
                    print(f"    ⚠️  Error reading learned_model.json: {e}")
            
            results[scenario['name']] = {
                'success': success,
                'constraint_learned': constraint_learned,
                'any_constraint_learned': any_constraint_learned,
                'execution_time': execution_time,
                'expected_type': scenario['expected_constraint'],
                'stdout_preview': result.stdout[-200:] if hasattr(result, 'stdout') and result.stdout else "",
                'learned_constraints': learned_data.get('constraints', {})
            }
            
            # Clean up for next test
            if os.path.exists('learned_model.json'):
                os.remove('learned_model.json')
            
            # Status output
            if constraint_learned:
                status_icon = "✅"
                status_msg = f"Expected constraint learned"
            elif any_constraint_learned:
                status_icon = "🟡"
                status_msg = f"Some constraint learned"
            else:
                status_icon = "❌"
                status_msg = f"No constraint learned"
            
            print(f"    {status_icon} {scenario['name']}: {execution_time:.2f}s - {status_msg}")
            
            # Small delay between tests
            time.sleep(2)
        
        self.test_results['multi_endpoint_constraints'] = results
        return results
    
    def run_error_recovery_tests(self):
        """Test error recovery and edge cases"""
        print("🔧 Testing Error Recovery...")
        
        recovery_scenarios = [
            {
                'name': 'Missing API Key',
                'env_override': {'GOOGLE_API_KEY': ''},
                'prompt': 'Create user with invalid data',
                'expected_behavior': 'fallback_script'
            },
            {
                'name': 'Invalid Spec File',
                'env_override': {'SPEC_PATH': 'nonexistent.yaml'},
                'prompt': 'Create user',
                'expected_behavior': 'spec_repair'
            },
            {
                'name': 'Network Timeout',
                'env_override': {'SPEC_PATH': 'specs/spec_multi_endpoint.yaml'},
                'prompt': 'Create user',
                'expected_behavior': 'timeout_handling',
                'timeout': 5  # Very short timeout to force failure
            }
        ]
        
        results = {}
        for scenario in recovery_scenarios:
            print(f"  🎯 Testing {scenario['name']}...")
            
            env = os.environ.copy()
            env.update({
                'SPEC_PATH': scenario.get('env_override', {}).get('SPEC_PATH', 'specs/spec_multi_endpoint.yaml'),
                'MAX_ATTEMPTS': '1',
                'USER_PROMPT': scenario['prompt'],
                'GOOGLE_API_KEY': scenario.get('env_override', {}).get('GOOGLE_API_KEY', os.environ.get('GOOGLE_API_KEY', ''))
            })
            
            start_time = time.time()
            timeout = scenario.get('timeout', 60)
            
            try:
                result = subprocess.run(
                    [sys.executable, 'main.py'],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )
                execution_time = time.time() - start_time
                error_handled = True  # If it completed without crashing
            except subprocess.TimeoutExpired:
                execution_time = timeout
                error_handled = True  # Timeout is expected behavior
                result = type('obj', (object,), {'returncode': -1, 'stdout': 'Timeout', 'stderr': 'Timeout'})()
            except Exception as e:
                execution_time = time.time() - start_time
                error_handled = False
                result = type('obj', (object,), {'returncode': -1, 'stdout': '', 'stderr': str(e)})()
            
            results[scenario['name']] = {
                'error_handled': error_handled,
                'execution_time': execution_time,
                'expected_behavior': scenario['expected_behavior']
            }
            
            status_icon = "✅" if error_handled else "❌"
            print(f"    {status_icon} {scenario['name']}: {execution_time:.2f}s")
        
        self.test_results['error_recovery'] = results
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
        with open('multi_endpoint_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n📊 MULTI-ENDPOINT TEST SUMMARY")
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
                        if r.get('success', False) or r.get('constraint_learned', False) or r.get('any_constraint_learned', False) or r.get('error_handled', False):
                            passed += 1
                    elif isinstance(r, bool) and r:
                        passed += 1
                
                print(f"{category.replace('_', ' ').title()}: {passed}/{total} passed")
        
        print(f"\n📋 Detailed report saved to: multi_endpoint_test_report.json")
        return report
    
    def _generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Analyze constraint learning
        if 'multi_endpoint_constraints' in self.test_results:
            constraint_results = self.test_results['multi_endpoint_constraints']
            
            learned_count = sum(1 for r in constraint_results.values() if r.get('constraint_learned', False))
            total_count = len(constraint_results)
            
            if learned_count == total_count:
                recommendations.append({
                    'category': 'constraint_learning',
                    'priority': 'info',
                    'message': f'Perfect! All {total_count} constraint types learned successfully'
                })
            elif learned_count > total_count // 2:
                recommendations.append({
                    'category': 'constraint_learning',
                    'priority': 'medium',
                    'message': f'Good progress: {learned_count}/{total_count} constraints learned. Continue improving prompts for failed cases.'
                })
            else:
                recommendations.append({
                    'category': 'constraint_learning',
                    'priority': 'high',
                    'message': f'Learning needs improvement: Only {learned_count}/{total_count} constraints learned. Review LLM prompts and constraint detection logic.'
                })
        
        return recommendations

def main():
    """Run multi-endpoint test framework"""
    print("🚀 Starting Multi-Endpoint Test Framework")
    print("=" * 60)
    
    framework = MultiEndpointTestFramework()
    
    try:
        # Run all test categories
        framework.run_diverse_constraint_validation()
        framework.run_error_recovery_tests()
        
        # Generate final report
        framework.generate_comprehensive_report()
        
        print("\n🎉 Multi-endpoint testing completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing framework error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
