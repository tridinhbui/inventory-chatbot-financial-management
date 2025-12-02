"""
Multi-User Financial Behavior Analysis
Analyzes cashflow volatility, expense spikes, and risk patterns
Enhances FinBud recommendation engine
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import json
from collections import defaultdict

class MultiUserFinancialAnalyzer:
    """Analyze financial behaviors across multiple users"""
    
    def __init__(self):
        self.user_data = {}
        self.patterns = {}
        self.risk_scores = {}
        
    def load_user_transactions(self, user_id: int, transactions: List[Dict]):
        """Load transactions for a user"""
        df = pd.DataFrame(transactions)
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'])
        
        self.user_data[user_id] = df
        return df
    
    def analyze_cashflow_volatility(self, user_id: int) -> Dict:
        """Analyze cashflow volatility for a user"""
        if user_id not in self.user_data:
            return {}
        
        df = self.user_data[user_id].copy()
        
        # Group by month
        df['year_month'] = df['transaction_date'].dt.to_period('M')
        monthly_cashflow = df.groupby('year_month').apply(
            lambda x: x[x['transaction_type'] == 'income']['amount'].sum() - 
                     x[x['transaction_type'] == 'expense']['amount'].sum()
        )
        
        if len(monthly_cashflow) < 2:
            return {'volatility_score': 0, 'volatility_level': 'low'}
        
        # Calculate volatility metrics
        mean_cashflow = monthly_cashflow.mean()
        std_cashflow = monthly_cashflow.std()
        cv = (std_cashflow / abs(mean_cashflow)) * 100 if mean_cashflow != 0 else 0
        
        # Classify volatility
        if cv < 20:
            level = 'low'
        elif cv < 50:
            level = 'medium'
        else:
            level = 'high'
        
        volatility_data = {
            'user_id': user_id,
            'volatility_score': float(cv),
            'volatility_level': level,
            'mean_monthly_cashflow': float(mean_cashflow),
            'std_monthly_cashflow': float(std_cashflow),
            'monthly_values': monthly_cashflow.tolist(),
            'trend': self._calculate_trend(monthly_cashflow.values)
        }
        
        return volatility_data
    
    def detect_expense_spikes(self, user_id: int, threshold_multiplier: float = 2.0) -> Dict:
        """Detect expense spikes"""
        if user_id not in self.user_data:
            return {}
        
        df = self.user_data[user_id].copy()
        expenses = df[df['transaction_type'] == 'expense'].copy()
        
        if len(expenses) == 0:
            return {'spikes': [], 'spike_count': 0}
        
        # Calculate daily expenses
        expenses['date'] = expenses['transaction_date'].dt.date
        daily_expenses = expenses.groupby('date')['amount'].sum()
        
        mean_expense = daily_expenses.mean()
        std_expense = daily_expenses.std()
        threshold = mean_expense + (threshold_multiplier * std_expense)
        
        # Find spikes
        spikes = daily_expenses[daily_expenses > threshold]
        
        spike_details = []
        for date, amount in spikes.items():
            day_expenses = expenses[expenses['date'] == date]
            spike_details.append({
                'date': str(date),
                'total_amount': float(amount),
                'transaction_count': len(day_expenses),
                'categories': day_expenses.groupby('category_id')['amount'].sum().to_dict(),
                'spike_ratio': float(amount / mean_expense) if mean_expense > 0 else 0
            })
        
        return {
            'user_id': user_id,
            'spikes': spike_details,
            'spike_count': len(spikes),
            'mean_daily_expense': float(mean_expense),
            'threshold': float(threshold),
            'spike_frequency': len(spikes) / len(daily_expenses) * 100 if len(daily_expenses) > 0 else 0
        }
    
    def identify_risk_patterns(self, user_id: int) -> Dict:
        """Identify financial risk patterns"""
        if user_id not in self.user_data:
            return {}
        
        df = self.user_data[user_id].copy()
        
        risks = {
            'user_id': user_id,
            'risk_factors': [],
            'risk_score': 0.0,
            'risk_level': 'low'
        }
        
        # Risk 1: Negative cashflow trend
        monthly_cashflow = self._get_monthly_cashflow(user_id)
        if len(monthly_cashflow) >= 3:
            recent_trend = monthly_cashflow[-3:].mean()
            if recent_trend < 0:
                risks['risk_factors'].append({
                    'type': 'negative_cashflow_trend',
                    'severity': 'high' if recent_trend < -500 else 'medium',
                    'description': 'Consistent negative cashflow in recent months'
                })
                risks['risk_score'] += 30
        
        # Risk 2: High expense volatility
        volatility = self.analyze_cashflow_volatility(user_id)
        if volatility.get('volatility_level') == 'high':
            risks['risk_factors'].append({
                'type': 'high_volatility',
                'severity': 'high',
                'description': 'High cashflow volatility indicates unstable finances'
            })
            risks['risk_score'] += 25
        
        # Risk 3: Frequent expense spikes
        spikes = self.detect_expense_spikes(user_id)
        if spikes.get('spike_frequency', 0) > 10:
            risks['risk_factors'].append({
                'type': 'frequent_spikes',
                'severity': 'medium',
                'description': f"Frequent expense spikes ({spikes['spike_count']} detected)"
            })
            risks['risk_score'] += 20
        
        # Risk 4: Low savings rate
        savings_rate = self._calculate_savings_rate(user_id)
        if savings_rate < 10:
            risks['risk_factors'].append({
                'type': 'low_savings',
                'severity': 'high' if savings_rate < 5 else 'medium',
                'description': f'Low savings rate: {savings_rate:.1f}%'
            })
            risks['risk_score'] += 25
        
        # Risk 5: Increasing debt/expenses
        expense_trend = self._calculate_expense_trend(user_id)
        if expense_trend > 0.1:  # 10% increase
            risks['risk_factors'].append({
                'type': 'increasing_expenses',
                'severity': 'medium',
                'description': f'Expenses increasing at {expense_trend*100:.1f}% rate'
            })
            risks['risk_score'] += 15
        
        # Determine overall risk level
        if risks['risk_score'] >= 70:
            risks['risk_level'] = 'high'
        elif risks['risk_score'] >= 40:
            risks['risk_level'] = 'medium'
        else:
            risks['risk_level'] = 'low'
        
        self.risk_scores[user_id] = risks
        return risks
    
    def analyze_all_users(self) -> Dict:
        """Analyze all users and generate insights"""
        all_insights = {
            'total_users': len(self.user_data),
            'user_analyses': {},
            'aggregate_patterns': {},
            'generated_at': datetime.now().isoformat()
        }
        
        volatility_scores = []
        risk_scores = []
        spike_counts = []
        
        for user_id in self.user_data.keys():
            # Individual analysis
            volatility = self.analyze_cashflow_volatility(user_id)
            spikes = self.detect_expense_spikes(user_id)
            risks = self.identify_risk_patterns(user_id)
            
            all_insights['user_analyses'][user_id] = {
                'volatility': volatility,
                'spikes': spikes,
                'risks': risks
            }
            
            # Aggregate metrics
            if volatility:
                volatility_scores.append(volatility.get('volatility_score', 0))
            if spikes:
                spike_counts.append(spikes.get('spike_count', 0))
            if risks:
                risk_scores.append(risks.get('risk_score', 0))
        
        # Aggregate patterns
        all_insights['aggregate_patterns'] = {
            'avg_volatility': np.mean(volatility_scores) if volatility_scores else 0,
            'avg_risk_score': np.mean(risk_scores) if risk_scores else 0,
            'total_spikes': sum(spike_counts),
            'high_risk_users': sum(1 for r in risk_scores if r >= 70),
            'medium_risk_users': sum(1 for r in risk_scores if 40 <= r < 70),
            'low_risk_users': sum(1 for r in risk_scores if r < 40)
        }
        
        return all_insights
    
    def generate_finbud_recommendations(self, user_id: int) -> List[Dict]:
        """Generate recommendations for FinBud recommendation engine"""
        recommendations = []
        
        if user_id not in self.user_data:
            return recommendations
        
        # Get analysis results
        volatility = self.analyze_cashflow_volatility(user_id)
        spikes = self.detect_expense_spikes(user_id)
        risks = self.identify_risk_patterns(user_id)
        
        # Recommendation 1: Based on volatility
        if volatility.get('volatility_level') == 'high':
            recommendations.append({
                'type': 'cashflow_stabilization',
                'priority': 'high',
                'title': 'Stabilize Cash Flow',
                'description': 'Your cashflow shows high volatility. Consider creating a budget buffer.',
                'action_items': [
                    'Set aside 3-6 months of expenses as emergency fund',
                    'Track expenses more consistently',
                    'Consider income diversification'
                ]
            })
        
        # Recommendation 2: Based on expense spikes
        if spikes.get('spike_count', 0) > 5:
            recommendations.append({
                'type': 'expense_management',
                'priority': 'medium',
                'title': 'Manage Expense Spikes',
                'description': f"You've had {spikes['spike_count']} expense spikes recently.",
                'action_items': [
                    'Review categories with frequent spikes',
                    'Set spending alerts for high-amount transactions',
                    'Plan for known upcoming expenses'
                ]
            })
        
        # Recommendation 3: Based on risk patterns
        if risks.get('risk_level') == 'high':
            recommendations.append({
                'type': 'risk_mitigation',
                'priority': 'high',
                'title': 'Address Financial Risks',
                'description': 'Multiple risk factors detected. Immediate action recommended.',
                'action_items': [
                    'Review and reduce unnecessary expenses',
                    'Increase savings rate to at least 20%',
                    'Consider financial counseling'
                ]
            })
        
        # Recommendation 4: Savings improvement
        savings_rate = self._calculate_savings_rate(user_id)
        if savings_rate < 20:
            recommendations.append({
                'type': 'savings_improvement',
                'priority': 'medium',
                'title': 'Improve Savings Rate',
                'description': f'Current savings rate: {savings_rate:.1f}%. Target: 20%+',
                'action_items': [
                    'Automate savings transfers',
                    'Reduce discretionary spending',
                    'Set specific savings goals'
                ]
            })
        
        return recommendations
    
    def _get_monthly_cashflow(self, user_id: int) -> pd.Series:
        """Get monthly cashflow series"""
        df = self.user_data[user_id].copy()
        df['year_month'] = df['transaction_date'].dt.to_period('M')
        return df.groupby('year_month').apply(
            lambda x: x[x['transaction_type'] == 'income']['amount'].sum() - 
                     x[x['transaction_type'] == 'expense']['amount'].sum()
        )
    
    def _calculate_trend(self, values: np.ndarray) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear trend
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_savings_rate(self, user_id: int) -> float:
        """Calculate savings rate"""
        df = self.user_data[user_id].copy()
        
        total_income = df[df['transaction_type'] == 'income']['amount'].sum()
        total_expenses = df[df['transaction_type'] == 'expense']['amount'].sum()
        
        if total_income == 0:
            return 0.0
        
        savings = total_income - total_expenses
        return (savings / total_income) * 100
    
    def _calculate_expense_trend(self, user_id: int) -> float:
        """Calculate expense growth trend"""
        df = self.user_data[user_id].copy()
        expenses = df[df['transaction_type'] == 'expense'].copy()
        
        if len(expenses) < 2:
            return 0.0
        
        expenses['year_month'] = expenses['transaction_date'].dt.to_period('M')
        monthly_expenses = expenses.groupby('year_month')['amount'].sum()
        
        if len(monthly_expenses) < 2:
            return 0.0
        
        # Calculate growth rate
        first_half = monthly_expenses[:len(monthly_expenses)//2].mean()
        second_half = monthly_expenses[len(monthly_expenses)//2:].mean()
        
        if first_half == 0:
            return 0.0
        
        return (second_half - first_half) / first_half
    
    def export_analysis(self, filename: str = 'analytics/multi_user_analysis.json'):
        """Export analysis results"""
        all_insights = self.analyze_all_users()
        
        with open(filename, 'w') as f:
            json.dump(all_insights, f, indent=2, default=str)
        
        print(f"✅ Multi-user analysis exported to {filename}")


if __name__ == "__main__":
    analyzer = MultiUserFinancialAnalyzer()
    
    # Sample data
    sample_transactions = [
        {
            'transaction_date': '2024-01-15',
            'amount': 5000,
            'transaction_type': 'income',
            'category_id': 1
        },
        {
            'transaction_date': '2024-01-20',
            'amount': 2000,
            'transaction_type': 'expense',
            'category_id': 2
        }
    ]
    
    analyzer.load_user_transactions(1, sample_transactions)
    
    volatility = analyzer.analyze_cashflow_volatility(1)
    spikes = analyzer.detect_expense_spikes(1)
    risks = analyzer.identify_risk_patterns(1)
    recommendations = analyzer.generate_finbud_recommendations(1)
    
    print("📊 Multi-User Financial Analysis")
    print(f"   Volatility Level: {volatility.get('volatility_level', 'N/A')}")
    print(f"   Risk Level: {risks.get('risk_level', 'N/A')}")
    print(f"   Recommendations: {len(recommendations)}")


