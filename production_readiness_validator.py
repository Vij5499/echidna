#!/usr/bin/env python3
"""
Production Readiness Assessment for Echidna Agent
Final comprehensive validation with enterprise-grade testing scenarios
"""

import os
import json
import time
import requests
import subprocess
import sys
from datetime import datetime

class ProductionReadinessValidator:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.enterprise_score = 0
        self.max_enterprise_score = 0
    
    def test_complex_json_api(self):
        """Test against JSONPlaceholder with complex nested scenarios"""
        print("\n📦 TESTING COMPLEX JSON SCENARIOS")
        print("-" * 50)
        
        # Enhanced JSONPlaceholder spec with more complex constraints
        complex_spec = """openapi: 3.0.0
info:
  title: JSONPlaceholder Complex Test
  version: 1.0.0
  description: Complex constraint testing

servers:
  - url: https://jsonplaceholder.typicode.com

paths:
  /posts:
    post:
      summary: Create complex post
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
                category:
                  type: string
                tags:
                  type: array
                  items:
                    type: string
                metadata:
                  type: object
                  properties:
                    priority:
                      type: string
                    department:
                      type: string
              # INTENTIONALLY MISSING: Complex validation rules
      responses:
        '201':
          description: Post created
        '400':
          description: Validation error
"""
        
        with open('specs/production_complex.yaml', 'w') as f:
            f.write(complex_spec)
        
        complex_scenarios = [
            {
                'prompt': 'Create post with title longer than 100 characters and see if it gets rejected',
                'expected': 'title length constraint',
                'complexity': 'high'
            },
            {
                'prompt': 'Create post with userId as negative number which should fail validation',
                'expected': 'userId validation rule',
                'complexity': 'medium'
            },
            {
                'prompt': 'Create post with empty tags array while category is missing',
                'expected': 'conditional requirement',
                'complexity': 'high'
            },
            {
                'prompt': 'Create post with metadata priority field as invalid value like "ultra-mega"',
                'expected': 'enum constraint',
                'complexity': 'high'
            }
        ]
        
        return self._run_enterprise_tests('ComplexJSON', 'specs/production_complex.yaml', complex_scenarios)
    
    def test_rate_limiting_scenarios(self):
        """Test API rate limiting behavior"""
        print("\n⚡ TESTING RATE LIMITING SCENARIOS")
        print("-" * 50)
        
        # Test with rapid requests to trigger potential rate limits
        rate_spec = """openapi: 3.0.0
info:
  title: Rate Limiting Test
  version: 1.0.0
  description: Test rate limiting constraints

servers:
  - url: https://httpbin.org

paths:
  /delay/{delay}:
    get:
      summary: Delayed response
      parameters:
        - name: delay
          in: path
          required: true
          schema:
            type: integer
            minimum: 1
            maximum: 10
          # MISSING: Rate limiting constraints
      responses:
        '200':
          description: Delayed response
        '429':
          description: Too many requests
"""
        
        with open('specs/production_rate_limit.yaml', 'w') as f:
            f.write(rate_spec)
        
        rate_scenarios = [
            {
                'prompt': 'Make rapid requests with delay of 0 seconds to trigger rate limiting',
                'expected': 'rate limiting constraint',
                'complexity': 'high'
            }
        ]
        
        return self._run_enterprise_tests('RateLimiting', 'specs/production_rate_limit.yaml', rate_scenarios)
    
    def test_authentication_patterns(self):
        """Test authentication-related constraints"""
        print("\n🔐 TESTING AUTHENTICATION PATTERNS")
        print("-" * 50)
        
        auth_spec = """openapi: 3.0.0
info:
  title: Authentication Test
  version: 1.0.0
  description: Test auth constraints

servers:
  - url: https://httpbin.org

paths:
  /basic-auth/{user}/{passwd}:
    get:
      summary: Basic auth test
      parameters:
        - name: user
          in: path
          required: true
          schema:
            type: string
        - name: passwd
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Authenticated
        '401':
          description: Authentication failed
"""
        
        with open('specs/production_auth.yaml', 'w') as f:
            f.write(auth_spec)
        
        auth_scenarios = [
            {
                'prompt': 'Access basic auth endpoint with empty password to see auth requirements',
                'expected': 'authentication constraint',
                'complexity': 'medium'
            }
        ]
        
        return self._run_enterprise_tests('Authentication', 'specs/production_auth.yaml', auth_scenarios)
    
    def test_data_validation_edge_cases(self):
        """Test edge cases in data validation"""
        print("\n🎯 TESTING DATA VALIDATION EDGE CASES")
        print("-" * 50)
        
        validation_spec = """openapi: 3.0.0
info:
  title: Data Validation Edge Cases
  version: 1.0.0
  description: Complex validation scenarios

servers:
  - url: https://httpbin.org

paths:
  /anything:
    post:
      summary: Accept anything
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                phone:
                  type: string
                age:
                  type: integer
                  minimum: 0
                  maximum: 150
                url:
                  type: string
                  format: uri
                date:
                  type: string
                  format: date
      responses:
        '200':
          description: Data accepted
        '400':
          description: Validation failed
"""
        
        with open('specs/production_validation.yaml', 'w') as f:
            f.write(validation_spec)
        
        validation_scenarios = [
            {
                'prompt': 'Send data with email as "not-an-email" to test email format validation',
                'expected': 'email format constraint',
                'complexity': 'medium'
            },
            {
                'prompt': 'Send data with age as 999 to test maximum value constraints',
                'expected': 'maximum value constraint',
                'complexity': 'medium'
            },
            {
                'prompt': 'Send data with invalid URL format to test URI validation',
                'expected': 'URI format constraint',
                'complexity': 'medium'
            }
        ]
        
        return self._run_enterprise_tests('DataValidation', 'specs/production_validation.yaml', validation_scenarios)
    
    def _run_enterprise_tests(self, test_name, spec_file, scenarios):
        """Run enterprise-grade test scenarios"""
        results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"   🏢 {test_name} Enterprise Test {i}: {scenario['prompt'][:50]}...")
            
            # Increase scoring based on complexity
            complexity_score = {'high': 3, 'medium': 2, 'low': 1}
            self.max_enterprise_score += complexity_score.get(scenario.get('complexity', 'low'), 1)
            
            # Clean up
            for file in ['learned_model.json', 'pattern_analysis.json']:
                if os.path.exists(file):
                    os.remove(file)
            
            # Set environment with more aggressive settings
            env = os.environ.copy()
            env.update({
                'SPEC_PATH': spec_file,
                'MAX_ATTEMPTS': '2',  # Allow more attempts for complex scenarios
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
                    timeout=180,  # Longer timeout for complex scenarios
                    encoding='utf-8',
                    errors='replace'
                )
                
                duration = time.time() - start_time
                
                # Check for learning with enhanced scoring
                constraint_learned = False
                learned_details = {}
                confidence = 0
                
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
                                confidence = learned_details.get('confidence_score', 0)
                    except:
                        pass
                
                # Enterprise scoring based on constraint quality and confidence
                if constraint_learned:
                    base_score = complexity_score.get(scenario.get('complexity', 'low'), 1)
                    confidence_multiplier = min(confidence, 1.0)
                    earned_score = base_score * confidence_multiplier
                    self.enterprise_score += earned_score
                    
                    print(f"      ✅ Enterprise Learning: {learned_details.get('constraint_type', 'unknown')} (confidence: {confidence:.1%})")
                else:
                    print(f"      ❌ No enterprise constraint learned")
                
                results.append({
                    'test_name': test_name,
                    'scenario': scenario['prompt'][:40] + '...',
                    'success': constraint_learned,
                    'duration': duration,
                    'learned_details': learned_details,
                    'expected': scenario['expected'],
                    'complexity': scenario.get('complexity', 'low'),
                    'confidence': confidence
                })
                
            except subprocess.TimeoutExpired:
                print(f"      ⏰ Enterprise timeout")
                results.append({
                    'test_name': test_name,
                    'scenario': scenario['prompt'][:40] + '...',
                    'success': False,
                    'duration': 180,
                    'learned_details': {},
                    'expected': scenario['expected'],
                    'complexity': scenario.get('complexity', 'low'),
                    'confidence': 0
                })
            except Exception as e:
                print(f"      ❌ Enterprise error: {str(e)[:30]}")
                results.append({
                    'test_name': test_name,
                    'scenario': scenario['prompt'][:40] + '...',
                    'success': False,
                    'duration': 0,
                    'learned_details': {},
                    'expected': scenario['expected'],
                    'complexity': scenario.get('complexity', 'low'),
                    'confidence': 0
                })
        
        return {'success': True, 'results': results}
    
    def run_production_readiness_assessment(self):
        """Run comprehensive production readiness assessment"""
        print("🏭 PRODUCTION READINESS ASSESSMENT")
        print("="*70)
        print("Testing Echidna for enterprise production deployment...")
        print()
        
        all_results = []
        
        # Enterprise-grade test suite
        enterprise_tests = [
            ('Complex JSON Validation', self.test_complex_json_api),
            ('Rate Limiting Detection', self.test_rate_limiting_scenarios),
            ('Authentication Patterns', self.test_authentication_patterns),
            ('Data Validation Edge Cases', self.test_data_validation_edge_cases),
        ]
        
        for test_name, test_func in enterprise_tests:
            try:
                result = test_func()
                if result.get('success') and 'results' in result:
                    all_results.extend(result['results'])
                time.sleep(2)  # Pause between test suites
            except Exception as e:
                print(f"   ❌ {test_name} failed: {str(e)}")
        
        # Generate production readiness report
        self._generate_production_report(all_results)
    
    def _generate_production_report(self, results):
        """Generate comprehensive production readiness report"""
        total_time = time.time() - self.start_time
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        basic_success_rate = (successful / total) * 100 if total > 0 else 0
        
        # Enterprise scoring
        enterprise_percentage = (self.enterprise_score / self.max_enterprise_score) * 100 if self.max_enterprise_score > 0 else 0
        
        print(f"\n" + "="*80)
        print("🏭 PRODUCTION READINESS ASSESSMENT REPORT")
        print("="*80)
        print(f"📅 Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Assessment Time: {total_time:.1f} seconds")
        print(f"🏢 Enterprise Test Categories: {len(set(r['test_name'] for r in results))}")
        print(f"🎯 Total Enterprise Scenarios: {total}")
        print(f"✅ Successful Enterprise Learning: {successful}")
        print(f"📊 Basic Success Rate: {basic_success_rate:.1f}%")
        print(f"🏆 Enterprise Score: {self.enterprise_score:.1f}/{self.max_enterprise_score:.1f} ({enterprise_percentage:.1f}%)")
        
        # Test category breakdown
        print(f"\n📋 ENTERPRISE RESULTS BY CATEGORY:")
        test_groups = {}
        for result in results:
            test_name = result['test_name']
            if test_name not in test_groups:
                test_groups[test_name] = []
            test_groups[test_name].append(result)
        
        for test_name, test_results in test_groups.items():
            test_success = sum(1 for r in test_results if r['success'])
            test_total = len(test_results)
            avg_confidence = sum(r['confidence'] for r in test_results if r['success']) / max(test_success, 1)
            
            print(f"   🏢 {test_name}: {test_success}/{test_total} scenarios")
            
            for result in test_results:
                status = "✅" if result['success'] else "❌"
                complexity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(result['complexity'], "⚪")
                print(f"      {status} {complexity_icon} {result['scenario']} ({result['duration']:.1f}s)")
                if result['success']:
                    details = result['learned_details']
                    confidence = result['confidence']
                    print(f"         └─ Learned: {details.get('constraint_type', 'unknown')} (confidence: {confidence:.1%})")
        
        # Production readiness assessment
        print(f"\n🎖️  PRODUCTION READINESS GRADE:")
        if enterprise_percentage >= 80:
            grade = "A+"
            readiness = "PRODUCTION READY"
            assessment = "🚀 EXCELLENT - Ready for enterprise deployment!"
        elif enterprise_percentage >= 70:
            grade = "A"
            readiness = "PRODUCTION READY"
            assessment = "🌟 VERY GOOD - Strong enterprise capabilities!"
        elif enterprise_percentage >= 60:
            grade = "B+"
            readiness = "MOSTLY READY"
            assessment = "💪 GOOD - Solid enterprise potential with minor gaps!"
        elif enterprise_percentage >= 50:
            grade = "B"
            readiness = "NEEDS REFINEMENT"
            assessment = "⚡ FAIR - Good foundation, needs enterprise tuning!"
        elif enterprise_percentage >= 30:
            grade = "B-"
            readiness = "DEVELOPMENT STAGE"
            assessment = "🔧 DEVELOPING - Shows promise, needs more work!"
        else:
            grade = "C+"
            readiness = "EARLY STAGE"
            assessment = "🛠️  EARLY - Good start, significant development needed!"
        
        print(f"   📈 Production Grade: {grade}")
        print(f"   🏭 Readiness Status: {readiness}")
        print(f"   💬 Enterprise Assessment: {assessment}")
        
        # Enterprise insights
        print(f"\n🔍 ENTERPRISE INSIGHTS:")
        constraint_types = [r['learned_details'].get('constraint_type') for r in results if r['success']]
        unique_constraints = set(filter(None, constraint_types))
        if unique_constraints:
            print(f"   🧠 Enterprise constraint types: {', '.join(unique_constraints)}")
        
        high_confidence = [r for r in results if r['success'] and r['confidence'] >= 0.8]
        print(f"   🎯 High-confidence learnings: {len(high_confidence)}/{successful}")
        
        complex_successes = [r for r in results if r['success'] and r['complexity'] == 'high']
        total_complex = [r for r in results if r['complexity'] == 'high']
        print(f"   🔴 Complex scenario success: {len(complex_successes)}/{len(total_complex)}")
        
        avg_processing_time = sum(r['duration'] for r in results) / len(results) if results else 0
        print(f"   ⚡ Average enterprise processing time: {avg_processing_time:.1f}s")
        
        # Production recommendations
        print(f"\n💡 PRODUCTION DEPLOYMENT RECOMMENDATIONS:")
        
        if enterprise_percentage >= 70:
            print("   ✅ System demonstrates strong enterprise capabilities")
            print("   🚀 Recommended for production pilot with real APIs")
            print("   📈 Consider scaling to multiple API endpoints")
        elif enterprise_percentage >= 50:
            print("   🔧 Good foundation with room for improvement")
            print("   🧪 Recommended for staging environment testing")
            print("   📊 Focus on improving constraint confidence scores")
        else:
            print("   🛠️  Needs additional development before production")
            print("   🔍 Focus on complex constraint detection")
            print("   📚 Consider additional training data")
        
        if avg_processing_time > 30:
            print("   ⚡ Consider optimizing processing time for production scale")
        
        # Save comprehensive production report
        production_report = {
            'production_assessment': {
                'assessment_date': datetime.now().isoformat(),
                'total_duration': total_time,
                'basic_success_rate': basic_success_rate,
                'enterprise_score': self.enterprise_score,
                'max_enterprise_score': self.max_enterprise_score,
                'enterprise_percentage': enterprise_percentage,
                'grade': grade,
                'readiness_status': readiness,
                'assessment': assessment
            },
            'detailed_results': results,
            'enterprise_insights': {
                'unique_constraint_types': list(unique_constraints) if unique_constraints else [],
                'high_confidence_count': len(high_confidence),
                'complex_success_count': len(complex_successes),
                'total_complex_count': len(total_complex),
                'average_processing_time': avg_processing_time
            }
        }
        
        with open('production_readiness_report.json', 'w') as f:
            json.dump(production_report, f, indent=2)
        
        print(f"\n📄 Production readiness report saved to: production_readiness_report.json")
        print(f"🎉 Production readiness assessment complete!")
        print(f"🏆 Final Enterprise Grade: {grade} ({readiness})")

def main():
    """Main execution function"""
    validator = ProductionReadinessValidator()
    validator.run_production_readiness_assessment()

if __name__ == "__main__":
    main()
