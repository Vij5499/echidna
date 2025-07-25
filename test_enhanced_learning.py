# test_enhanced_learning.py - Complete Fixed Version
import subprocess
import time
import requests
import json
import sys
import os

def test_api_connection():
    """Test that the enhanced mock API is responding"""
    try:
        # Test the actual endpoint that should trigger learning
        test_data = {
            "name": "Test User",
            "username": "testuser",
            "email": "test@example.com",
            "phone": "123-456-7890"
        }
        
        response = requests.post('http://localhost:5000/users', json=test_data, timeout=5)
        print(f"✅ API Users Endpoint: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        return response.status_code == 400  # Should return 400 for mutual exclusivity
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return False

def test_enhanced_constraint_learning():
    """Test the enhanced constraint learning capabilities"""
    
    print("🚀 Testing Enhanced Constraint Learning...")
    
    # Start enhanced mock API using the same Python interpreter
    print("🔄 Starting enhanced mock API...")
    api_process = subprocess.Popen([sys.executable, 'enhanced_mock_api.py'])
    time.sleep(5)  # Give more time for API to start
    
    # Test API connectivity first
    print("🔧 Testing API connectivity...")
    if not test_api_connection():
        print("❌ API connectivity issues detected")
        api_process.terminate()
        return
    
    print("✅ API is working correctly")
    
    try:
        # Test scenarios that should trigger different constraint types
        test_scenarios = [
            {
                'name': 'Mutual Exclusivity Test',
                'prompt': 'Create a user with both email and phone contact methods',
                'expected_learning': 'either email or phone, not both'
            },
            {
                'name': 'Business Rule Test',
                'prompt': 'Create a user account for a 16-year-old person',
                'expected_learning': 'age must be at least 18'
            },
            {
                'name': 'Conditional Requirement Test',
                'prompt': 'Create a premium user account with all required information',
                'expected_learning': 'email required when account_type is premium'
            }
        ]
        
        total_learning_detected = 0
        
        for scenario in test_scenarios:
            print(f"\n📋 Testing: {scenario['name']}")
            print(f"🎯 Expected Learning: {scenario['expected_learning']}")
            
            # Create environment with UTF-8 encoding
            env = os.environ.copy()
            env.update({
                'SPEC_PATH': 'specs/spec_enhanced_flawed.yaml',
                'MAX_ATTEMPTS': '3',
                'USER_PROMPT': scenario['prompt'],
                # CRITICAL: Set UTF-8 encoding for subprocess
                'PYTHONIOENCODING': 'utf-8',
                'PYTHONLEGACYWINDOWSSTDIO': '0'
            })
            
            print("🔄 Running main.py subprocess with UTF-8 encoding...")
            result = subprocess.run(
                [sys.executable, 'main.py'],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',  # Explicitly set encoding
                errors='replace'   # Replace problematic characters instead of failing
            )
            
            print(f"✅ Subprocess completed with return code: {result.returncode}")
            
            # Show first 1000 chars of output for debugging
            if result.stdout:
                print("🔍 SUBPROCESS OUTPUT (first 1000 chars):")
                print("="*50)
                print(result.stdout[:1000])
                print("="*50)
            
            if result.stderr:
                print("🔍 SUBPROCESS ERRORS:")
                print("="*50)
                print(result.stderr[:500])  # Show first 500 chars of errors
                print("="*50)
            
            # Enhanced learning detection logic
            learning_indicators = [
                'new constraint learned',
                'successfully created enhanced learned constraint',
                'constraints learned: 1',
                'constraints learned: 2',
                'constraints learned: 3',
                'mutual_exclusivity',
                'conditional_requirement', 
                'business_rule',
                'rate_limiting',
                'format_dependency'
            ]
            
            learning_detected = False
            constraints_found = []
            
            if result.stdout:
                output_lower = result.stdout.lower()
                for indicator in learning_indicators:
                    if indicator in output_lower:
                        learning_detected = True
                        constraints_found.append(indicator)
            
            if learning_detected:
                print(f"🧠 Learning detected! Found indicators: {constraints_found}")
                total_learning_detected += 1
                
                # Show learning summary from output
                if 'constraints learned:' in output_lower:
                    for line in result.stdout.split('\n'):
                        if 'constraints learned:' in line.lower():
                            print(f"   📊 {line.strip()}")
            else:
                print(f"⚠️ No learning detected")
                
            # Add delay between tests to avoid rate limiting interference
            print("⏳ Waiting 15 seconds to avoid rate limiting...")
            time.sleep(15)
            
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        api_process.terminate()
        time.sleep(1)
        
    print(f"\n🎉 Enhanced constraint learning test complete!")
    print(f"📊 Learning detected in {total_learning_detected}/{len(test_scenarios)} scenarios")
    
    if total_learning_detected >= 2:
        print("✅ EXCELLENT: Enhanced constraint learning is working successfully!")
    elif total_learning_detected >= 1:
        print("✅ GOOD: Some learning detected, system is functional")
    else:
        print("⚠️ REVIEW NEEDED: Limited learning detected")

if __name__ == "__main__":
    test_enhanced_constraint_learning()
