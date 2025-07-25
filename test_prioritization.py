from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from datetime import datetime, timedelta

class TestPriority(Enum):
    CRITICAL = 1.0
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    MINIMAL = 0.2

@dataclass
class TestScenario:
    """Represents a potential test scenario"""
    scenario_id: str
    description: str
    target_endpoint: str
    target_parameters: List[str]
    priority_score: float
    expected_learning_value: float
    execution_cost: float
    risk_level: str
    
    # Learning potential
    constraint_discovery_potential: Dict[str, float] = field(default_factory=dict)
    pattern_validation_potential: float = 0.0
    coverage_improvement: float = 0.0

class IntelligentTestPrioritizer:
    def __init__(self):
        self.endpoint_coverage: Dict[str, float] = {}
        self.parameter_coverage: Dict[str, float] = {}
        self.constraint_type_coverage: Dict[str, float] = {}
        self.recent_test_history: List[Dict[str, Any]] = []
        
        # Prioritization weights
        self.weights = {
            'learning_potential': 0.35,
            'coverage_gap': 0.25,
            'pattern_validation': 0.20,
            'execution_efficiency': 0.15,
            'risk_mitigation': 0.05
        }
    
    def analyze_test_landscape(self, constraints: Dict[str, Any], patterns: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze the current test landscape to identify gaps and opportunities"""
        
        analysis = {
            'coverage_gaps': self._identify_coverage_gaps(constraints),
            'learning_opportunities': self._identify_learning_opportunities(constraints),
            'pattern_validation_needs': self._identify_pattern_validation_needs(patterns or {}),
            'risk_areas': self._identify_risk_areas(constraints)
        }
        
        return analysis
    
    def prioritize_test_scenarios(self, potential_scenarios: List[TestScenario], constraints: Dict[str, Any]) -> List[TestScenario]:
        """Prioritize test scenarios based on learning value and strategic importance"""
        
        scored_scenarios = []
        
        for scenario in potential_scenarios:
            score = self._calculate_priority_score(scenario, constraints)
            scenario.priority_score = score
            scored_scenarios.append(scenario)
        
        # Sort by priority score (descending)
        return sorted(scored_scenarios, key=lambda x: x.priority_score, reverse=True)
    
    def generate_strategic_test_plan(self, constraints: Dict[str, Any], patterns: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a strategic test plan focusing on maximum learning value"""
        
        landscape_analysis = self.analyze_test_landscape(constraints, patterns)
        
        # Generate test scenarios based on gaps and opportunities
        scenarios = self._generate_strategic_scenarios(landscape_analysis, constraints)
        
        # Prioritize scenarios
        prioritized_scenarios = self.prioritize_test_scenarios(scenarios, constraints)
        
        # Create execution plan
        execution_plan = self._create_execution_plan(prioritized_scenarios)
        
        return {
            'landscape_analysis': landscape_analysis,
            'prioritized_scenarios': [
                {
                    'scenario_id': s.scenario_id,
                    'description': s.description,
                    'priority_score': s.priority_score,
                    'expected_learning_value': s.expected_learning_value,
                    'target_endpoint': s.target_endpoint,
                    'risk_level': s.risk_level
                }
                for s in prioritized_scenarios[:10]  # Top 10 scenarios
            ],
            'execution_plan': execution_plan,
            'recommendations': self._generate_recommendations(landscape_analysis, prioritized_scenarios)
        }
    
    def _calculate_priority_score(self, scenario: TestScenario, constraints: Dict[str, Any]) -> float:
        """Calculate priority score for a test scenario"""
        
        # Learning potential score
        learning_score = scenario.expected_learning_value * self.weights['learning_potential']
        
        # Coverage gap score
        coverage_score = self._calculate_coverage_score(scenario) * self.weights['coverage_gap']
        
        # Pattern validation score
        pattern_score = scenario.pattern_validation_potential * self.weights['pattern_validation']
        
        # Execution efficiency score (inverse of cost)
        efficiency_score = (1.0 - scenario.execution_cost) * self.weights['execution_efficiency']
        
        # Risk mitigation score
        risk_score = self._calculate_risk_score(scenario) * self.weights['risk_mitigation']
        
        total_score = learning_score + coverage_score + pattern_score + efficiency_score + risk_score
        
        return min(1.0, total_score)
    
    def _identify_coverage_gaps(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Identify gaps in test coverage"""
        
        # Analyze endpoint coverage
        covered_endpoints = set()
        constraint_types_by_endpoint = {}
        
        for constraint_id, constraint in constraints.items():
            endpoint = constraint.get('endpoint_path', 'unknown')
            constraint_type = constraint.get('constraint_type', 'unknown')
            
            covered_endpoints.add(endpoint)
            
            if endpoint not in constraint_types_by_endpoint:
                constraint_types_by_endpoint[endpoint] = set()
            constraint_types_by_endpoint[endpoint].add(constraint_type)
        
        # Identify missing constraint types per endpoint
        all_constraint_types = {'required_field', 'mutual_exclusivity', 'conditional_requirement', 'business_rule', 'rate_limiting'}
        
        coverage_gaps = {
            'uncovered_endpoints': [],  # Would need endpoint discovery
            'partial_constraint_coverage': {},
            'missing_constraint_types': {}
        }
        
        for endpoint, types in constraint_types_by_endpoint.items():
            missing_types = all_constraint_types - types
            if missing_types:
                coverage_gaps['missing_constraint_types'][endpoint] = list(missing_types)
        
        return coverage_gaps
    
    def _identify_learning_opportunities(self, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify high-value learning opportunities"""
        
        opportunities = []
        
        # Look for constraint types that appear infrequently
        constraint_type_counts = {}
        for constraint in constraints.values():
            c_type = constraint.get('constraint_type', 'unknown')
            constraint_type_counts[c_type] = constraint_type_counts.get(c_type, 0) + 1
        
        # Identify underrepresented constraint types
        total_constraints = len(constraints)
        for c_type, count in constraint_type_counts.items():
            frequency = count / total_constraints if total_constraints > 0 else 0
            
            if frequency < 0.2 and c_type in ['conditional_requirement', 'business_rule', 'format_dependency']:
                opportunities.append({
                    'type': 'constraint_type_underrepresented',
                    'constraint_type': c_type,
                    'current_frequency': frequency,
                    'learning_value': 0.8,
                    'description': f"Constraint type '{c_type}' is underrepresented. Focus on discovering more instances."
                })
        
        # Look for low-confidence constraints that could be improved
        for constraint_id, constraint in constraints.items():
            confidence = constraint.get('confidence_score', 1.0)
            if confidence < 0.7:
                opportunities.append({
                    'type': 'confidence_improvement',
                    'constraint_id': constraint_id,
                    'current_confidence': confidence,
                    'learning_value': 0.6,
                    'description': f"Low-confidence constraint could benefit from validation tests."
                })
        
        return sorted(opportunities, key=lambda x: x['learning_value'], reverse=True)
    
    def _identify_pattern_validation_needs(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify patterns that need validation"""
        
        validation_needs = []
        
        for pattern_id, pattern in patterns.items():
            confidence = pattern.get('confidence', 1.0)
            validation_attempts = pattern.get('validation_attempts', 0)
            
            # Patterns with high confidence but low validation
            if confidence > 0.8 and validation_attempts < 3:
                validation_needs.append({
                    'pattern_id': pattern_id,
                    'validation_priority': 'high',
                    'reason': 'high_confidence_low_validation',
                    'description': pattern.get('description', 'Unknown pattern')
                })
            
            # Patterns with medium confidence that could be improved
            elif 0.5 <= confidence <= 0.8:
                validation_needs.append({
                    'pattern_id': pattern_id,
                    'validation_priority': 'medium',
                    'reason': 'medium_confidence_improvement',
                    'description': pattern.get('description', 'Unknown pattern')
                })
        
        return validation_needs
    
    def _identify_risk_areas(self, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify high-risk areas that need attention"""
        
        risk_areas = []
        
        # Look for critical endpoints with few constraints
        endpoint_constraint_counts = {}
        for constraint in constraints.values():
            endpoint = constraint.get('endpoint_path', 'unknown')
            endpoint_constraint_counts[endpoint] = endpoint_constraint_counts.get(endpoint, 0) + 1
        
        for endpoint, count in endpoint_constraint_counts.items():
            if count < 2 and endpoint not in ['/health', '/status']:  # Exclude health check endpoints
                risk_areas.append({
                    'type': 'insufficient_coverage',
                    'endpoint': endpoint,
                    'constraint_count': count,
                    'risk_level': 'high',
                    'description': f"Endpoint '{endpoint}' has insufficient constraint coverage"
                })
        
        return risk_areas
    
    def _generate_strategic_scenarios(self, analysis: Dict[str, Any], constraints: Dict[str, Any]) -> List[TestScenario]:
        """Generate strategic test scenarios based on analysis"""
        
        scenarios = []
        scenario_counter = 1
        
        # Generate scenarios for coverage gaps
        for endpoint, missing_types in analysis['coverage_gaps'].get('missing_constraint_types', {}).items():
            for constraint_type in missing_types:
                scenario = TestScenario(
                    scenario_id=f"coverage_{scenario_counter}",
                    description=f"Test {endpoint} for {constraint_type} constraints",
                    target_endpoint=endpoint,
                    target_parameters=["test_param"],  # Would be determined dynamically
                    priority_score=0.0,  # Will be calculated
                    expected_learning_value=0.7,
                    execution_cost=0.3,
                    risk_level="medium",
                    constraint_discovery_potential={constraint_type: 0.8}
                )
                scenarios.append(scenario)
                scenario_counter += 1
        
        # Generate scenarios for learning opportunities
        for opportunity in analysis['learning_opportunities'][:5]:  # Top 5 opportunities
            scenario = TestScenario(
                scenario_id=f"learning_{scenario_counter}",
                description=f"Learning opportunity: {opportunity['description']}",
                target_endpoint="/users",  # Default, would be determined dynamically
                target_parameters=["test_param"],
                priority_score=0.0,
                expected_learning_value=opportunity['learning_value'],
                execution_cost=0.4,
                risk_level="low"
            )
            scenarios.append(scenario)
            scenario_counter += 1
        
        return scenarios
    
    def _calculate_coverage_score(self, scenario: TestScenario) -> float:
        """Calculate coverage improvement score for a scenario"""
        # Simplified calculation - in real implementation, this would analyze
        # current coverage and potential improvement
        return 0.6  # Default moderate coverage value
    
    def _calculate_risk_score(self, scenario: TestScenario) -> float:
        """Calculate risk mitigation score for a scenario"""
        risk_mapping = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4,
            'minimal': 0.2
        }
        return risk_mapping.get(scenario.risk_level, 0.5)
    
    def _create_execution_plan(self, prioritized_scenarios: List[TestScenario]) -> Dict[str, Any]:
        """Create an execution plan for prioritized scenarios"""
        
        plan = {
            'immediate_priority': prioritized_scenarios[:3],
            'short_term': prioritized_scenarios[3:8],
            'long_term': prioritized_scenarios[8:],
            'estimated_execution_time': sum(s.execution_cost for s in prioritized_scenarios[:10]) * 5,  # 5 minutes per cost unit
            'expected_learning_value': sum(s.expected_learning_value for s in prioritized_scenarios[:10]) / len(prioritized_scenarios[:10]) if prioritized_scenarios else 0
        }
        
        return plan
    
    def _generate_recommendations(self, analysis: Dict[str, Any], scenarios: List[TestScenario]) -> List[str]:
        """Generate strategic recommendations"""
        
        recommendations = []
        
        if len(analysis['coverage_gaps'].get('missing_constraint_types', {})) > 0:
            recommendations.append("Focus on discovering missing constraint types to improve coverage")
        
        if len(analysis['learning_opportunities']) > 5:
            recommendations.append("High number of learning opportunities detected - prioritize systematic exploration")
        
        if len(analysis['risk_areas']) > 0:
            recommendations.append("Address high-risk areas with insufficient constraint coverage")
        
        high_priority_scenarios = [s for s in scenarios if s.priority_score > 0.8]
        if len(high_priority_scenarios) > 3:
            recommendations.append("Multiple high-priority scenarios available - consider batch execution")
        
        return recommendations
