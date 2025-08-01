#!/usr/bin/env python3
"""
Quick Constraint Validation Test
Tests all 8 constraint types to ensure they're properly handled
"""

import subprocess
import os
import sys
import time
import json

def test_all_constraint_types():
    """Test all constraint types defined in the system"""
    
    print("🎯 TESTING ALL 8 CONSTRAINT TYPES")
    print("="*50)
    
    # All constraint scenarios
    constraint_scenarios = [
        {
            'name': 'Required Field',
            'prompt': 'Create user without mandatory name field',
            'expected_constraint': 'required_field'
        },
        {
            'name': 'Format Validation', 
            'prompt': 'Create user with invalid email format like "not-an-email"',
            'expected_constraint': 'format_validation'
        },
        {
            'name': 'Conditional Requirement',
            'prompt': 'Create user with premium features but without premium subscription',
            'expected_constraint': 'conditional_requirement'
        },
        {
            'name': 'Mutual Exclusivity',
            'prompt': 'Create user with both email and phone contact methods',
            'expected_constraint': 'mutual_exclusivity'
        },
        {
            'name': 'Format Dependency',
            'prompt': 'Create user with country code but invalid phone format for that country',
            'expected_constraint': 'format_dependency'
        },
        {
            'name': 'Business Rule',
            'prompt': 'Create user with age less than minimum required age of 13',
            'expected_constraint': 'business_rule'
        },
        {
            'name': 'Value Constraint',
            'prompt': 'Create user with negative age value which should be invalid',
            'expected_constraint': 'value_constraint'
        },
        {
            'name': 'Rate Limiting',
            'prompt': 'Make rapid consecutive requests to trigger rate limiting',
            'expected_constraint': 'rate_limiting'
        }
    ]
    
    results = {}
    total_tested = 0
    total_learned = 0
    
    for i, scenario in enumerate(constraint_scenarios, 1):
        print(f"\n🧪 Test {i}/8: {scenario['name']}")
        print(f"   Prompt: {scenario['prompt']}")
        
        # Clean up any existing learned model
        if os.path.exists('learned_model.json'):
            os.remove('learned_model.json')
        
        # Set environment for test
        env = os.environ.copy()
        env.update({
            'SPEC_PATH': 'specs/spec_enhanced_flawed.yaml',
            'MAX_ATTEMPTS': '1',
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
                timeout=60,  # Quick test - 60 second timeout
                encoding='utf-8',
                errors='replace'
            )
            execution_time = time.time() - start_time
            
            # Check if any constraint was learned
            constraint_learned = False
            learned_type = "none"
            
            if os.path.exists('learned_model.json'):
                try:
                    with open('learned_model.json', 'r') as f:
                        learned_data = json.load(f)
                        if learned_data.get('total_constraints', 0) > 0:
                            constraint_learned = True
                            # Get the constraint type that was learned
                            constraints = learned_data.get('constraints', {})
                            if constraints:
                                first_constraint = list(constraints.values())[0]
                                learned_type = first_constraint.get('constraint_type', 'unknown')
                            total_learned += 1
                except Exception as e:
                    print(f"   ⚠️  Error reading learned model: {e}")
            
            total_tested += 1
            
            status = "✅" if constraint_learned else "❌"
            print(f"   {status} Result: {learned_type} constraint ({execution_time:.2f}s)")
            
            results[scenario['name']] = {
                'success': constraint_learned,
                'learned_type': learned_type,
                'expected_type': scenario['expected_constraint'],
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout (60s)")
            results[scenario['name']] = {
                'success': False,
                'learned_type': 'timeout',
                'expected_type': scenario['expected_constraint'],
                'execution_time': 60.0
            }
            total_tested += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[scenario['name']] = {
                'success': False,
                'learned_type': 'error',
                'expected_type': scenario['expected_constraint'],
                'execution_time': 0
            }
            total_tested += 1
        
        # Brief pause between tests
        if i < len(constraint_scenarios):
            time.sleep(2)
    
    # Summary
    print(f"\n📊 CONSTRAINT TYPE VALIDATION SUMMARY")
    print("="*50)
    print(f"Total constraint types tested: {total_tested}/8")
    print(f"Constraints successfully learned: {total_learned}")
    print(f"Success rate: {(total_learned/total_tested)*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        learned = result['learned_type']
        expected = result['expected_type']
        time_taken = result['execution_time']
        
        match_icon = "🎯" if learned == expected else ("🔄" if learned != "none" and learned != "timeout" and learned != "error" else "❌")
        
        print(f"   {status} {test_name}")
        print(f"      Expected: {expected}")
        print(f"      Learned: {learned} {match_icon}")
        print(f"      Time: {time_taken:.2f}s")
    
    # Analysis
    exact_matches = sum(1 for r in results.values() if r['learned_type'] == r['expected_type'])
    any_learning = sum(1 for r in results.values() if r['success'])
    
    print(f"\n🎯 ANALYSIS:")
    print(f"   Exact constraint type matches: {exact_matches}/8")
    print(f"   Any constraint learned: {any_learning}/8") 
    print(f"   System demonstrates constraint learning: {'Yes' if any_learning > 0 else 'No'}")
    
    if any_learning >= 4:
        print(f"   🎉 GOOD: System successfully learns constraints!")
    elif any_learning >= 2:
        print(f"   🔧 FAIR: System shows learning capability, needs tuning")
    else:
        print(f"   ⚠️  NEEDS WORK: Limited constraint learning observed")
    
    return results

if __name__ == "__main__":
    test_all_constraint_types()
