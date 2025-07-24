from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml

class ConstraintType(Enum):
    REQUIRED_FIELD = "required_field"
    FORMAT_VALIDATION = "format_validation"
    DEPENDENCY_RULE = "dependency_rule"
    VALUE_CONSTRAINT = "value_constraint"
    PARAMETER_TYPE = "parameter_type"

@dataclass
class LearnedConstraint:
    constraint_type: ConstraintType
    affected_parameter: str
    endpoint_path: str
    rule_description: str
    formal_constraint: Dict[str, Any]
    confidence_score: float = 1.0
    success_count: int = 0
    failure_count: int = 0
    
    def update_confidence(self, success: bool):
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        total_attempts = self.success_count + self.failure_count
        self.confidence_score = self.success_count / total_attempts if total_attempts > 0 else 0.0

class APIConstraintModel:
    def __init__(self, openapi_spec: Dict[str, Any]):
        self.base_spec = openapi_spec.copy()
        self.learned_constraints: Dict[str, LearnedConstraint] = {}
        self.endpoint_rules: Dict[str, List[str]] = {}
        
    def add_constraint(self, constraint: LearnedConstraint) -> str:
        """Add a learned constraint and return its ID"""
        constraint_id = f"{constraint.endpoint_path}_{constraint.affected_parameter}_{constraint.constraint_type.value}"
        self.learned_constraints[constraint_id] = constraint
        
        # Update endpoint rules mapping
        if constraint.endpoint_path not in self.endpoint_rules:
            self.endpoint_rules[constraint.endpoint_path] = []
        self.endpoint_rules[constraint.endpoint_path].append(constraint_id)
        
        return constraint_id
    
    def get_enhanced_schema(self, endpoint_path: str = None) -> Dict[str, Any]:
        """Return spec enhanced with learned constraints"""
        enhanced_spec = self.base_spec.copy()
        
        # Add learned rules to the spec
        if 'x-learned-rules' not in enhanced_spec:
            enhanced_spec['x-learned-rules'] = {}
        
        constraints_to_apply = []
        if endpoint_path:
            constraints_to_apply = self.endpoint_rules.get(endpoint_path, [])
        else:
            constraints_to_apply = list(self.learned_constraints.keys())
        
        for constraint_id in constraints_to_apply:
            constraint = self.learned_constraints[constraint_id]
            if constraint.confidence_score > 0.7:  # Only apply high-confidence rules
                self._apply_constraint_to_spec(enhanced_spec, constraint)
        
        return enhanced_spec
    
    def _apply_constraint_to_spec(self, spec: Dict[str, Any], constraint: LearnedConstraint):
        """Apply a learned constraint to the OpenAPI spec"""
        try:
            # Navigate to the correct parameter in the spec
            paths = spec.get('paths', {})
            if constraint.endpoint_path in paths:
                for method in paths[constraint.endpoint_path]:
                    if method in ['get', 'post', 'put', 'patch', 'delete']:
                        parameters = paths[constraint.endpoint_path][method].get('parameters', [])
                        request_body = paths[constraint.endpoint_path][method].get('requestBody', {})
                        
                        if constraint.constraint_type == ConstraintType.REQUIRED_FIELD:
                            self._apply_required_field_constraint(parameters, request_body, constraint)
                        elif constraint.constraint_type == ConstraintType.FORMAT_VALIDATION:
                            self._apply_format_constraint(parameters, request_body, constraint)
                        
        except Exception as e:
            print(f"Warning: Could not apply constraint {constraint.rule_description}: {e}")
    
    def _apply_required_field_constraint(self, parameters: List, request_body: Dict, constraint: LearnedConstraint):
        """Apply required field constraint to spec"""
        if request_body and 'content' in request_body:
            content = request_body['content']
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                if 'required' not in schema:
                    schema['required'] = []
                if constraint.affected_parameter not in schema['required']:
                    schema['required'].append(constraint.affected_parameter)
    
    def _apply_format_constraint(self, parameters: List, request_body: Dict, constraint: LearnedConstraint):
        """Apply format validation constraint to spec"""
        format_rule = constraint.formal_constraint.get('format')
        if format_rule and request_body and 'content' in request_body:
            content = request_body['content']
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                properties = schema.get('properties', {})
                if constraint.affected_parameter in properties:
                    properties[constraint.affected_parameter]['format'] = format_rule
    
    def get_constraints_for_endpoint(self, endpoint_path: str) -> List[LearnedConstraint]:
        """Get all constraints for a specific endpoint"""
        constraint_ids = self.endpoint_rules.get(endpoint_path, [])
        return [self.learned_constraints[cid] for cid in constraint_ids]
    
    def update_constraint_confidence(self, constraint_id: str, success: bool):
        """Update confidence score for a constraint"""
        if constraint_id in self.learned_constraints:
            self.learned_constraints[constraint_id].update_confidence(success)
