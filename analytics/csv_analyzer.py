"""
CSV Data Analyzer for Retail Store Inventory and Walmart Sales Data
Analyzes financial patterns, inventory trends, and sales performance
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import json

class CSVDataAnalyzer:
    """Analyze retail inventory and sales data"""
    
    def __init__(self, inventory_path: str, walmart_path: str):
        self.inventory_path = inventory_path
        self.walmart_path = walmart_path
        self.inventory_df = None
        self.walmart_df = None
        
    def load_data(self):
        """Load CSV files into DataFrames"""
        try:
            self.inventory_df = pd.read_csv(self.inventory_path)
            self.walmart_df = pd.read_csv(self.walmart_path)
            
            # Parse dates
            self.inventory_df['Date'] = pd.to_datetime(self.inventory_df['Date'])
            self.walmart_df['Date'] = pd.to_datetime(self.walmart_df['Date'], format='%d-%m-%Y')
            
            print(f"✅ Loaded {len(self.inventory_df)} inventory records")
            print(f"✅ Loaded {len(self.walmart_df)} Walmart sales records")
            return True
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def analyze_inventory_financials(self) -> Dict:
        """Analyze financial aspects of inventory data"""
        if self.inventory_df is None:
            return {}
        
        df = self.inventory_df.copy()
        
        # Calculate revenue
        df['Revenue'] = df['Units Sold'] * df['Price'] * (1 - df['Discount'] / 100)
        df['Cost'] = df['Units Ordered'] * df['Price']
        df['Profit'] = df['Revenue'] - df['Cost']
        
        analysis = {
            'total_revenue': float(df['Revenue'].sum()),
            'total_cost': float(df['Cost'].sum()),
            'total_profit': float(df['Profit'].sum()),
            'profit_margin': float((df['Profit'].sum() / df['Revenue'].sum() * 100) if df['Revenue'].sum() > 0 else 0),
            'avg_price': float(df['Price'].mean()),
            'total_units_sold': int(df['Units Sold'].sum()),
            'total_units_ordered': int(df['Units Ordered'].sum()),
            'inventory_turnover': float(df['Units Sold'].sum() / df['Inventory Level'].mean() if df['Inventory Level'].mean() > 0 else 0),
            'category_breakdown': df.groupby('Category').agg({
                'Revenue': 'sum',
                'Profit': 'sum',
                'Units Sold': 'sum'
            }).to_dict('index'),
            'region_performance': df.groupby('Region').agg({
                'Revenue': 'sum',
                'Profit': 'sum'
            }).to_dict('index'),
            'seasonal_trends': df.groupby('Seasonality').agg({
                'Revenue': 'sum',
                'Units Sold': 'sum'
            }).to_dict('index')
        }
        
        return analysis
    
    def analyze_walmart_sales(self) -> Dict:
        """Analyze Walmart sales data"""
        if self.walmart_df is None:
            return {}
        
        df = self.walmart_df.copy()
        
        analysis = {
            'total_sales': float(df['Weekly_Sales'].sum()),
            'avg_weekly_sales': float(df['Weekly_Sales'].mean()),
            'total_weeks': len(df),
            'holiday_impact': {
                'holiday_sales': float(df[df['Holiday_Flag'] == 1]['Weekly_Sales'].mean()),
                'non_holiday_sales': float(df[df['Holiday_Flag'] == 0]['Weekly_Sales'].mean()),
                'holiday_lift': float((df[df['Holiday_Flag'] == 1]['Weekly_Sales'].mean() / 
                                     df[df['Holiday_Flag'] == 0]['Weekly_Sales'].mean() - 1) * 100) if df[df['Holiday_Flag'] == 0]['Weekly_Sales'].mean() > 0 else 0
            },
            'store_performance': df.groupby('Store').agg({
                'Weekly_Sales': ['sum', 'mean', 'std']
            }).to_dict(),
            'correlations': {
                'temperature_sales': float(df['Temperature'].corr(df['Weekly_Sales'])),
                'fuel_price_sales': float(df['Fuel_Price'].corr(df['Weekly_Sales'])),
                'cpi_sales': float(df['CPI'].corr(df['Weekly_Sales'])),
                'unemployment_sales': float(df['Unemployment'].corr(df['Weekly_Sales']))
            },
            'monthly_trends': df.groupby(df['Date'].dt.to_period('M')).agg({
                'Weekly_Sales': 'sum'
            }).to_dict('index')
        }
        
        return analysis
    
    def detect_anomalies(self) -> Dict:
        """Detect anomalies in sales and inventory"""
        anomalies = {
            'inventory': {},
            'sales': {}
        }
        
        if self.inventory_df is not None:
            df = self.inventory_df.copy()
            
            # Detect low inventory levels
            threshold = df['Inventory Level'].quantile(0.1)
            low_inventory = df[df['Inventory Level'] < threshold]
            anomalies['inventory']['low_stock'] = {
                'count': len(low_inventory),
                'products': low_inventory[['Store ID', 'Product ID', 'Category', 'Inventory Level']].to_dict('records')
            }
            
            # Detect high demand vs inventory
            df['demand_ratio'] = df['Demand Forecast'] / (df['Inventory Level'] + 1)
            high_demand = df[df['demand_ratio'] > 2]
            anomalies['inventory']['high_demand_risk'] = {
                'count': len(high_demand),
                'items': high_demand[['Store ID', 'Product ID', 'Demand Forecast', 'Inventory Level']].to_dict('records')
            }
        
        if self.walmart_df is not None:
            df = self.walmart_df.copy()
            
            # Detect sales spikes
            mean_sales = df['Weekly_Sales'].mean()
            std_sales = df['Weekly_Sales'].std()
            spikes = df[df['Weekly_Sales'] > mean_sales + 2 * std_sales]
            anomalies['sales']['spikes'] = {
                'count': len(spikes),
                'records': spikes[['Store', 'Date', 'Weekly_Sales']].to_dict('records')
            }
            
            # Detect sales drops
            drops = df[df['Weekly_Sales'] < mean_sales - 2 * std_sales]
            anomalies['sales']['drops'] = {
                'count': len(drops),
                'records': drops[['Store', 'Date', 'Weekly_Sales']].to_dict('records')
            }
        
        return anomalies
    
    def generate_financial_insights(self) -> Dict:
        """Generate comprehensive financial insights"""
        inventory_analysis = self.analyze_inventory_financials()
        walmart_analysis = self.analyze_walmart_sales()
        anomalies = self.detect_anomalies()
        
        insights = {
            'inventory_insights': inventory_analysis,
            'sales_insights': walmart_analysis,
            'anomalies': anomalies,
            'recommendations': self._generate_recommendations(inventory_analysis, walmart_analysis, anomalies),
            'generated_at': datetime.now().isoformat()
        }
        
        return insights
    
    def _generate_recommendations(self, inventory: Dict, sales: Dict, anomalies: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Inventory recommendations
        if inventory.get('profit_margin', 0) < 10:
            recommendations.append("⚠️ Low profit margin detected. Consider reviewing pricing strategy or reducing costs.")
        
        if anomalies.get('inventory', {}).get('low_stock', {}).get('count', 0) > 0:
            recommendations.append(f"📦 {anomalies['inventory']['low_stock']['count']} products have low inventory levels. Consider restocking.")
        
        if anomalies.get('inventory', {}).get('high_demand_risk', {}).get('count', 0) > 0:
            recommendations.append(f"🔥 {anomalies['inventory']['high_demand_risk']['count']} products show high demand risk. Increase inventory to avoid stockouts.")
        
        # Sales recommendations
        if sales.get('holiday_impact', {}).get('holiday_lift', 0) > 20:
            recommendations.append("🎉 Strong holiday performance detected. Consider increasing inventory during holiday periods.")
        
        if sales.get('correlations', {}).get('temperature_sales', 0) > 0.3:
            recommendations.append("🌡️ Temperature correlates with sales. Plan inventory based on seasonal weather patterns.")
        
        # Financial recommendations
        if inventory.get('inventory_turnover', 0) < 2:
            recommendations.append("💰 Low inventory turnover. Review slow-moving products and consider promotions.")
        
        return recommendations


if __name__ == "__main__":
    analyzer = CSVDataAnalyzer(
        'retail_store_inventory.csv',
        'Walmart.csv'
    )
    
    if analyzer.load_data():
        insights = analyzer.generate_financial_insights()
        
        # Save to JSON
        with open('analytics/financial_insights.json', 'w') as f:
            json.dump(insights, f, indent=2, default=str)
        
        print("\n📊 Financial Insights Generated!")
        print(f"   Total Revenue: ${insights['inventory_insights']['total_revenue']:,.2f}")
        print(f"   Total Profit: ${insights['inventory_insights']['total_profit']:,.2f}")
        print(f"   Profit Margin: {insights['inventory_insights']['profit_margin']:.2f}%")
        print(f"\n💡 Recommendations:")
        for rec in insights['recommendations']:
            print(f"   {rec}")


