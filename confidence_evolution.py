from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
from constraint_model import LearnedConstraint, ConstraintType

@dataclass
class ValidationEvent:
    """Represents a constraint validation event"""
    constraint_id: str
    validation_time: datetime
    success: bool
    context: Dict[str, Any] = field(default_factory=dict)
    confidence_before: float = 0.0
    confidence_after: float = 0.0

@dataclass
class ConfidenceMetrics:
    """Metrics for constraint confidence analysis"""
    current_confidence: float
    historical_accuracy: float
    trend_direction: str  # "improving", "declining", "stable"
    validation_count: int
    recent_performance: float  # Performance in last N validations
    stability_score: float  # How stable the confidence has been

class AdvancedConfidenceEvolution:
    def __init__(self, lookback_window: int = 10):
        self.validation_history: Dict[str, List[ValidationEvent]] = {}
        self.lookback_window = lookback_window
        self.confidence_thresholds = {
            'high': 0.85,
            'medium': 0.65,
            'low': 0.45
        }
    
    def record_validation_event(self, constraint_id: str, success: bool, context: Dict[str, Any] = None):
        """Record a validation event for confidence evolution"""
        if constraint_id not in self.validation_history:
            self.validation_history[constraint_id] = []
        
        event = ValidationEvent(
            constraint_id=constraint_id,
            validation_time=datetime.now(),
            success=success,
            context=context or {}
        )
        
        self.validation_history[constraint_id].append(event)
        
        # Keep only recent events within lookback window
        if len(self.validation_history[constraint_id]) > self.lookback_window:
            self.validation_history[constraint_id] = self.validation_history[constraint_id][-self.lookback_window:]
    
    def calculate_evolved_confidence(self, constraint: LearnedConstraint) -> ConfidenceMetrics:
        """Calculate evolved confidence based on validation history"""
        constraint_id = f"{constraint.endpoint_path}_{constraint.affected_parameter}_{constraint.constraint_type.value}"
        
        if constraint_id not in self.validation_history:
            return ConfidenceMetrics(
                current_confidence=constraint.confidence_score,
                historical_accuracy=constraint.confidence_score,
                trend_direction="stable",
                validation_count=0,
                recent_performance=constraint.confidence_score,
                stability_score=1.0
            )
        
        events = self.validation_history[constraint_id]
        
        # Calculate historical accuracy
        total_events = len(events)
        successful_events = sum(1 for event in events if event.success)
        historical_accuracy = successful_events / total_events if total_events > 0 else constraint.confidence_score
        
        # Calculate recent performance (last 5 events)
        recent_events = events[-5:] if len(events) >= 5 else events
        recent_successful = sum(1 for event in recent_events if event.success)
        recent_performance = recent_successful / len(recent_events) if recent_events else historical_accuracy
        
        # Calculate trend direction
        if len(events) >= 4:
            first_half = events[:len(events)//2]
            second_half = events[len(events)//2:]
            
            first_half_accuracy = sum(1 for e in first_half if e.success) / len(first_half)
            second_half_accuracy = sum(1 for e in second_half if e.success) / len(second_half)
            
            if second_half_accuracy > first_half_accuracy + 0.1:
                trend_direction = "improving"
            elif second_half_accuracy < first_half_accuracy - 0.1:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        # Calculate stability score (how consistent the results are)
        if len(events) >= 3:
            success_rates = []
            for i in range(len(events) - 2):
                window = events[i:i+3]
                rate = sum(1 for e in window if e.success) / len(window)
                success_rates.append(rate)
            
            stability_score = 1.0 - statistics.stdev(success_rates) if len(success_rates) > 1 else 1.0
        else:
            stability_score = 1.0
        
        # Calculate evolved confidence
        base_confidence = constraint.confidence_score
        
        # Weight factors
        historical_weight = 0.4
        recent_weight = 0.4
        trend_weight = 0.2
        
        evolved_confidence = (
            base_confidence * (1 - historical_weight - recent_weight - trend_weight) +
            historical_accuracy * historical_weight +
            recent_performance * recent_weight
        )
        
        # Apply trend adjustment
        if trend_direction == "improving":
            evolved_confidence = min(1.0, evolved_confidence + 0.05)
        elif trend_direction == "declining":
            evolved_confidence = max(0.0, evolved_confidence - 0.05)
        
        # Apply stability adjustment
        evolved_confidence = evolved_confidence * stability_score
        
        return ConfidenceMetrics(
            current_confidence=evolved_confidence,
            historical_accuracy=historical_accuracy,
            trend_direction=trend_direction,
            validation_count=total_events,
            recent_performance=recent_performance,
            stability_score=stability_score
        )
    
    def get_confidence_recommendations(self, constraints: Dict[str, LearnedConstraint]) -> List[Dict[str, Any]]:
        """Get recommendations for constraint confidence management"""
        recommendations = []
        
        for constraint_id, constraint in constraints.items():
            metrics = self.calculate_evolved_confidence(constraint)
            
            # High confidence, declining trend
            if metrics.current_confidence > 0.8 and metrics.trend_direction == "declining":
                recommendations.append({
                    'constraint_id': constraint_id,
                    'recommendation_type': 'monitor_closely',
                    'message': f"High-confidence constraint showing declining performance. Monitor for API changes.",
                    'priority': 'high',
                    'metrics': metrics
                })
            
            # Low confidence, improving trend
            elif metrics.current_confidence < 0.5 and metrics.trend_direction == "improving":
                recommendations.append({
                    'constraint_id': constraint_id,
                    'recommendation_type': 'promote_confidence',
                    'message': f"Low-confidence constraint showing improvement. Consider increasing weight in test generation.",
                    'priority': 'medium',
                    'metrics': metrics
                })
            
            # Low stability
            elif metrics.stability_score < 0.5:
                recommendations.append({
                    'constraint_id': constraint_id,
                    'recommendation_type': 'investigate_instability',
                    'message': f"Constraint showing unstable behavior. May need context-dependent refinement.",
                    'priority': 'high',
                    'metrics': metrics
                })
            
            # Very low confidence
            elif metrics.current_confidence < 0.3:
                recommendations.append({
                    'constraint_id': constraint_id,
                    'recommendation_type': 'consider_removal',
                    'message': f"Very low confidence constraint. Consider removing or re-learning.",
                    'priority': 'medium',
                    'metrics': metrics
                })
        
        return sorted(recommendations, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)
    
    def export_confidence_analysis(self) -> Dict[str, Any]:
        """Export confidence evolution analysis"""
        return {
            'validation_events_count': sum(len(events) for events in self.validation_history.values()),
            'tracked_constraints': len(self.validation_history),
            'confidence_thresholds': self.confidence_thresholds,
            'lookback_window': self.lookback_window,
            'validation_history_summary': {
                constraint_id: {
                    'total_validations': len(events),
                    'success_rate': sum(1 for e in events if e.success) / len(events) if events else 0,
                    'most_recent': events[-1].validation_time.isoformat() if events else None
                }
                for constraint_id, events in self.validation_history.items()
            }
        }
