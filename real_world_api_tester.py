#!/usr/bin/env python3
"""
Real-World API Testing Framework for Echidna
Tests the system against actual public APIs to validate real-world performance
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

class RealWorldAPITester:
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def discover_real_apis(self):
        """Discover publicly available APIs for testing"""
        print("🌐 DISCOVERING REAL-WORLD APIs FOR TESTING")
        print("="*60)
        
        # Test various public APIs to find suitable candidates
        api_candidates = [
            {
                'name': 'JSONPlaceholder',
                'base_url': 'https://jsonplaceholder.typicode.com',
                'endpoints': ['/posts', '/users', '/comments'],
                'description': 'Fake REST API for testing and prototyping'
            },
            {
                'name': 'ReqRes',
                'base_url': 'https://reqres.in/api',
                'endpoints': ['/users', '/register', '/login'],
                'description': 'Real API responses for frontend testing'
            },
            {
                'name': 'HTTPBin',
                'base_url': 'https://httpbin.org',
                'endpoints': ['/post', '/put', '/patch'],
                'description': 'HTTP request & response service'
            },
            {
                'name': 'Lorem Picsum',
                'base_url': 'https://picsum.photos',
                'endpoints': ['/200/300', '/v2/list'],
                'description': 'Lorem Ipsum for photos'
            }
        ]
        
        available_apis = []
        
        for api in api_candidates:
            print(f"\n🔍 Testing {api['name']}...")
            try:
                # Test basic connectivity
                response = requests.get(f"{api['base_url']}{api['endpoints'][0]}", timeout=10)
                if response.status_code in [200, 404, 405]:  # API is responding
                    print(f"   ✅ Available: {api['name']} - {api['description']}")
                    available_apis.append(api)
                else:
                    print(f"   ❌ Unavailable: {api['name']} (Status: {response.status_code})")
            except Exception as e:
                print(f"   ❌ Unavailable: {api['name']} (Error: {str(e)[:50]})")
        
        return available_apis
    
    def generate_real_world_specs(self, apis):
        """Generate OpenAPI specs for real-world APIs"""
        print(f"\n📝 GENERATING REAL-WORLD API SPECIFICATIONS")
        print("="*60)
        
        specs_created = []
        
        for api in apis:
            spec_filename = f"specs/real_world_{api['name'].lower().replace(' ', '_')}.yaml"
            
            if api['name'] == 'JSONPlaceholder':
                spec_content = self._create_jsonplaceholder_spec()
            elif api['name'] == 'ReqRes':
                spec_content = self._create_reqres_spec()
            elif api['name'] == 'HTTPBin':
                spec_content = self._create_httpbin_spec()
            else:
                continue
            
            # Create specs directory if it doesn't exist
            os.makedirs('specs', exist_ok=True)
            
            # Write spec file
            with open(spec_filename, 'w') as f:
                f.write(spec_content)
            
            specs_created.append({
                'api_name': api['name'],
                'spec_file': spec_filename,
                'base_url': api['base_url']
            })
            
            print(f"   ✅ Created: {spec_filename}")
        
        return specs_created
    
    def _create_jsonplaceholder_spec(self):
        """Create spec for JSONPlaceholder API with intentional gaps for learning"""
        return """openapi: 3.0.0
info:
  title: JSONPlaceholder API (Real-World Test)
  version: 1.0.0
  description: Real JSONPlaceholder API for Echidna testing

servers:
  - url: https://jsonplaceholder.typicode.com

paths:
  /posts:
    post:
      summary: Create a new post
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
                body:
                  type: string
                userId:
                  type: integer
              # INTENTIONALLY MISSING: Required fields not specified
      responses:
        '201':
          description: Post created successfully
        '400':
          description: Bad request

  /users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                username:
                  type: string
                email:
                  type: string
                phone:
                  type: string
              # INTENTIONALLY MISSING: Format validation and required fields
      responses:
        '201':
          description: User created successfully
        '400':
          description: Bad request

  /comments:
    post:
      summary: Create a new comment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                postId:
                  type: integer
                name:
                  type: string
                email:
                  type: string
                body:
                  type: string
              # INTENTIONALLY MISSING: Required field constraints
      responses:
        '201':
          description: Comment created successfully
        '400':
          description: Bad request
"""

    def _create_reqres_spec(self):
        """Create spec for ReqRes API with intentional gaps"""
        return """openapi: 3.0.0
info:
  title: ReqRes API (Real-World Test)
  version: 1.0.0
  description: Real ReqRes API for Echidna testing

servers:
  - url: https://reqres.in/api

paths:
  /users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                job:
                  type: string
              # INTENTIONALLY MISSING: Required field specification
      responses:
        '201':
          description: User created successfully
        '400':
          description: Bad request

  /register:
    post:
      summary: Register a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
              # INTENTIONALLY MISSING: Email format validation and required fields
      responses:
        '200':
          description: Registration successful
        '400':
          description: Bad request

  /login:
    post:
      summary: Login user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
              # INTENTIONALLY MISSING: Required field constraints
      responses:
        '200':
          description: Login successful
        '400':
          description: Bad request
"""

    def _create_httpbin_spec(self):
        """Create spec for HTTPBin API"""
        return """openapi: 3.0.0
info:
  title: HTTPBin API (Real-World Test)
  version: 1.0.0
  description: Real HTTPBin API for Echidna testing

servers:
  - url: https://httpbin.org

paths:
  /post:
    post:
      summary: HTTP POST method
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
              # INTENTIONALLY MISSING: Field constraints
      responses:
        '200':
          description: Request echoed back
        '400':
          description: Bad request

  /put:
    put:
      summary: HTTP PUT method
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
              # INTENTIONALLY MISSING: Required field specification
      responses:
        '200':
          description: Request echoed back
        '400':
          description: Bad request
"""

    def create_real_world_test_scenarios(self, specs):
        """Create test scenarios designed to discover real API constraints"""
        print(f"\n🎯 CREATING REAL-WORLD TEST SCENARIOS")
        print("="*60)
        
        scenarios = []
        
        for spec in specs:
            api_name = spec['api_name']
            
            if api_name == 'JSONPlaceholder':
                scenarios.extend([
                    {
                        'name': 'JSONPlaceholder - Missing Title',
                        'prompt': 'Create post without title field since it should be optional',
                        'spec_file': spec['spec_file'],
                        'expected_learning': 'Missing required fields or validation rules'
                    },
                    {
                        'name': 'JSONPlaceholder - Invalid User Data',
                        'prompt': 'Create user with minimal data only',
                        'spec_file': spec['spec_file'],
                        'expected_learning': 'Required field constraints'
                    }
                ])
            
            elif api_name == 'ReqRes':
                scenarios.extend([
                    {
                        'name': 'ReqRes - Registration without Email',
                        'prompt': 'Register user without email since username should work',
                        'spec_file': spec['spec_file'],
                        'expected_learning': 'Email requirement for registration'
                    },
                    {
                        'name': 'ReqRes - Invalid Email Format',
                        'prompt': 'Register with email "invalid-email" which should work',
                        'spec_file': spec['spec_file'],
                        'expected_learning': 'Email format validation'
                    }
                ])
            
            elif api_name == 'HTTPBin':
                scenarios.extend([
                    {
                        'name': 'HTTPBin - Empty POST',
                        'prompt': 'Send empty POST request to test minimal data requirements',
                        'spec_file': spec['spec_file'],
                        'expected_learning': 'Data requirements or validation'
                    }
                ])
        
        print(f"   📋 Created {len(scenarios)} real-world test scenarios")
        return scenarios

    def run_real_world_tests(self, scenarios):
        """Execute real-world API tests"""
        print(f"\n🚀 EXECUTING REAL-WORLD API TESTS")
        print("="*60)
        
        results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🧪 Test {i}/{len(scenarios)}: {scenario['name']}")
            print(f"   📝 Prompt: {scenario['prompt']}")
            
            # Clean up before test
            for file in ['learned_model.json', 'pattern_analysis.json']:
                if os.path.exists(file):
                    os.remove(file)
            
            # Set environment for real-world test
            env = os.environ.copy()
            env.update({
                'SPEC_PATH': scenario['spec_file'],
                'MAX_ATTEMPTS': '2',  # Allow more attempts for real APIs
                'USER_PROMPT': scenario['prompt'],
                'PYTHONIOENCODING': 'utf-8'
            })
            
            start_time = time.time()
            try:
                import subprocess
                import sys
                
                result = subprocess.run(
                    [sys.executable, 'main.py'],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=180,  # Longer timeout for real APIs
                    encoding='utf-8',
                    errors='replace'
                )
                
                duration = time.time() - start_time
                
                # Analyze results
                constraint_learned = False
                learned_details = {}
                
                if os.path.exists('learned_model.json'):
                    try:
                        with open('learned_model.json', 'r') as f:
                            learned_data = json.load(f)
                        
                        constraints = learned_data.get('constraints', {})
                        if constraints:
                            constraint_learned = True
                            constraint_key = list(constraints.keys())[0]
                            learned_details = constraints[constraint_key]
                    except Exception as e:
                        print(f"   ⚠️  Error reading learned model: {e}")
                
                # Report result
                if constraint_learned:
                    print(f"   ✅ SUCCESS: Learned constraint from real API!")
                    print(f"      Type: {learned_details.get('constraint_type', 'unknown')}")
                    print(f"      Rule: {learned_details.get('rule_description', 'N/A')[:60]}...")
                    print(f"      Confidence: {learned_details.get('confidence_score', 0):.0%}")
                else:
                    print(f"   ❌ No constraint learned (API may not enforce expected rules)")
                
                results.append({
                    'scenario': scenario['name'],
                    'success': constraint_learned,
                    'duration': duration,
                    'learned_details': learned_details,
                    'return_code': result.returncode,
                    'expected_learning': scenario['expected_learning']
                })
                
            except subprocess.TimeoutExpired:
                print(f"   ⏰ TIMEOUT: Test exceeded 180 seconds")
                results.append({
                    'scenario': scenario['name'],
                    'success': False,
                    'duration': 180,
                    'learned_details': {},
                    'return_code': -1,
                    'expected_learning': scenario['expected_learning']
                })
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                results.append({
                    'scenario': scenario['name'],
                    'success': False,
                    'duration': 0,
                    'learned_details': {},
                    'return_code': -1,
                    'expected_learning': scenario['expected_learning']
                })
            
            # Brief pause between tests
            time.sleep(2)
        
        return results

    def generate_real_world_report(self, results):
        """Generate comprehensive real-world testing report"""
        total_time = time.time() - self.start_time
        successful_tests = sum(1 for r in results if r['success'])
        total_tests = len(results)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n" + "="*70)
        print("🌐 REAL-WORLD API TESTING REPORT")
        print("="*70)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Duration: {total_time:.1f} seconds")
        print(f"🎯 Tests Executed: {total_tests}")
        print(f"✅ Constraints Learned: {successful_tests}")
        print(f"📊 Real-World Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED REAL-WORLD RESULTS:")
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['scenario']} ({result['duration']:.1f}s)")
            if result['success']:
                details = result['learned_details']
                print(f"      └─ Learned: {details.get('constraint_type', 'unknown')} constraint")
                print(f"      └─ Confidence: {details.get('confidence_score', 0):.0%}")
            else:
                print(f"      └─ Expected: {result['expected_learning']}")
        
        # Real-world assessment
        print(f"\n🏆 REAL-WORLD ASSESSMENT:")
        if success_rate >= 70:
            assessment = "EXCELLENT - Your system works great with real APIs!"
            grade = "A"
        elif success_rate >= 50:
            assessment = "GOOD - System demonstrates real-world capability!"
            grade = "B+"
        elif success_rate >= 30:
            assessment = "FAIR - Some real-world learning demonstrated!"
            grade = "B"
        else:
            assessment = "IMPROVEMENT NEEDED - Real APIs present challenges!"
            grade = "C+"
        
        print(f"   📈 Real-World Grade: {grade}")
        print(f"   💬 Assessment: {assessment}")
        
        # Key insights
        print(f"\n🔍 REAL-WORLD INSIGHTS:")
        learned_types = [r['learned_details'].get('constraint_type') for r in results if r['success']]
        if learned_types:
            print(f"   🧠 Real API constraint types discovered: {', '.join(set(filter(None, learned_types)))}")
        
        avg_confidence = sum(r['learned_details'].get('confidence_score', 0) for r in results if r['success']) / len([r for r in results if r['success']]) if any(r['success'] for r in results) else 0
        if avg_confidence > 0:
            print(f"   🎯 Average confidence on real APIs: {avg_confidence:.0%}")
        
        # Save report
        report = {
            'summary': {
                'test_date': datetime.now().isoformat(),
                'total_duration': total_time,
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': success_rate,
                'grade': grade,
                'assessment': assessment
            },
            'detailed_results': results
        }
        
        with open('real_world_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Real-world report saved to: real_world_test_report.json")
        print(f"🎉 Real-world testing complete! Grade: {grade}")
        
        return report

def main():
    """Main real-world testing function"""
    print("🌐 ECHIDNA REAL-WORLD API TESTING")
    print("="*50)
    print("Testing your system against actual public APIs...")
    print()
    
    tester = RealWorldAPITester()
    
    try:
        # Step 1: Discover available real APIs
        available_apis = tester.discover_real_apis()
        
        if not available_apis:
            print("❌ No real APIs available for testing. Check internet connection.")
            return
        
        # Step 2: Generate specs for real APIs
        specs = tester.generate_real_world_specs(available_apis)
        
        if not specs:
            print("❌ No API specifications could be generated.")
            return
        
        # Step 3: Create test scenarios
        scenarios = tester.create_real_world_test_scenarios(specs)
        
        # Step 4: Execute real-world tests
        results = tester.run_real_world_tests(scenarios)
        
        # Step 5: Generate report
        tester.generate_real_world_report(results)
        
    except KeyboardInterrupt:
        print("\n⚠️ Real-world testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Real-world testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
