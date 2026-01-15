"""
Trade barrier analyzer model
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle
import logging

logger = logging.getLogger(__name__)


class TradeBarrierAnalyzer:
    """
    Analyzes trade barriers and predicts impact
    """
    
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_columns = [
            'destination_country', 'product_category', 'trade_volume',
            'historical_growth', 'political_risk', 'regulatory_complexity'
        ]
        
    def train(self, historical_data: pd.DataFrame):
        """
        Train model on historical trade barrier data
        
        Args:
            historical_data: DataFrame with historical trade barrier impacts
        """
        logger.info("Training trade barrier analyzer model")
        
        # Prepare features
        X = self._prepare_features(historical_data)
        y = historical_data['cost_impact'].values
        
        # Train model
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        
        logger.info(f"Model trained with {len(X)} samples")
        
    def predict_impact(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict trade barrier impact for a route
        
        Args:
            route_data: Route data including destination, product, etc.
            
        Returns:
            Predicted impact analysis
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Prepare input features
        features = self._prepare_single_sample(route_data)
        
        # Make prediction
        predicted_impact = self.model.predict([features])[0]
        
        # Calculate confidence interval (simplified)
        confidence = 0.85  # Placeholder for actual confidence calculation
        
        # Generate recommendations
        recommendations = self._generate_recommendations(route_data, predicted_impact)
        
        return {
            "predicted_cost_impact_percent": round(predicted_impact, 2),
            "confidence": round(confidence, 2),
            "risk_level": self._determine_risk_level(predicted_impact),
            "recommendations": recommendations,
            "alternative_strategies": self._suggest_alternative_strategies(route_data)
        }
    
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for model training/prediction"""
        X = data[self.feature_columns].copy()
        
        # Encode categorical variables
        for col in ['destination_country', 'product_category']:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col])
            else:
                X[col] = self.label_encoders[col].transform(X[col])
        
        return X
    
    def _prepare_single_sample(self, route_data: Dict[str, Any]) -> List[float]:
        """Prepare single sample for prediction"""
        features = []
        
        # Encode destination country
        if 'destination_country' in self.label_encoders:
            try:
                country_encoded = self.label_encoders['destination_country'].transform(
                    [route_data.get('destination_country', 'unknown')]
                )[0]
            except:
                country_encoded = 0  # Default for unseen
        else:
            country_encoded = 0
        
        # Encode product category
        if 'product_category' in self.label_encoders:
            try:
                product_encoded = self.label_encoders['product_category'].transform(
                    [route_data.get('product_category', 'general')]
                )[0]
            except:
                product_encoded = 0
        else:
            product_encoded = 0
        
        # Get numerical features
        trade_volume = route_data.get('trade_volume', 1000000)
        historical_growth = route_data.get('historical_growth', 0.0)
        political_risk = route_data.get('political_risk', 0.5)
        regulatory_complexity = route_data.get('regulatory_complexity', 0.5)
        
        return [
            country_encoded, product_encoded, trade_volume,
            historical_growth, political_risk, regulatory_complexity
        ]
    
    def _determine_risk_level(self, impact: float) -> str:
        """Determine risk level based on predicted impact"""
        if impact < 5:
            return "low"
        elif impact < 15:
            return "medium"
        elif impact < 30:
            return "high"
        else:
            return "critical"
    
    def _generate_recommendations(self, route_data: Dict[str, Any], impact: float) -> List[str]:
        """Generate recommendations based on predicted impact"""
        recommendations = []
        
        destination = route_data.get('destination_country', '')
        product = route_data.get('product_category', '')
        
        if impact > 20:
            recommendations.append("Consider alternative markets with lower barriers")
            recommendations.append("Explore digital export channels to bypass physical barriers")
        
        if destination in ['US', 'EU']:
            recommendations.append("Ensure full regulatory compliance documentation")
            recommendations.append("Consider local partnership or joint venture")
        
        if product in ['electronics', 'technology']:
            recommendations.append("Verify export control and licensing requirements")
            recommendations.append("Consider component-level export vs finished product")
        
        if impact > 10:
            recommendations.append("Apply for trade barrier mitigation support programs")
            recommendations.append("Diversify export destinations to reduce risk")
        
        return recommendations
    
    def _suggest_alternative_strategies(self, route_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest alternative trade strategies"""
        strategies = []
        
        destination = route_data.get('destination_country', '')
        product = route_data.get('product_category', '')
        
        # Strategy 1: Alternative destinations
        alternative_destinations = {
            'US': ['Canada', 'Mexico', 'Vietnam', 'Thailand'],
            'EU': ['UK', 'Turkey', 'Switzerland', 'Norway'],
            'general': ['ASEAN', 'Middle East', 'Africa', 'Latin America']
        }
        
        for key, alts in alternative_destinations.items():
            if key == destination or (key == 'general' and destination not in alternative_destinations):
                for alt in alts[:2]:  # Suggest top 2 alternatives
                    strategies.append({
                        "type": "alternative_destination",
                        "destination": alt,
                        "rationale": f"Lower trade barriers compared to {destination}",
                        "estimated_savings_percent": np.random.uniform(5, 25)
                    })
        
        # Strategy 2: Product modification
        if product in ['electronics', 'machinery']:
            strategies.append({
                "type": "product_modification",
                "description": "Modify product to meet destination standards",
                "rationale": "Compliance with technical standards reduces barriers",
                "estimated_savings_percent": np.random.uniform(10, 30)
            })
        
        # Strategy 3: Digital transformation
        if product in ['software', 'services', 'consulting']:
            strategies.append({
                "type": "digital_export",
                "description": "Convert to digital delivery format",
                "rationale": "Digital exports face fewer physical barriers",
                "estimated_savings_percent": np.random.uniform(20, 40)
            })
        
        return strategies
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'label_encoders': self.label_encoders,
                'feature_columns': self.feature_columns
            }, f)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.label_encoders = data['label_encoders']
        self.feature_columns = data['feature_columns']
        
        logger.info(f"Model loaded from {filepath}")
    
    def generate_training_data(self) -> pd.DataFrame:
        """
        Generate synthetic training data for demonstration
        
        Returns:
            DataFrame with synthetic trade barrier data
        """
        countries = ['US', 'EU', 'JP', 'KR', 'VN', 'IN', 'AU', 'CA', 'MX', 'BR']
        products = ['electronics', 'machinery', 'textiles', 'chemicals', 'agricultural', 'vehicles']
        
        data = []
        np.random.seed(42)
        
        for _ in range(1000):
            country = np.random.choice(countries)
            product = np.random.choice(products)
            
            # Base impact based on country and product
            base_impact = 10.0
            
            # Adjust for country
            if country == 'US':
                base_impact += np.random.uniform(5, 20)
            elif country == 'EU':
                base_impact += np.random.uniform(3, 15)
            elif country in ['VN', 'MX']:
                base_impact -= np.random.uniform(2, 8)
            
            # Adjust for product
            if product in ['electronics', 'vehicles']:
                base_impact += np.random.uniform(5, 15)
            elif product in ['textiles', 'agricultural']:
                base_impact -= np.random.uniform(2, 10)
            
            # Add random variation
            impact = max(0, base_impact + np.random.normal(0, 5))
            
            data.append({
                'destination_country': country,
                'product_category': product,
                'trade_volume': np.random.uniform(100000, 10000000),
                'historical_growth': np.random.uniform(-10, 20),
                'political_risk': np.random.uniform(0, 1),
                'regulatory_complexity': np.random.uniform(0, 1),
                'cost_impact': impact
            })
        
        return pd.DataFrame(data)
