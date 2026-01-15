"""
Property market analyzer model
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')
import logging

logger = logging.getLogger(__name__)


class PropertyMarketAnalyzer:
    """
    Analyzes property market stability and identifies risks
    """
    
    def __init__(self):
        self.anomaly_detector = None
        self.risk_classifier = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'price_index', 'volume_index', 'vacancy_rate', 'rental_yield',
            'debt_to_value', 'affordability_index', 'price_to_income'
        ]
        
    def analyze_market_stability(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze property market stability
        
        Args:
            market_data: DataFrame with market metrics over time
            
        Returns:
            Stability analysis with risk indicators
        """
        logger.info("Analyzing property market stability")
        
        if len(market_data) < 6:
            return {"error": "Insufficient data for analysis"}
        
        # Calculate trends
        trends = self._calculate_trends(market_data)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(market_data)
        
        # Calculate risk scores
        risk_scores = self._calculate_risk_scores(market_data, trends)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(market_data, trends, risk_scores)
        
        return {
            "analysis_period": {
                "start": market_data['period'].min(),
                "end": market_data['period'].max(),
                "data_points": len(market_data)
            },
            "current_state": self._summarize_current_state(market_data),
            "trends": trends,
            "anomalies": anomalies,
            "risk_assessment": risk_scores,
            "stability_score": self._calculate_stability_score(risk_scores),
            "recommendations": recommendations,
            "early_warnings": self._generate_early_warnings(market_data, trends)
        }
    
    def _calculate_trends(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trends for key indicators"""
        # Sort by period
        data_sorted = market_data.sort_values('period')
        
        # Calculate slope for last 6 periods
        recent_data = data_sorted.tail(6)
        
        trends = {}
        for col in ['price_index', 'volume_index', 'vacancy_rate', 'affordability_index']:
            if col in recent_data.columns:
                values = recent_data[col].values
                if len(values) >= 2:
                    # Simple linear trend
                    x = np.arange(len(values))
                    slope = np.polyfit(x, values, 1)[0]
                    trends[f'{col}_trend'] = {
                        "slope": round(slope, 3),
                        "direction": "increasing" if slope > 0 else "decreasing",
                        "strength": abs(slope) / np.std(values) if np.std(values) > 0 else 0
                    }
        
        # Calculate momentum
        if len(data_sorted) >= 3:
            latest = data_sorted.iloc[-1]
            previous = data_sorted.iloc[-2]
            older = data_sorted.iloc[-3]
            
            price_momentum = latest['price_index'] - 2*previous['price_index'] + older['price_index']
            volume_momentum = latest['volume_index'] - 2*previous['volume_index'] + older['volume_index']
            
            trends['price_momentum'] = price_momentum
            trends['volume_momentum'] = volume_momentum
        
        return trends
    
    def _detect_anomalies(self, market_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalous periods in market data"""
        anomalies = []
        
        if len(market_data) < 10:
            return anomalies
        
        # Prepare features for anomaly detection
        features = market_data[self.feature_columns].copy()
        
        # Handle missing values
        features = features.fillna(features.mean())
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train anomaly detector
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = self.anomaly_detector.fit_predict(features_scaled)
        
        # Identify anomalies
        anomaly_indices = np.where(anomaly_labels == -1)[0]
        
        for idx in anomaly_indices:
            if idx < len(market_data):
                period = market_data.iloc[idx]['period']
                anomaly_data = {
                    "period": period,
                    "indicators": {},
                    "severity": "medium"
                }
                
                # Identify which indicators are anomalous
                for col in self.feature_columns:
                    if col in market_data.columns:
                        value = market_data.iloc[idx][col]
                        mean = market_data[col].mean()
                        std = market_data[col].std()
                        
                        if std > 0 and abs(value - mean) > 2 * std:
                            anomaly_data["indicators"][col] = {
                                "value": value,
                                "deviation_sigma": round((value - mean) / std, 2)
                            }
                
                # Determine severity
                if len(anomaly_data["indicators"]) >= 3:
                    anomaly_data["severity"] = "high"
                elif len(anomaly_data["indicators"]) == 0:
                    anomaly_data["severity"] = "low"
                
                anomalies.append(anomaly_data)
        
        return anomalies
    
    def _calculate_risk_scores(self, market_data: pd.DataFrame, trends: Dict[str, Any]) -> Dict[str, float]:
        """Calculate risk scores for various factors"""
        latest = market_data.iloc[-1]
        
        risk_scores = {}
        
        # Price bubble risk
        if 'price_index' in latest:
            price_trend = trends.get('price_index_trend', {}).get('slope', 0)
            price_level = latest['price_index']
            
            # Simple bubble indicator: rapid price increase + high price level
            price_risk = min(1.0, (abs(price_trend) * 10 + price_level / 200) / 2)
            risk_scores['price_bubble'] = round(price_risk, 2)
        
        # Vacancy risk
        if 'vacancy_rate' in latest:
            vacancy_risk = min(1.0, latest['vacancy_rate'] / 30)  # 30% vacancy = max risk
            risk_scores['vacancy'] = round(vacancy_risk, 2)
        
        # Debt risk
        if 'debt_to_value' in latest:
            debt_risk = min(1.0, latest['debt_to_value'] / 100)  # 100% DTV = max risk
            risk_scores['debt'] = round(debt_risk, 2)
        
        # Affordability risk
        if 'affordability_index' in latest:
            affordability_risk = min(1.0, (100 - latest['affordability_index']) / 100)
            risk_scores['affordability'] = round(affordability_risk, 2)
        
        # Liquidity risk (from volume)
        if 'volume_index' in latest:
            volume_trend = trends.get('volume_index_trend', {}).get('slope', 0)
            liquidity_risk = min(1.0, (70 - latest['volume_index']) / 70 + abs(volume_trend) * 5)
            risk_scores['liquidity'] = round(liquidity_risk, 2)
        
        # Overall market risk (weighted average)
        if risk_scores:
            weights = {
                'price_bubble': 0.3,
                'vacancy': 0.2,
                'debt': 0.2,
                'affordability': 0.2,
                'liquidity': 0.1
            }
            
            overall_risk = sum(risk_scores.get(key, 0) * weights.get(key, 0) 
                              for key in weights)
            risk_scores['overall'] = round(overall_risk, 2)
        
        return risk_scores
    
    def _generate_recommendations(self, market_data: pd.DataFrame, 
                                 trends: Dict[str, Any], 
                                 risk_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        latest = market_data.iloc[-1]
        
        # Price bubble recommendations
        if risk_scores.get('price_bubble', 0) > 0.7:
            recommendations.append("Implement price stabilization measures")
            recommendations.append("Increase affordable housing supply")
        
        if risk_scores.get('price_bubble', 0) > 0.5:
            recommendations.append("Monitor speculative investment activity")
            recommendations.append("Consider temporary transaction taxes")
        
        # Vacancy recommendations
        if risk_scores.get('vacancy', 0) > 0.6:
            recommendations.append("Incentivize commercial space conversion")
            recommendations.append("Promote mixed-use development")
        
        if risk_scores.get('vacancy', 0) > 0.4:
            recommendations.append("Review zoning regulations")
            recommendations.append("Support property management improvements")
        
        # Debt recommendations
        if risk_scores.get('debt', 0) > 0.7:
            recommendations.append("Implement debt restructuring programs")
            recommendations.append("Strengthen lending standards")
        
        if risk_scores.get('debt', 0) > 0.5:
            recommendations.append("Provide financial counseling services")
            recommendations.append("Monitor household debt levels")
        
        # Affordability recommendations
        if risk_scores.get('affordability', 0) > 0.6:
            recommendations.append("Expand affordable housing programs")
            recommendations.append("Provide rental assistance")
        
        if risk_scores.get('affordability', 0) > 0.4:
            recommendations.append("Promote income-based housing")
            recommendations.append("Review property tax policies")
        
        # If overall risk is high
        if risk_scores.get('overall', 0) > 0.6:
            recommendations.append("Develop comprehensive market intervention plan")
            recommendations.append("Establish early warning system")
            recommendations.append("Coordinate with financial regulators")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _summarize_current_state(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Summarize current market state"""
        if len(market_data) == 0:
            return {}
        
        latest = market_data.iloc[-1]
        summary = {}
        
        metrics = ['price_index', 'volume_index', 'vacancy_rate', 
                  'rental_yield', 'debt_to_value', 'affordability_index']
        
        for metric in metrics:
            if metric in latest:
                summary[metric] = {
                    "value": latest[metric],
                    "unit": self._get_metric_unit(metric)
                }
        
        return summary
    
    def _calculate_stability_score(self, risk_scores: Dict[str, float]) -> float:
        """Calculate overall stability score (0-100)"""
        overall_risk = risk_scores.get('overall', 0.5)
        stability = 100 * (1 - overall_risk)
        return round(stability, 1)
    
    def _generate_early_warnings(self, market_data: pd.DataFrame, 
                                trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate early warning signals"""
        warnings = []
        
        if len(market_data) < 6:
            return warnings
        
        # Rapid price increase warning
        price_trend = trends.get('price_index_trend', {})
        if price_trend.get('slope', 0) > 2.0:  # Rapid increase
            warnings.append({
                "type": "price_acceleration",
                "severity": "high",
                "message": "Rapid price acceleration detected",
                "suggested_action": "Monitor for speculative activity"
            })
        
        # Volume decline warning
        volume_trend = trends.get('volume_index_trend', {})
        if volume_trend.get('slope', 0) < -1.0:  # Rapid decline
            warnings.append({
                "type": "liquidity_decline",
                "severity": "medium",
                "message": "Transaction volume declining rapidly",
                "suggested_action": "Investigate market liquidity"
            })
        
        # Vacancy increase warning
        latest = market_data.iloc[-1]
        if 'vacancy_rate' in latest and latest['vacancy_rate'] > 15:
            avg_vacancy = market_data['vacancy_rate'].mean()
            if latest['vacancy_rate'] > avg_vacancy * 1.5:
                warnings.append({
                    "type": "high_vacancy",
                    "severity": "medium",
                    "message": "Vacancy rate significantly above historical average",
                    "suggested_action": "Review supply-demand balance"
                })
        
        # Debt level warning
        if 'debt_to_value' in latest and latest['debt_to_value'] > 70:
            warnings.append({
                "type": "high_leverage",
                "severity": "high",
                "message": "High debt-to-value ratio detected",
                "suggested_action": "Monitor financial stability risks"
            })
        
        return warnings
    
    def _get_metric_unit(self, metric: str) -> str:
        """Get unit for metric"""
        units = {
            'price_index': 'index (base=100)',
            'volume_index': 'index (base=100)',
            'vacancy_rate': 'percent',
            'rental_yield': 'percent',
            'debt_to_value': 'percent',
            'affordability_index': 'index (0-100)'
        }
        return units.get(metric, '')
    
    def analyze_debt_restructuring(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze debt restructuring options for a property
        
        Args:
            property_data: Property and debt information
            
        Returns:
            Debt restructuring analysis
        """
        logger.info("Analyzing debt restructuring options")
        
        current_debt = property_data.get('current_debt_amount', 0)
        property_value = property_data.get('property_value', 0)
        monthly_income = property_data.get('monthly_income', 0)
        monthly_expenses = property_data.get('monthly_expenses', 0)
        credit_score = property_data.get('credit_score', 650)
        
        # Calculate key ratios
        ltv = current_debt / property_value if property_value > 0 else 1.0
        dti = current_debt / (monthly_income * 12) if monthly_income > 0 else float('inf')
        net_cash_flow = monthly_income - monthly_expenses
        
        # Determine restructuring options
        options = []
        
        # Option 1: Term extension
        if ltv < 0.8 and credit_score > 600:
            options.append({
                "type": "term_extension",
                "description": "Extend loan term to reduce monthly payments",
                "current_payment": self._estimate_monthly_payment(current_debt, 0.05, 20),
                "proposed_payment": self._estimate_monthly_payment(current_debt, 0.05, 30),
                "reduction_percent": 20,
                "eligibility": "high",
                "requirements": ["credit_score > 600", "ltv < 80%"]
            })
        
        # Option 2: Interest rate reduction
        if credit_score > 700:
            options.append({
                "type": "rate_reduction",
                "description": "Negotiate lower interest rate",
                "current_rate": 0.05,
                "proposed_rate": 0.04,
                "reduction_percent": 15,
                "eligibility": "medium",
                "requirements": ["credit_score > 700", "payment_history"]
            })
        
        # Option 3: Principal reduction
        if ltv > 0.9 and net_cash_flow < 0:
            options.append({
                "type": "principal_reduction",
                "description": "Negotiate principal reduction",
                "current_principal": current_debt,
                "proposed_principal": current_debt * 0.8,
                "reduction_percent": 20,
                "eligibility": "low",
                "requirements": ["financial_hardship", "ltv > 90%"]
            })
        
        # Option 4: Refinancing
        if credit_score > 650 and property_value > current_debt * 1.2:
            options.append({
                "type": "refinancing",
                "description": "Refinance with new lender",
                "current_rate": 0.05,
                "proposed_rate": 0.045,
                "reduction_percent": 10,
                "eligibility": "medium",
                "requirements": ["credit_score > 650", "property_value > 120% debt"]
            })
        
        # Generate recommendation
        best_option = None
        if options:
            # Simple heuristic: choose option with highest reduction
            best_option = max(options, key=lambda x: x.get('reduction_percent', 0))
        
        return {
            "property_analysis": {
                "loan_to_value_ratio": round(ltv * 100, 1),
                "debt_to_income_ratio": round(dti, 1),
                "net_cash_flow": net_cash_flow,
                "credit_score_tier": self._get_credit_tier(credit_score)
            },
            "restructuring_options": options,
            "recommended_option": best_option,
            "next_steps": [
                "Gather financial documentation",
                "Contact lender for negotiations",
                "Consider professional debt counseling"
            ]
        }
    
    def _estimate_monthly_payment(self, principal: float, rate:
