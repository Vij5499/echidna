from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
import re
from datetime import datetime, timedelta

class ConstraintType(Enum):
    REQUIRED_FIELD = "required_field"
    FORMAT_VALIDATION = "format_validation"
    CONDITIONAL_REQUIREMENT = "conditional_requirement"  # NEW
    MUTUAL_EXCLUSIVITY = "mutual_exclusivity"           # NEW
    FORMAT_DEPENDENCY = "format_dependency"             # NEW
    BUSINESS_RULE = "business_rule"                      # NEW
    RATE_LIMITING = "rate_limiting"                      # NEW
    VALUE_CONSTRAINT = "value_constraint"

@dataclass
class ConditionalRule:
    """Represents conditional logic: if condition then requirement"""
    condition_field: str
    condition_value: Union[str, int, float, bool]
    condition_operator: str  # "equals", "not_equals", "greater_than", "less_than", "contains"
    required_field: str
    required_value: Optional[Union[str, int, float, bool]] = None

@dataclass
class MutualExclusivityRule:
    """Represents mutual exclusivity: only one of these fields can be present"""
    exclusive_fields: List[str]
    min_required: int = 1  # At least this many must be present
    max_allowed: int = 1   # At most this many can be present

@dataclass
class FormatDependencyRule:
    """Represents format that depends on another field's value"""
    dependent_field: str
    dependency_field: str
    dependency_value: Union[str, int, float, bool]
    required_format: str  # "email", "url", "uuid", "date", "phone", etc.

@dataclass
class BusinessRule:
    """Represents business logic constraints"""
    field: str
    rule_type: str  # "min_value", "max_value", "range", "pattern", "custom"
    constraint_value: Union[str, int, float, Dict[str, Any]]
    error_message: str

@dataclass
class RateLimitRule:
    """Represents rate limiting constraints"""
    endpoint_pattern: str
    max_requests: int
    time_window_seconds: int
    scope: str = "per_user"  # "per_user", "per_ip", "global"

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
    
    # NEW: Enhanced constraint data
    conditional_rule: Optional[ConditionalRule] = None
    exclusivity_rule: Optional[MutualExclusivityRule] = None
    format_dependency: Optional[FormatDependencyRule] = None
    business_rule: Optional[BusinessRule] = None
    rate_limit_rule: Optional[RateLimitRule] = None
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    last_validated: Optional[datetime] = None
    context_tags: List[str] = field(default_factory=list)
    
    def update_confidence(self, success: bool):
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        total_attempts = self.success_count + self.failure_count
        if total_attempts > 0:
            self.confidence_score = self.success_count / total_attempts
            self.last_validated = datetime.now()

class APIConstraintModel:
    def __init__(self, openapi_spec: Dict[str, Any]):
        self.base_spec = openapi_spec.copy()
        self.learned_constraints: Dict[str, LearnedConstraint] = {}
        self.endpoint_rules: Dict[str, List[str]] = {}
        
        # NEW: Enhanced indexing for complex queries
        self.constraints_by_type: Dict[ConstraintType, List[str]] = {}
        self.conditional_dependencies: Dict[str, List[str]] = {}  # field -> list of dependent constraints
        self.format_dependencies: Dict[str, List[str]] = {}
        self.business_rules_index: Dict[str, List[str]] = {}  # field -> business rules
        
        # Rate limiting tracking
        self.rate_limit_tracker: Dict[str, Dict[str, Any]] = {}
        
    def add_constraint(self, constraint: LearnedConstraint) -> str:
        """Add a learned constraint with enhanced indexing"""
        constraint_id = self._generate_constraint_id(constraint)
        
        # Store the constraint
        self.learned_constraints[constraint_id] = constraint
        
        # Update endpoint mapping
        if constraint.endpoint_path not in self.endpoint_rules:
            self.endpoint_rules[constraint.endpoint_path] = []
        self.endpoint_rules[constraint.endpoint_path].append(constraint_id)
        
        # Update type-based indexing
        if constraint.constraint_type not in self.constraints_by_type:
            self.constraints_by_type[constraint.constraint_type] = []
        self.constraints_by_type[constraint.constraint_type].append(constraint_id)
        
        # Update specialized indexes
        self._update_specialized_indexes(constraint_id, constraint)
        
        return constraint_id
    
    def _generate_constraint_id(self, constraint: LearnedConstraint) -> str:
        """Generate unique constraint ID"""
        base_id = f"{constraint.endpoint_path}_{constraint.affected_parameter}_{constraint.constraint_type.value}"
        
        # Add disambiguating suffix for complex constraints
        if constraint.conditional_rule:
            base_id += f"_cond_{constraint.conditional_rule.condition_field}"
        elif constraint.exclusivity_rule:
            base_id += f"_excl_{'_'.join(constraint.exclusivity_rule.exclusive_fields)}"
        elif constraint.format_dependency:
            base_id += f"_fmt_{constraint.format_dependency.dependency_field}"
        
        return base_id
    
    def _update_specialized_indexes(self, constraint_id: str, constraint: LearnedConstraint):
        """Update specialized indexes for complex constraint types"""
        
        # Conditional dependencies
        if constraint.conditional_rule:
            condition_field = constraint.conditional_rule.condition_field
            if condition_field not in self.conditional_dependencies:
                self.conditional_dependencies[condition_field] = []
            self.conditional_dependencies[condition_field].append(constraint_id)
        
        # Format dependencies
        if constraint.format_dependency:
            dep_field = constraint.format_dependency.dependency_field
            if dep_field not in self.format_dependencies:
                self.format_dependencies[dep_field] = []
            self.format_dependencies[dep_field].append(constraint_id)
        
        # Business rules
        if constraint.business_rule:
            field = constraint.business_rule.field
            if field not in self.business_rules_index:
                self.business_rules_index[field] = []
            self.business_rules_index[field].append(constraint_id)
    
    def get_enhanced_schema(self, endpoint_path: str = None) -> Dict[str, Any]:
        """Return spec enhanced with learned constraints"""
        enhanced_spec = self.base_spec.copy()
        
        # Add learned rules to the spec
        if 'x-learned-rules' not in enhanced_spec:
            enhanced_spec['x-learned-rules'] = {}
        
        # Get constraints to apply
        constraints_to_apply = []
        if endpoint_path:
            constraints_to_apply = self.endpoint_rules.get(endpoint_path, [])
        else:
            constraints_to_apply = list(self.learned_constraints.keys())
        
        # Apply high-confidence constraints
        for constraint_id in constraints_to_apply:
            constraint = self.learned_constraints[constraint_id]
            if constraint.confidence_score > 0.7:
                self._apply_constraint_to_spec(enhanced_spec, constraint)
        
        return enhanced_spec
    
    def get_related_constraints(self, field_name: str, endpoint_path: str = None) -> List[LearnedConstraint]:
        """Get all constraints related to a specific field"""
        related_constraints = []
        
        for constraint_id, constraint in self.learned_constraints.items():
            if endpoint_path and constraint.endpoint_path != endpoint_path:
                continue
            
            # Direct field match
            if constraint.affected_parameter == field_name:
                related_constraints.append(constraint)
            
            # Conditional dependencies
            if (constraint.conditional_rule and 
                (constraint.conditional_rule.condition_field == field_name or 
                 constraint.conditional_rule.required_field == field_name)):
                related_constraints.append(constraint)
            
            # Format dependencies
            if (constraint.format_dependency and
                (constraint.format_dependency.dependent_field == field_name or
                 constraint.format_dependency.dependency_field == field_name)):
                related_constraints.append(constraint)
            
            # Mutual exclusivity
            if (constraint.exclusivity_rule and
                field_name in constraint.exclusivity_rule.exclusive_fields):
                related_constraints.append(constraint)
        
        return related_constraints
    def _apply_constraint_to_spec(self, spec: Dict[str, Any], constraint: LearnedConstraint):
        """Apply a learned constraint to the OpenAPI spec"""
        try:
            paths = spec.get('paths', {})
            if constraint.endpoint_path not in paths:
                return
            
            for method in paths[constraint.endpoint_path]:
                if method not in ['get', 'post', 'put', 'patch', 'delete']:
                    continue
                
                operation = paths[constraint.endpoint_path][method]
                
                # Apply different constraint types
                if constraint.constraint_type == ConstraintType.REQUIRED_FIELD:
                    self._apply_required_field_constraint(operation, constraint)
                elif constraint.constraint_type == ConstraintType.FORMAT_VALIDATION:
                    self._apply_format_constraint(operation, constraint)
                elif constraint.constraint_type == ConstraintType.CONDITIONAL_REQUIREMENT:
                    self._apply_conditional_constraint(operation, constraint)
                elif constraint.constraint_type == ConstraintType.MUTUAL_EXCLUSIVITY:
                    self._apply_exclusivity_constraint(operation, constraint)
                elif constraint.constraint_type == ConstraintType.FORMAT_DEPENDENCY:
                    self._apply_format_dependency_constraint(operation, constraint)
                elif constraint.constraint_type == ConstraintType.BUSINESS_RULE:
                    self._apply_business_rule_constraint(operation, constraint)
                    
        except Exception as e:
            print(f"Warning: Could not apply constraint {constraint.rule_description}: {e}")

    def _apply_required_field_constraint(self, operation: Dict, constraint: LearnedConstraint):
        """Apply required field constraint to operation"""
        if 'requestBody' in operation:
            content = operation['requestBody'].get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                if 'required' not in schema:
                    schema['required'] = []
                if constraint.affected_parameter not in schema['required']:
                    schema['required'].append(constraint.affected_parameter)

    def _apply_format_constraint(self, operation: Dict, constraint: LearnedConstraint):
        """Apply format validation constraint"""
        if 'requestBody' in operation:
            content = operation['requestBody'].get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                properties = schema.get('properties', {})
                if constraint.affected_parameter in properties:
                    format_rule = constraint.formal_constraint.get('format')
                    if format_rule:
                        properties[constraint.affected_parameter]['format'] = format_rule

    def _apply_conditional_constraint(self, operation: Dict, constraint: LearnedConstraint):
        """Apply conditional requirement constraint"""
        if constraint.conditional_rule:
            # Add conditional logic to x-conditional-requirements
            if 'x-conditional-requirements' not in operation:
                operation['x-conditional-requirements'] = []
            
            operation['x-conditional-requirements'].append({
                'condition': {
                    'field': constraint.conditional_rule.condition_field,
                    'operator': constraint.conditional_rule.condition_operator,
                    'value': constraint.conditional_rule.condition_value
                },
                'requirement': {
                    'field': constraint.conditional_rule.required_field,
                    'required': True
                }
            })

    def _apply_exclusivity_constraint(self, operation: Dict, constraint: LearnedConstraint):
        """Apply mutual exclusivity constraint"""
        if constraint.exclusivity_rule:
            if 'x-mutual-exclusivity' not in operation:
                operation['x-mutual-exclusivity'] = []
            
            operation['x-mutual-exclusivity'].append({
                'exclusive_fields': constraint.exclusivity_rule.exclusive_fields,
                'min_required': constraint.exclusivity_rule.min_required,
                'max_allowed': constraint.exclusivity_rule.max_allowed
            })

    def _apply_format_dependency_constraint(self, operation: Dict, constraint: LearnedConstraint):
        """Apply format dependency constraint"""
        if constraint.format_dependency:
            if 'x-format-dependencies' not in operation:
                operation['x-format-dependencies'] = []
            
            operation['x-format-dependencies'].append({
                'dependent_field': constraint.format_dependency.dependent_field,
                'dependency_field': constraint.format_dependency.dependency_field,
                'dependency_value': constraint.format_dependency.dependency_value,
                'required_format': constraint.format_dependency.required_format
            })

    def _apply_business_rule_constraint(self, operation: Dict, constraint: LearnedConstraint):
        """Apply business rule constraint"""
        if constraint.business_rule:
            if 'x-business-rules' not in operation:
                operation['x-business-rules'] = []
            
            operation['x-business-rules'].append({
                'field': constraint.business_rule.field,
                'rule_type': constraint.business_rule.rule_type,
                'constraint_value': constraint.business_rule.constraint_value,
                'error_message': constraint.business_rule.error_message
            })
