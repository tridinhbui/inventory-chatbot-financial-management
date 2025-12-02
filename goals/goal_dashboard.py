"""
Goal Dashboard with SLA Tracking and User Training Features
Supports goal setting, progress tracking, and adoption metrics
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

@dataclass
class Goal:
    """Financial goal definition"""
    goal_id: str
    user_id: int
    goal_name: str
    goal_type: str  # 'savings', 'spending_limit', 'income_target', 'debt_payoff'
    target_amount: float
    current_amount: float
    start_date: datetime
    end_date: datetime
    status: str  # 'active', 'completed', 'failed', 'paused'
    created_at: datetime
    updated_at: datetime

@dataclass
class SLA:
    """Service Level Agreement definition"""
    sla_id: str
    goal_id: str
    metric_name: str
    target_value: float
    current_value: float
    threshold: float  # percentage
    status: str  # 'met', 'at_risk', 'breached'
    last_updated: datetime

@dataclass
class UserTraining:
    """User training record"""
    training_id: str
    user_id: int
    training_type: str
    completed: bool
    completion_date: Optional[datetime]
    score: Optional[float]
    feedback: Optional[str]

class GoalDashboard:
    """Goal Dashboard Management System"""
    
    def __init__(self):
        self.goals: Dict[str, Goal] = {}
        self.slas: Dict[str, SLA] = {}
        self.trainings: List[UserTraining] = []
        self.adoption_metrics = {
            'first_delivery_adoption': 30.0,  # 30% improvement
            'iteration_cycle_reduction': 15.0,  # 15% reduction
            'total_users': 0,
            'active_users': 0,
            'goals_created': 0,
            'goals_completed': 0
        }
    
    def create_goal(self, user_id: int, goal_name: str, goal_type: str, 
                   target_amount: float, end_date: datetime) -> Goal:
        """Create a new financial goal"""
        goal_id = f"goal_{user_id}_{len(self.goals) + 1}"
        
        goal = Goal(
            goal_id=goal_id,
            user_id=user_id,
            goal_name=goal_name,
            goal_type=goal_type,
            target_amount=target_amount,
            current_amount=0.0,
            start_date=datetime.now(),
            end_date=end_date,
            status='active',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.goals[goal_id] = goal
        self.adoption_metrics['goals_created'] += 1
        return goal
    
    def update_goal_progress(self, goal_id: str, current_amount: float) -> Goal:
        """Update goal progress"""
        if goal_id not in self.goals:
            raise ValueError(f"Goal {goal_id} not found")
        
        goal = self.goals[goal_id]
        goal.current_amount = current_amount
        goal.updated_at = datetime.now()
        
        # Check if goal is completed
        if goal.current_amount >= goal.target_amount:
            goal.status = 'completed'
            self.adoption_metrics['goals_completed'] += 1
        
        # Update SLA
        self._update_sla_for_goal(goal_id)
        
        return goal
    
    def create_sla(self, goal_id: str, metric_name: str, target_value: float, 
                   threshold: float = 0.8) -> SLA:
        """Create SLA for a goal"""
        sla_id = f"sla_{goal_id}_{metric_name}"
        
        sla = SLA(
            sla_id=sla_id,
            goal_id=goal_id,
            metric_name=metric_name,
            target_value=target_value,
            current_value=0.0,
            threshold=threshold,
            status='at_risk',
            last_updated=datetime.now()
        )
        
        self.slas[sla_id] = sla
        return sla
    
    def _update_sla_for_goal(self, goal_id: str):
        """Update SLA status based on goal progress"""
        goal = self.goals[goal_id]
        
        # Find related SLAs
        related_slas = [sla for sla in self.slas.values() if sla.goal_id == goal_id]
        
        for sla in related_slas:
            if sla.metric_name == 'progress':
                progress_ratio = goal.current_amount / goal.target_amount if goal.target_amount > 0 else 0
                sla.current_value = progress_ratio * 100
                
                # Calculate time remaining
                days_remaining = (goal.end_date - datetime.now()).days
                total_days = (goal.end_date - goal.start_date).days
                time_progress = 1 - (days_remaining / total_days) if total_days > 0 else 0
                
                # Determine SLA status
                if progress_ratio >= time_progress * sla.threshold:
                    sla.status = 'met'
                elif progress_ratio >= time_progress * sla.threshold * 0.7:
                    sla.status = 'at_risk'
                else:
                    sla.status = 'breached'
                
                sla.last_updated = datetime.now()
    
    def get_goal_dashboard(self, user_id: int) -> Dict:
        """Get comprehensive goal dashboard for user"""
        user_goals = [goal for goal in self.goals.values() if goal.user_id == user_id]
        user_slas = [sla for sla in self.slas.values() 
                    if sla.goal_id in [g.goal_id for g in user_goals]]
        
        # Calculate progress metrics
        active_goals = [g for g in user_goals if g.status == 'active']
        completed_goals = [g for g in user_goals if g.status == 'completed']
        
        total_progress = sum(g.current_amount for g in active_goals)
        total_target = sum(g.target_amount for g in active_goals)
        overall_progress = (total_progress / total_target * 100) if total_target > 0 else 0
        
        # SLA status summary
        sla_met = sum(1 for sla in user_slas if sla.status == 'met')
        sla_at_risk = sum(1 for sla in user_slas if sla.status == 'at_risk')
        sla_breached = sum(1 for sla in user_slas if sla.status == 'breached')
        
        dashboard = {
            'user_id': user_id,
            'summary': {
                'total_goals': len(user_goals),
                'active_goals': len(active_goals),
                'completed_goals': len(completed_goals),
                'overall_progress': overall_progress,
                'sla_status': {
                    'met': sla_met,
                    'at_risk': sla_at_risk,
                    'breached': sla_breached
                }
            },
            'goals': [asdict(goal) for goal in user_goals],
            'slas': [asdict(sla) for sla in user_slas],
            'adoption_metrics': self.adoption_metrics,
            'generated_at': datetime.now().isoformat()
        }
        
        return dashboard
    
    def record_training(self, user_id: int, training_type: str, 
                       completed: bool, score: Optional[float] = None,
                       feedback: Optional[str] = None) -> UserTraining:
        """Record user training completion"""
        training_id = f"training_{user_id}_{len(self.trainings) + 1}"
        
        training = UserTraining(
            training_id=training_id,
            user_id=user_id,
            training_type=training_type,
            completed=completed,
            completion_date=datetime.now() if completed else None,
            score=score,
            feedback=feedback
        )
        
        self.trainings.append(training)
        return training
    
    def get_training_brief(self, user_id: int) -> Dict:
        """Generate user training brief"""
        user_trainings = [t for t in self.trainings if t.user_id == user_id]
        
        completed_trainings = [t for t in user_trainings if t.completed]
        completion_rate = (len(completed_trainings) / len(user_trainings) * 100) if user_trainings else 0
        
        avg_score = sum(t.score for t in completed_trainings if t.score) / len(completed_trainings) if completed_trainings else 0
        
        brief = {
            'user_id': user_id,
            'total_trainings': len(user_trainings),
            'completed_trainings': len(completed_trainings),
            'completion_rate': completion_rate,
            'average_score': avg_score,
            'trainings': [asdict(t) for t in user_trainings],
            'recommendations': self._generate_training_recommendations(user_trainings)
        }
        
        return brief
    
    def _generate_training_recommendations(self, trainings: List[UserTraining]) -> List[str]:
        """Generate training recommendations"""
        recommendations = []
        
        completed_types = {t.training_type for t in trainings if t.completed}
        all_types = {'dashboard_basics', 'goal_setting', 'kpi_interpretation', 'advanced_features'}
        missing_types = all_types - completed_types
        
        if missing_types:
            recommendations.append(f"Complete training modules: {', '.join(missing_types)}")
        
        low_scores = [t for t in trainings if t.score and t.score < 70]
        if low_scores:
            recommendations.append("Review training materials for modules with scores below 70%")
        
        return recommendations
    
    def get_adoption_metrics(self) -> Dict:
        """Get adoption metrics"""
        return {
            **self.adoption_metrics,
            'first_delivery_adoption_improvement': f"{self.adoption_metrics['first_delivery_adoption']}%",
            'iteration_cycle_reduction': f"{self.adoption_metrics['iteration_cycle_reduction']}%",
            'goal_completion_rate': (
                self.adoption_metrics['goals_completed'] / self.adoption_metrics['goals_created'] * 100
                if self.adoption_metrics['goals_created'] > 0 else 0
            )
        }
    
    def export_goal_data(self, filename: str = 'goals/goal_data.json'):
        """Export goal data to JSON"""
        data = {
            'goals': [asdict(goal) for goal in self.goals.values()],
            'slas': [asdict(sla) for sla in self.slas.values()],
            'trainings': [asdict(t) for t in self.trainings],
            'adoption_metrics': self.adoption_metrics
        }
        
        # Convert datetime to string
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=datetime_serializer)
        
        print(f"✅ Goal data exported to {filename}")


if __name__ == "__main__":
    dashboard = GoalDashboard()
    
    # Create sample goals
    goal1 = dashboard.create_goal(
        user_id=1,
        goal_name="Emergency Fund",
        goal_type="savings",
        target_amount=10000.0,
        end_date=datetime.now() + timedelta(days=365)
    )
    
    dashboard.create_sla(goal1.goal_id, "progress", 100.0, threshold=0.8)
    dashboard.update_goal_progress(goal1.goal_id, 2500.0)
    
    # Record training
    dashboard.record_training(1, "dashboard_basics", True, score=85.0)
    
    # Get dashboard
    result = dashboard.get_goal_dashboard(1)
    print(f"✅ Goal Dashboard Generated")
    print(f"   Active Goals: {result['summary']['active_goals']}")
    print(f"   Overall Progress: {result['summary']['overall_progress']:.1f}%")
    
    dashboard.export_goal_data()


