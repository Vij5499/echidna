#!/usr/bin/env python3
"""
Enhanced Real-World API Testing with Multiple Public APIs
Tests Echidna against various real APIs with different constraint patterns
"""

import os
import json
import time
import requests
import subprocess
import sys
from datetime import datetime

class EnhancedRealWorldTester:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    def test_github_api(self):
        """Test against GitHub API (no auth required for some endpoints)"""
        print("\n🐙 TESTING GITHUB API")
        print("-" * 40)
        
        # Create GitHub API spec with intentional gaps
        github_spec = """openapi: 3.0.0
info:
  title: GitHub API (Real-World Test)
  version: 3.0.0
  description: GitHub REST API for Echidna testing

servers:
  - url: https://api.github.com

paths:
  /gists:
    post:
      summary: Create a gist
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                description:
                  type: string
                public:
                  type: boolean
                files:
                  type: object
              # INTENTIONALLY MISSING: Required fields and constraints
      responses:
        '201':
          description: Gist created
        '400':
          description: Bad request
        '401':
          description: Unauthorized
"""
        
        # Write spec
        with open('specs/real_world_github.yaml', 'w') as f:
            f.write(github_spec)
        
        # Test scenarios for GitHub API
        scenarios = [
            {
                'prompt': 'Create gist without files property since description should be enough',
                'expected': 'files field requirement'
            },
            {
                'prompt': 'Create gist with empty files object which should work fine',
                'expected': 'files content validation'
            }
        ]
        
        return self._run_api_tests('GitHub', 'specs/real_world_github.yaml', scenarios)
    
    def test_catfact_api(self):
        """Test against Cat Facts API"""
        print("\n🐱 TESTING CAT FACTS API")
        print("-" * 40)
        
        # Test if API is available first
        try:
            response = requests.get('https://catfact.ninja/fact', timeout=5)
            if response.status_code != 200:
                print("   ❌ Cat Facts API not available")
                return {'success': False, 'reason': 'API unavailable'}
        except:
            print("   ❌ Cat Facts API not accessible")
            return {'success': False, 'reason': 'API not accessible'}
        
        catfact_spec = """openapi: 3.0.0
info:
  title: Cat Facts API (Real-World Test)  
  version: 1.0.0
  description: Cat Facts API for Echidna testing

servers:
  - url: https://catfact.ninja

paths:
  /fact:
    get:
      summary: Get random cat fact
      parameters:
        - name: max_length
          in: query
          schema:
            type: integer
        # INTENTIONALLY MISSING: Parameter constraints
      responses:
        '200':
          description: Cat fact returned
        '400':
          description: Bad request
"""
        
        with open('specs/real_world_catfacts.yaml', 'w') as f:
            f.write(catfact_spec)
        
        scenarios = [
            {
                'prompt': 'Get cat fact with max_length of -1 which should work fine',
                'expected': 'parameter validation constraints'
            }
        ]
        
        return self._run_api_tests('CatFacts', 'specs/real_world_catfacts.yaml', scenarios)
    
    def test_postman_echo_api(self):
        """Test against Postman Echo API"""
        print("\n📮 TESTING POSTMAN ECHO API")
        print("-" * 40)
        
        # Test availability
        try:
            response = requests.get('https://postman-echo.com/get', timeout=5)
            if response.status_code != 200:
                print("   ❌ Postman Echo API not available")
                return {'success': False, 'reason': 'API unavailable'}
        except:
            print("   ❌ Postman Echo API not accessible")
            return {'success': False, 'reason': 'API not accessible'}
        
        postman_spec = """openapi: 3.0.0
info:
  title: Postman Echo API (Real-World Test)
  version: 1.0.0
  description: Postman Echo API for testing

servers:
  - url: https://postman-echo.com

paths:
  /post:
    post:
      summary: Echo POST data
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: string
                number:
                  type: integer
                email:
                  type: string
              # INTENTIONALLY MISSING: Validation rules
      responses:
        '200':
          description: Data echoed back
        '400':
          description: Bad request

  /headers:
    post:
      summary: Echo headers
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                test:
                  type: string
      responses:
        '200':
          description: Headers echoed
"""
        
        with open('specs/real_world_postman.yaml', 'w') as f:
            f.write(postman_spec)
        
        scenarios = [
            {
                'prompt': 'Send POST with email field as "invalid-email" which should work',
                'expected': 'email format validation'
            },
            {
                'prompt': 'Send POST with very long data string to test limits',
                'expected': 'data length constraints'
            }
        ]
        
        return self._run_api_tests('PostmanEcho', 'specs/real_world_postman.yaml', scenarios)
    
    def test_dog_api(self):
        """Test against Dog API"""
        print("\n🐕 TESTING DOG API")
        print("-" * 40)
        
        try:
            response = requests.get('https://dog.ceo/api/breeds/list/all', timeout=5)
            if response.status_code != 200:
                print("   ❌ Dog API not available")
                return {'success': False, 'reason': 'API unavailable'}
        except:
            print("   ❌ Dog API not accessible")
            return {'success': False, 'reason': 'API not accessible'}
        
        dog_spec = """openapi: 3.0.0
info:
  title: Dog API (Real-World Test)
  version: 1.0.0
  description: Dog API for breed information

servers:
  - url: https://dog.ceo/api

paths:
  /breed/{breed}/images/random:
    get:
      summary: Get random dog image by breed
      parameters:
        - name: breed
          in: path
          required: true
          schema:
            type: string
          # INTENTIONALLY MISSING: Valid breed validation
      responses:
        '200':
          description: Dog image URL
        '404':
          description: Breed not found
"""
        
        with open('specs/real_world_dog.yaml', 'w') as f:
            f.write(dog_spec)
        
        scenarios = [
            {
                'prompt': 'Get image for breed "invalid-breed-name" which should work',
                'expected': 'valid breed name constraint'
            }
        ]
        
        return self._run_api_tests('DogAPI', 'specs/real_world_dog.yaml', scenarios)
    
    def _run_api_tests(self, api_name, spec_file, scenarios):
        """Run tests for a specific API"""
        results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"   🧪 {api_name} Test {i}: {scenario['prompt'][:50]}...")
            
            # Clean up
            for file in ['learned_model.json', 'pattern_analysis.json']:
                if os.path.exists(file):
                    os.remove(file)
            
            # Set environment
            env = os.environ.copy()
            env.update({
                'SPEC_PATH': spec_file,
                'MAX_ATTEMPTS': '1',
                'USER_PROMPT': scenario['prompt'],
                'PYTHONIOENCODING': 'utf-8'
            })
            
            start_time = time.time()
            try:
                result = subprocess.run(
                    [sys.executable, 'main.py'],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    encoding='utf-8',
                    errors='replace'
                )
                
                duration = time.time() - start_time
                
                # Check for learning
                constraint_learned = False
                learned_details = {}
                
                if os.path.exists('learned_model.json'):
                    try:
                        with open('learned_model.json', 'r') as f:
                            data = json.load(f)
                        if data.get('total_constraints', 0) > 0:
                            constraint_learned = True
                            constraints = data.get('constraints', {})
                            if constraints:
                                key = list(constraints.keys())[0]
                                learned_details = constraints[key]
                    except:
                        pass
                
                if constraint_learned:
                    print(f"      ✅ Learned: {learned_details.get('constraint_type', 'unknown')}")
                else:
                    print(f"      ❌ No constraint learned")
                
                results.append({
                    'api': api_name,
                    'scenario': scenario['prompt'][:30] + '...',
                    'success': constraint_learned,
                    'duration': duration,
                    'learned_details': learned_details,
                    'expected': scenario['expected']
                })
                
            except subprocess.TimeoutExpired:
                print(f"      ⏰ Timeout")
                results.append({
                    'api': api_name,
                    'scenario': scenario['prompt'][:30] + '...',
                    'success': False,
                    'duration': 120,
                    'learned_details': {},
                    'expected': scenario['expected']
                })
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:30]}")
                results.append({
                    'api': api_name,
                    'scenario': scenario['prompt'][:30] + '...',
                    'success': False,
                    'duration': 0,
                    'learned_details': {},
                    'expected': scenario['expected']
                })
        
        return {'success': True, 'results': results}
    
    def run_comprehensive_real_world_test(self):
        """Run comprehensive real-world testing across multiple APIs"""
        print("🌍 COMPREHENSIVE REAL-WORLD API TESTING")
        print("="*60)
        print("Testing Echidna against multiple real-world APIs...")
        print()
        
        all_results = []
        
        # Test different APIs
        api_tests = [
            ('GitHub API', self.test_github_api),
            ('Cat Facts API', self.test_catfact_api),
            ('Postman Echo API', self.test_postman_echo_api),
            ('Dog API', self.test_dog_api),
        ]
        
        for api_name, test_func in api_tests:
            try:
                result = test_func()
                if result.get('success') and 'results' in result:
                    all_results.extend(result['results'])
                time.sleep(1)  # Brief pause between API tests
            except Exception as e:
                print(f"   ❌ {api_name} test failed: {str(e)}")
        
        # Generate comprehensive report
        self._generate_comprehensive_report(all_results)
    
    def _generate_comprehensive_report(self, results):
        """Generate final comprehensive real-world testing report"""
        total_time = time.time() - self.start_time
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        print(f"\n" + "="*70)
        print("🌍 COMPREHENSIVE REAL-WORLD TESTING REPORT")
        print("="*70)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Duration: {total_time:.1f} seconds")
        print(f"🌐 APIs Tested: {len(set(r['api'] for r in results))}")
        print(f"🧪 Total Scenarios: {total}")
        print(f"✅ Successful Learning: {successful}")
        print(f"📊 Real-World Success Rate: {success_rate:.1f}%")
        
        # API breakdown
        print(f"\n📋 RESULTS BY API:")
        api_groups = {}
        for result in results:
            api = result['api']
            if api not in api_groups:
                api_groups[api] = []
            api_groups[api].append(result)
        
        for api, api_results in api_groups.items():
            api_success = sum(1 for r in api_results if r['success'])
            api_total = len(api_results)
            print(f"   🔌 {api}: {api_success}/{api_total} scenarios successful")
            
            for result in api_results:
                status = "✅" if result['success'] else "❌"
                print(f"      {status} {result['scenario']} ({result['duration']:.1f}s)")
                if result['success']:
                    details = result['learned_details']
                    print(f"         └─ Learned: {details.get('constraint_type', 'unknown')} constraint")
        
        # Overall assessment
        print(f"\n🏆 REAL-WORLD PERFORMANCE ASSESSMENT:")
        if success_rate >= 70:
            grade = "A"
            assessment = "EXCELLENT - Your Echidna system excels with real-world APIs!"
        elif success_rate >= 50:
            grade = "B+"
            assessment = "VERY GOOD - Strong real-world performance demonstrated!"
        elif success_rate >= 30:
            grade = "B"
            assessment = "GOOD - Solid real-world learning capability shown!"
        elif success_rate >= 15:
            grade = "B-"
            assessment = "FAIR - Some real-world learning demonstrated!"
        else:
            grade = "C+"
            assessment = "NEEDS IMPROVEMENT - Real-world APIs present challenges!"
        
        print(f"   📈 Real-World Grade: {grade}")
        print(f"   💬 Assessment: {assessment}")
        
        # Key insights
        print(f"\n🔍 REAL-WORLD INSIGHTS:")
        learned_types = [r['learned_details'].get('constraint_type') for r in results if r['success']]
        if learned_types:
            unique_types = set(filter(None, learned_types))
            print(f"   🧠 Constraint types discovered from real APIs: {', '.join(unique_types)}")
        
        avg_time = sum(r['duration'] for r in results) / len(results) if results else 0
        print(f"   ⚡ Average processing time per real API: {avg_time:.1f}s")
        
        apis_with_success = set(r['api'] for r in results if r['success'])
        total_apis = set(r['api'] for r in results)
        print(f"   🌐 APIs with successful learning: {len(apis_with_success)}/{len(total_apis)}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if success_rate < 50:
            print("   🔧 Consider enhancing prompts for better real-world constraint detection")
            print("   🎯 Some real APIs may not enforce constraints as expected")
        
        if success_rate >= 30:
            print("   ✨ Your system shows promising real-world adaptability!")
            print("   🚀 Consider testing with more complex enterprise APIs")
        
        # Save report
        report = {
            'summary': {
                'test_date': datetime.now().isoformat(),
                'total_duration': total_time,
                'apis_tested': len(total_apis),
                'total_scenarios': total,
                'successful_learning': successful,
                'success_rate': success_rate,
                'grade': grade,
                'assessment': assessment
            },
            'detailed_results': results
        }
        
        with open('comprehensive_real_world_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Comprehensive report saved to: comprehensive_real_world_report.json")
        print(f"🎉 Comprehensive real-world testing complete! Final Grade: {grade}")

def main():
    """Main execution function"""
    tester = EnhancedRealWorldTester()
    tester.run_comprehensive_real_world_test()

if __name__ == "__main__":
    main()
