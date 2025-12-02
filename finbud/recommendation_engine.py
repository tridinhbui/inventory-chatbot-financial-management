"""
FinBud Recommendation Engine Integration
Enhanced recommendation system based on financial behavior analysis
"""

from typing import Dict, List, Optional
from datetime import datetime
import json

class FinBudRecommendationEngine:
    """FinBud Recommendation Engine"""
    
    def __init__(self):
        self.recommendations = []
        self.user_profiles = {}
        self.recommendation_history = {}
        
    def generate_recommendations(self, user_id: int, financial_data: Dict, 
                                 behavior_analysis: Dict) -> List[Dict]:
        """Generate personalized financial recommendations"""
        recommendations = []
        
        # Get user profile
        profile = self.user_profiles.get(user_id, {})
        
        # 1. Cashflow-based recommendations
        if 'volatility' in behavior_analysis:
            volatility = behavior_analysis['volatility']
            if volatility.get('volatility_level') == 'high':
                recommendations.append({
                    'id': f"rec_{user_id}_001",
                    'category': 'cashflow_stability',
                    'priority': 'high',
                    'title': 'Stabilize Your Cash Flow',
                    'description': 'Your cashflow shows high volatility. Here are ways to stabilize it.',
                    'actions': [
                        'Create a monthly budget with buffer funds',
                        'Set up automatic savings transfers',
                        'Track expenses daily for better visibility'
                    ],
                    'expected_impact': 'Reduce cashflow volatility by 30-40%',
                    'confidence_score': 0.85
                })
        
        # 2. Expense spike recommendations
        if 'spikes' in behavior_analysis:
            spikes = behavior_analysis['spikes']
            if spikes.get('spike_count', 0) > 3:
                recommendations.append({
                    'id': f"rec_{user_id}_002",
                    'category': 'expense_management',
                    'priority': 'medium',
                    'title': 'Manage Expense Spikes',
                    'description': f"You've experienced {spikes['spike_count']} expense spikes recently.",
                    'actions': [
                        'Set spending alerts for amounts above $500',
                        'Review and categorize all spike transactions',
                        'Create a "spike fund" for unexpected expenses'
                    ],
                    'expected_impact': 'Reduce unexpected expense impact by 25%',
                    'confidence_score': 0.75
                })
        
        # 3. Risk-based recommendations
        if 'risks' in behavior_analysis:
            risks = behavior_analysis['risks']
            risk_level = risks.get('risk_level', 'low')
            
            if risk_level in ['high', 'medium']:
                risk_factors = risks.get('risk_factors', [])
                recommendations.append({
                    'id': f"rec_{user_id}_003",
                    'category': 'risk_mitigation',
                    'priority': 'high' if risk_level == 'high' else 'medium',
                    'title': f'Address {risk_level.title()} Financial Risks',
                    'description': f'Detected {len(risk_factors)} risk factors requiring attention.',
                    'actions': self._generate_risk_actions(risk_factors),
                    'expected_impact': 'Improve financial stability score by 20-30%',
                    'confidence_score': 0.80
                })
        
        # 4. Savings recommendations
        if 'savings_rate' in financial_data:
            savings_rate = financial_data['savings_rate']
            if savings_rate < 20:
                recommendations.append({
                    'id': f"rec_{user_id}_004",
                    'category': 'savings',
                    'priority': 'medium',
                    'title': 'Increase Your Savings Rate',
                    'description': f'Current savings rate: {savings_rate:.1f}%. Target: 20%+',
                    'actions': [
                        'Automate 20% of income to savings account',
                        'Reduce discretionary spending by 15%',
                        'Set up separate savings goals'
                    ],
                    'expected_impact': f'Increase savings rate to {min(20, savings_rate + 5):.1f}%',
                    'confidence_score': 0.70
                })
        
        # 5. Category-specific recommendations
        if 'category_breakdown' in financial_data:
            category_breakdown = financial_data['category_breakdown']
            top_category = max(category_breakdown, key=lambda x: x.get('amount', 0)) if category_breakdown else None
            
            if top_category and top_category.get('percentage', 0) > 40:
                recommendations.append({
                    'id': f"rec_{user_id}_005",
                    'category': 'spending_optimization',
                    'priority': 'low',
                    'title': f'Optimize {top_category.get("category", "Spending")}',
                    'description': f'{top_category.get("category")} accounts for {top_category.get("percentage", 0):.1f}% of expenses.',
                    'actions': [
                        f'Review {top_category.get("category")} transactions for savings opportunities',
                        'Compare prices before major purchases',
                        'Look for subscription services to cancel'
                    ],
                    'expected_impact': 'Reduce category spending by 10-15%',
                    'confidence_score': 0.65
                })
        
        # Store recommendations
        self.recommendations.extend(recommendations)
        self.recommendation_history[user_id] = recommendations
        
        return recommendations
    
    def _generate_risk_actions(self, risk_factors: List[Dict]) -> List[str]:
        """Generate action items based on risk factors"""
        actions = []
        
        for factor in risk_factors:
            risk_type = factor.get('type', '')
            severity = factor.get('severity', 'medium')
            
            if risk_type == 'negative_cashflow_trend':
                actions.append('Immediately review and reduce non-essential expenses')
                actions.append('Consider additional income sources')
            elif risk_type == 'high_volatility':
                actions.append('Create emergency fund of 3-6 months expenses')
                actions.append('Implement consistent budgeting practices')
            elif risk_type == 'frequent_spikes':
                actions.append('Set up expense alerts and monitoring')
                actions.append('Plan for known upcoming large expenses')
            elif risk_type == 'low_savings':
                actions.append('Automate savings transfers')
                actions.append('Increase savings rate gradually')
            elif risk_type == 'increasing_expenses':
                actions.append('Review expense trends and identify causes')
                actions.append('Set spending limits by category')
        
        return list(set(actions))  # Remove duplicates
    
    def get_user_recommendations(self, user_id: int) -> List[Dict]:
        """Get all recommendations for a user"""
        return self.recommendation_history.get(user_id, [])
    
    def track_recommendation_impact(self, recommendation_id: str, 
                                   user_feedback: Dict) -> Dict:
        """Track the impact of a recommendation"""
        tracking = {
            'recommendation_id': recommendation_id,
            'user_feedback': user_feedback,
            'tracked_at': datetime.now().isoformat(),
            'effectiveness_score': user_feedback.get('effectiveness', 0),
            'adopted': user_feedback.get('adopted', False)
        }
        
        return tracking
    
    def update_user_profile(self, user_id: int, profile_data: Dict):
        """Update user profile for better recommendations"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        
        self.user_profiles[user_id].update(profile_data)
        self.user_profiles[user_id]['updated_at'] = datetime.now().isoformat()
    
    def get_recommendation_summary(self, user_id: int) -> Dict:
        """Get summary of recommendations for user"""
        recommendations = self.get_user_recommendations(user_id)
        
        if not recommendations:
            return {
                'user_id': user_id,
                'total_recommendations': 0,
                'by_priority': {},
                'by_category': {}
            }
        
        summary = {
            'user_id': user_id,
            'total_recommendations': len(recommendations),
            'by_priority': {
                'high': sum(1 for r in recommendations if r.get('priority') == 'high'),
                'medium': sum(1 for r in recommendations if r.get('priority') == 'medium'),
                'low': sum(1 for r in recommendations if r.get('priority') == 'low')
            },
            'by_category': {},
            'avg_confidence': sum(r.get('confidence_score', 0) for r in recommendations) / len(recommendations),
            'recommendations': recommendations
        }
        
        # Count by category
        for rec in recommendations:
            category = rec.get('category', 'other')
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
        
        return summary
    
    def export_recommendations(self, filename: str = 'finbud/recommendations.json'):
        """Export all recommendations"""
        data = {
            'recommendations': self.recommendations,
            'user_profiles': self.user_profiles,
            'recommendation_history': self.recommendation_history,
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"✅ Recommendations exported to {filename}")


if __name__ == "__main__":
    engine = FinBudRecommendationEngine()
    
    # Sample usage
    financial_data = {
        'savings_rate': 15.5,
        'category_breakdown': [
            {'category': 'Groceries', 'amount': 500, 'percentage': 45}
        ]
    }
    
    behavior_analysis = {
        'volatility': {'volatility_level': 'high'},
        'spikes': {'spike_count': 5},
        'risks': {'risk_level': 'medium', 'risk_factors': []}
    }
    
    recommendations = engine.generate_recommendations(1, financial_data, behavior_analysis)
    
    print(f"✅ Generated {len(recommendations)} recommendations")
    for rec in recommendations:
        print(f"   - {rec['title']} ({rec['priority']} priority)")


