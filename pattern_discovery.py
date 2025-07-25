from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re
from constraint_model import LearnedConstraint, ConstraintType

class PatternScope(Enum):
    ENDPOINT_SPECIFIC = "endpoint_specific"
    DOMAIN_WIDE = "domain_wide"          # Applies across all endpoints in domain
    PARAMETER_BASED = "parameter_based"   # Applies to specific parameter types
    OPERATION_BASED = "operation_based"   # Applies to specific HTTP operations
    GLOBAL = "global"                     # Applies system-wide

class PatternConfidence(Enum):
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class CrossEndpointPattern:
    """Represents a pattern discovered across multiple endpoints"""
    pattern_id: str
    pattern_type: str  # "authentication", "validation", "rate_limiting", "business_rule"
    pattern_description: str
    scope: PatternScope
    confidence: float
    
    # Pattern evidence
    supporting_constraints: List[str] = field(default_factory=list)  # Constraint IDs
    affected_endpoints: Set[str] = field(default_factory=set)
    parameter_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Pattern validation
    validation_attempts: int = 0
    validation_successes: int = 0
    last_validated: Optional[datetime] = None
    
    # Pattern metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    pattern_tags: List[str] = field(default_factory=list)

@dataclass
class PatternGeneralizationRule:
    """Rules for applying patterns to new scenarios"""
    source_pattern_id: str
    target_conditions: Dict[str, Any]  # Conditions when this rule applies
    adaptation_strategy: str  # How to adapt the pattern
    confidence_modifier: float  # How much to adjust confidence when applying
    success_rate: float = 0.0
    application_count: int = 0

class AdvancedPatternDiscovery:
    def __init__(self):
        self.discovered_patterns: Dict[str, CrossEndpointPattern] = {}
        self.generalization_rules: Dict[str, PatternGeneralizationRule] = {}
        self.endpoint_relationships: Dict[str, Set[str]] = defaultdict(set)
        self.parameter_frequency: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
    def analyze_constraint_patterns(self, constraints: Dict[str, LearnedConstraint]) -> List[CrossEndpointPattern]:
        """Analyze learned constraints to discover cross-endpoint patterns"""
        
        print("🔍 Starting cross-endpoint pattern discovery...")
        
        # Group constraints by type and analyze patterns
        constraint_groups = self._group_constraints_by_characteristics(constraints)
        
        discovered_patterns = []
        
        # Discover parameter-based patterns
        param_patterns = self._discover_parameter_patterns(constraint_groups)
        discovered_patterns.extend(param_patterns)
        
        # Discover validation patterns
        validation_patterns = self._discover_validation_patterns(constraint_groups)
        discovered_patterns.extend(validation_patterns)
        
        # Discover business rule patterns
        business_patterns = self._discover_business_rule_patterns(constraint_groups)
        discovered_patterns.extend(business_patterns)
        
        # Discover operational patterns
        operational_patterns = self._discover_operational_patterns(constraint_groups)
        discovered_patterns.extend(operational_patterns)
        
        # Store discovered patterns
        for pattern in discovered_patterns:
            self.discovered_patterns[pattern.pattern_id] = pattern
            
        print(f"🎯 Discovered {len(discovered_patterns)} cross-endpoint patterns")
        return discovered_patterns
    
    def _group_constraints_by_characteristics(self, constraints: Dict[str, LearnedConstraint]) -> Dict[str, List[LearnedConstraint]]:
        """Group constraints by various characteristics for pattern analysis"""
        
        groups = {
            'by_type': defaultdict(list),
            'by_parameter': defaultdict(list), 
            'by_endpoint': defaultdict(list),
            'by_confidence': defaultdict(list),
            'mutual_exclusivity': [],
            'conditional_requirements': [],
            'business_rules': [],
            'rate_limiting': []
        }
        
        for constraint_id, constraint in constraints.items():
            # Group by type
            groups['by_type'][constraint.constraint_type].append(constraint)
            
            # Group by parameter
            groups['by_parameter'][constraint.affected_parameter].append(constraint)
            
            # Group by endpoint
            groups['by_endpoint'][constraint.endpoint_path].append(constraint)
            
            # Group by confidence level
            if constraint.confidence_score >= 0.9:
                groups['by_confidence']['high'].append(constraint)
            elif constraint.confidence_score >= 0.7:
                groups['by_confidence']['medium'].append(constraint)
            else:
                groups['by_confidence']['low'].append(constraint)
            
            # Group by specific constraint types
            if constraint.constraint_type == ConstraintType.MUTUAL_EXCLUSIVITY:
                groups['mutual_exclusivity'].append(constraint)
            elif constraint.constraint_type == ConstraintType.CONDITIONAL_REQUIREMENT:
                groups['conditional_requirements'].append(constraint)
            elif constraint.constraint_type == ConstraintType.BUSINESS_RULE:
                groups['business_rules'].append(constraint)
            elif constraint.constraint_type == ConstraintType.RATE_LIMITING:
                groups['rate_limiting'].append(constraint)
                
        return groups
    
    def _discover_parameter_patterns(self, groups: Dict[str, Any]) -> List[CrossEndpointPattern]:
        """Discover patterns based on parameter behavior across endpoints"""
        patterns = []
        
        # Look for parameters that appear across multiple endpoints with similar constraints
        parameter_analysis = {}
        
        for param_name, constraints in groups['by_parameter'].items():
            if len(constraints) < 2:  # Need at least 2 constraints to form a pattern
                continue
                
            # Analyze constraint types for this parameter
            constraint_types = [c.constraint_type for c in constraints]
            endpoints = [c.endpoint_path for c in constraints]
            
            # Check if same parameter has consistent constraint types across endpoints
            if len(set(constraint_types)) == 1 and len(set(endpoints)) > 1:
                pattern = CrossEndpointPattern(
                    pattern_id=f"param_{param_name}_{constraint_types[0].value}",
                    pattern_type="parameter_validation",
                    pattern_description=f"Parameter '{param_name}' consistently requires {constraint_types[0].value} validation across multiple endpoints",
                    scope=PatternScope.PARAMETER_BASED,
                    confidence=min(c.confidence_score for c in constraints),
                    supporting_constraints=[f"constraint_{i}" for i, c in enumerate(constraints)],
                    affected_endpoints=set(endpoints),
                    parameter_patterns={
                        'parameter_name': param_name,
                        'constraint_type': constraint_types[0].value,
                        'consistency_score': 1.0
                    }
                )
                patterns.append(pattern)
                
        return patterns
    
    def _discover_validation_patterns(self, groups: Dict[str, Any]) -> List[CrossEndpointPattern]:
        """Discover validation patterns that span multiple endpoints"""
        patterns = []
        
        # Look for mutual exclusivity patterns
        if groups['mutual_exclusivity']:
            # Check if mutual exclusivity patterns are consistent across endpoints
            exclusivity_patterns = defaultdict(list)
            
            for constraint in groups['mutual_exclusivity']:
                if constraint.exclusivity_rule:
                    # Create a signature for the exclusivity pattern
                    fields = sorted(constraint.exclusivity_rule.exclusive_fields)
                    signature = f"{'_'.join(fields)}_{constraint.exclusivity_rule.min_required}_{constraint.exclusivity_rule.max_allowed}"
                    exclusivity_patterns[signature].append(constraint)
            
            # Create patterns for consistent exclusivity rules
            for signature, constraints in exclusivity_patterns.items():
                if len(constraints) >= 2:  # Pattern appears in multiple places
                    endpoints = [c.endpoint_path for c in constraints]
                    
                    pattern = CrossEndpointPattern(
                        pattern_id=f"exclusivity_{signature}",
                        pattern_type="mutual_exclusivity",
                        pattern_description=f"Mutual exclusivity pattern '{signature}' appears across {len(endpoints)} endpoints",
                        scope=PatternScope.DOMAIN_WIDE if len(endpoints) > 2 else PatternScope.PARAMETER_BASED,
                        confidence=sum(c.confidence_score for c in constraints) / len(constraints),
                        supporting_constraints=[f"constraint_{i}" for i, c in enumerate(constraints)],
                        affected_endpoints=set(endpoints),
                        parameter_patterns={
                            'exclusivity_signature': signature,
                            'field_pattern': constraints[0].exclusivity_rule.exclusive_fields,
                            'occurrence_count': len(constraints)
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _discover_business_rule_patterns(self, groups: Dict[str, Any]) -> List[CrossEndpointPattern]:
        """Discover business rule patterns across endpoints"""
        patterns = []
        
        if groups['business_rules']:
            # Group business rules by rule type
            rule_type_groups = defaultdict(list)
            
            for constraint in groups['business_rules']:
                if constraint.business_rule:
                    rule_type_groups[constraint.business_rule.rule_type].append(constraint)
            
            # Look for patterns in each rule type
            for rule_type, constraints in rule_type_groups.items():
                if len(constraints) >= 2:
                    # Check for similar business rules across endpoints
                    value_patterns = defaultdict(list)
                    
                    for constraint in constraints:
                        # Group by constraint value patterns
                        if isinstance(constraint.business_rule.constraint_value, (int, float)):
                            # Numeric constraints - group by range
                            value = constraint.business_rule.constraint_value
                            if rule_type == "min_value":
                                range_key = f"min_{value}"
                            elif rule_type == "max_value":
                                range_key = f"max_{value}"
                            else:
                                range_key = f"value_{value}"
                            value_patterns[range_key].append(constraint)
                    
                    # Create patterns for consistent business rules
                    for pattern_key, pattern_constraints in value_patterns.items():
                        if len(pattern_constraints) >= 2:
                            endpoints = [c.endpoint_path for c in pattern_constraints]
                            
                            pattern = CrossEndpointPattern(
                                pattern_id=f"business_rule_{rule_type}_{pattern_key}",
                                pattern_type="business_rule",
                                pattern_description=f"Business rule pattern '{rule_type}' with '{pattern_key}' appears across {len(endpoints)} endpoints",
                                scope=PatternScope.DOMAIN_WIDE,
                                confidence=sum(c.confidence_score for c in pattern_constraints) / len(pattern_constraints),
                                supporting_constraints=[f"constraint_{i}" for i, c in enumerate(pattern_constraints)],
                                affected_endpoints=set(endpoints),
                                parameter_patterns={
                                    'rule_type': rule_type,
                                    'pattern_key': pattern_key,
                                    'occurrence_count': len(pattern_constraints)
                                }
                            )
                            patterns.append(pattern)
        
        return patterns
    
    def _discover_operational_patterns(self, groups: Dict[str, Any]) -> List[CrossEndpointPattern]:
        """Discover operational patterns like rate limiting"""
        patterns = []
        
        if groups['rate_limiting']:
            # Analyze rate limiting patterns
            rate_limit_analysis = defaultdict(list)
            
            for constraint in groups['rate_limiting']:
                if constraint.rate_limit_rule:
                    # Group by rate limit characteristics
                    key = f"{constraint.rate_limit_rule.max_requests}_{constraint.rate_limit_rule.time_window_seconds}_{constraint.rate_limit_rule.scope}"
                    rate_limit_analysis[key].append(constraint)
            
            # Create patterns for consistent rate limiting
            for pattern_key, constraints in rate_limit_analysis.items():
                if len(constraints) >= 2:
                    endpoints = [c.endpoint_path for c in constraints]
                    max_requests, time_window, scope = pattern_key.split('_')
                    
                    pattern = CrossEndpointPattern(
                        pattern_id=f"rate_limit_{pattern_key}",
                        pattern_type="rate_limiting",
                        pattern_description=f"Rate limiting pattern ({max_requests} requests per {time_window}s, {scope}) appears across {len(endpoints)} endpoints",
                        scope=PatternScope.GLOBAL if scope == "global" else PatternScope.DOMAIN_WIDE,
                        confidence=sum(c.confidence_score for c in constraints) / len(constraints),
                        supporting_constraints=[f"constraint_{i}" for i, c in enumerate(constraints)],
                        affected_endpoints=set(endpoints),
                        parameter_patterns={
                            'max_requests': int(max_requests),
                            'time_window_seconds': int(time_window),
                            'scope': scope,
                            'occurrence_count': len(constraints)
                        }
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def generate_pattern_predictions(self, target_endpoint: str, target_parameters: List[str]) -> List[Dict[str, Any]]:
        """Generate predictions for likely constraints on a new endpoint based on discovered patterns"""
        predictions = []
        
        for pattern_id, pattern in self.discovered_patterns.items():
            # Check if pattern might apply to target endpoint
            applicability_score = self._calculate_pattern_applicability(pattern, target_endpoint, target_parameters)
            
            if applicability_score > 0.3:  # Threshold for considering a pattern applicable
                prediction = {
                    'pattern_id': pattern_id,
                    'pattern_type': pattern.pattern_type,
                    'description': pattern.pattern_description,
                    'applicability_score': applicability_score,
                    'confidence': pattern.confidence * applicability_score,
                    'suggested_constraints': self._generate_constraint_suggestions(pattern, target_endpoint, target_parameters)
                }
                predictions.append(prediction)
        
        # Sort by confidence
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return predictions
    
    def _calculate_pattern_applicability(self, pattern: CrossEndpointPattern, target_endpoint: str, target_parameters: List[str]) -> float:
        """Calculate how applicable a pattern is to a target endpoint"""
        score = 0.0
        
        # Endpoint similarity
        if pattern.scope == PatternScope.GLOBAL:
            score += 0.8
        elif pattern.scope == PatternScope.DOMAIN_WIDE:
            # Check if endpoint is in same domain (simple heuristic)
            pattern_domains = [ep.split('/')[1] if '/' in ep else ep for ep in pattern.affected_endpoints]
            target_domain = target_endpoint.split('/')[1] if '/' in target_endpoint else target_endpoint
            if target_domain in pattern_domains:
                score += 0.7
            else:
                score += 0.3
        elif pattern.scope == PatternScope.PARAMETER_BASED:
            # Check parameter overlap
            if 'parameter_name' in pattern.parameter_patterns:
                if pattern.parameter_patterns['parameter_name'] in target_parameters:
                    score += 0.9
                else:
                    score += 0.2
        
        return min(score, 1.0)
    
    def _generate_constraint_suggestions(self, pattern: CrossEndpointPattern, target_endpoint: str, target_parameters: List[str]) -> List[Dict[str, Any]]:
        """Generate specific constraint suggestions based on a pattern"""
        suggestions = []
        
        if pattern.pattern_type == "parameter_validation":
            param_name = pattern.parameter_patterns.get('parameter_name')
            constraint_type = pattern.parameter_patterns.get('constraint_type')
            
            if param_name in target_parameters:
                suggestions.append({
                    'constraint_type': constraint_type,
                    'affected_parameter': param_name,
                    'reasoning': f"Parameter '{param_name}' consistently requires {constraint_type} validation across similar endpoints"
                })
        
        elif pattern.pattern_type == "mutual_exclusivity":
            field_pattern = pattern.parameter_patterns.get('field_pattern', [])
            # Check if target has similar parameters
            matching_params = [p for p in target_parameters if p in field_pattern]
            if len(matching_params) >= 2:
                suggestions.append({
                    'constraint_type': 'mutual_exclusivity',
                    'affected_parameters': matching_params,
                    'reasoning': f"Similar endpoints show mutual exclusivity between {matching_params}"
                })
        
        elif pattern.pattern_type == "rate_limiting":
            max_requests = pattern.parameter_patterns.get('max_requests')
            time_window = pattern.parameter_patterns.get('time_window_seconds')
            scope = pattern.parameter_patterns.get('scope')
            
            suggestions.append({
                'constraint_type': 'rate_limiting',
                'max_requests': max_requests,
                'time_window_seconds': time_window,
                'scope': scope,
                'reasoning': f"Similar endpoints have rate limiting: {max_requests} requests per {time_window}s"
            })
        
        return suggestions
    
    def export_pattern_knowledge(self) -> Dict[str, Any]:
        """Export discovered patterns for persistence or analysis"""
        return {
            'patterns': {
                pattern_id: {
                    'pattern_type': pattern.pattern_type,
                    'description': pattern.pattern_description,
                    'scope': pattern.scope.value,
                    'confidence': pattern.confidence,
                    'affected_endpoints': list(pattern.affected_endpoints),
                    'parameter_patterns': pattern.parameter_patterns,
                    'validation_stats': {
                        'attempts': pattern.validation_attempts,
                        'successes': pattern.validation_successes,
                        'success_rate': pattern.validation_successes / max(pattern.validation_attempts, 1)
                    },
                    'discovered_at': pattern.discovered_at.isoformat()
                }
                for pattern_id, pattern in self.discovered_patterns.items()
            },
            'summary': {
                'total_patterns': len(self.discovered_patterns),
                'pattern_types': list(set(p.pattern_type for p in self.discovered_patterns.values())),
                'coverage': {
                    'endpoints': len(set().union(*[p.affected_endpoints for p in self.discovered_patterns.values()])),
                    'parameters': len(set().union(*[p.parameter_patterns.keys() for p in self.discovered_patterns.values() if isinstance(p.parameter_patterns, dict)]))
                }
            }
        }
