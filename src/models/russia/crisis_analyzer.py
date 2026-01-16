"""
Russian Economic Crisis Analyzer
ML-based analysis of economic crisis factors and recovery scenarios
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class RussianCrisisAnalyzer:
    """
    ML model for analyzing Russian economic crisis severity and predicting outcomes
    Uses ensemble methods to assess crisis severity and recovery prospects
    """

    def __init__(self):
        self.severity_model = None
        self.recovery_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize and train models with historical/simulated data"""
        logger.info("Initializing Russian crisis analysis models...")

        # Generate training data based on historical patterns
        X_train, y_severity, y_recovery = self._generate_training_data()

        # Scale features
        X_scaled = self.scaler.fit_transform(X_train)

        # Train severity prediction model (regression: 0-100 severity score)
        self.severity_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.severity_model.fit(X_scaled, y_severity)

        # Train recovery classification model
        self.recovery_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        self.recovery_model.fit(X_scaled, y_recovery)

        logger.info("Crisis analysis models trained successfully")

    def _generate_training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate training data based on Russian economic patterns"""
        np.random.seed(42)
        n_samples = 500

        # Features representing economic indicators
        # [inflation, budget_deficit%, oil_price, ruble_rate, brain_drain_k,
        #  cb_rate, sanctions_intensity, war_spending%, capacity_util, labor_shortage%]

        # Generate realistic feature distributions
        inflation = np.random.uniform(5, 35, n_samples)  # 5-35%
        budget_deficit = np.random.uniform(-2, 8, n_samples)  # -2 to 8% of GDP
        oil_price = np.random.uniform(40, 120, n_samples)  # $/barrel
        ruble_rate = np.random.uniform(60, 150, n_samples)  # RUB/USD
        brain_drain = np.random.uniform(0, 1000, n_samples)  # thousands emigrated
        cb_rate = np.random.uniform(5, 25, n_samples)  # central bank rate %
        sanctions = np.random.uniform(0, 1, n_samples)  # 0-1 intensity
        war_spending = np.random.uniform(0, 10, n_samples)  # % of GDP
        capacity_util = np.random.uniform(60, 98, n_samples)  # %
        labor_shortage = np.random.uniform(0, 5, n_samples)  # millions

        X = np.column_stack([
            inflation, budget_deficit, oil_price, ruble_rate, brain_drain,
            cb_rate, sanctions, war_spending, capacity_util, labor_shortage
        ])

        # Calculate severity score (0-100) based on realistic relationships
        severity = (
            0.2 * np.clip(inflation / 35 * 100, 0, 100) +
            0.15 * np.clip(budget_deficit / 8 * 100, 0, 100) +
            0.1 * np.clip((120 - oil_price) / 80 * 100, 0, 100) +
            0.1 * np.clip((ruble_rate - 60) / 90 * 100, 0, 100) +
            0.1 * np.clip(brain_drain / 1000 * 100, 0, 100) +
            0.1 * np.clip(cb_rate / 25 * 100, 0, 100) +
            0.1 * np.clip(sanctions * 100, 0, 100) +
            0.05 * np.clip(war_spending / 10 * 100, 0, 100) +
            0.05 * np.clip((capacity_util - 60) / 38 * 100, 0, 100) +
            0.05 * np.clip(labor_shortage / 5 * 100, 0, 100)
        )

        # Add noise
        severity = np.clip(severity + np.random.normal(0, 5, n_samples), 0, 100)

        # Recovery classification based on severity and structural factors
        # 0: Likely recovery, 1: Difficult recovery, 2: Very difficult, 3: Crisis deepening
        recovery_score = (
            severity * 0.5 +
            sanctions * 30 +
            war_spending * 3 +
            brain_drain / 20
        )
        recovery = np.digitize(recovery_score, [30, 50, 70])

        return X, severity, recovery

    def analyze_current_crisis(
        self,
        inflation: float = 20.0,
        budget_deficit: float = 3.5,
        oil_price: float = 75.0,
        ruble_rate: float = 95.0,
        brain_drain_thousands: float = 750.0,
        cb_rate: float = 21.0,
        sanctions_intensity: float = 0.85,
        war_spending_pct: float = 8.0,
        capacity_utilization: float = 95.0,
        labor_shortage_millions: float = 2.5
    ) -> Dict[str, Any]:
        """
        Analyze current crisis state and predict outcomes

        Returns:
            Dict with severity score, risk level, recovery prospects, and recommendations
        """
        # Prepare features
        features = np.array([[
            inflation, budget_deficit, oil_price, ruble_rate, brain_drain_thousands,
            cb_rate, sanctions_intensity, war_spending_pct, capacity_utilization,
            labor_shortage_millions
        ]])

        features_scaled = self.scaler.transform(features)

        # Predict severity
        severity_score = float(self.severity_model.predict(features_scaled)[0])

        # Predict recovery class
        recovery_class = int(self.recovery_model.predict(features_scaled)[0])
        recovery_proba = self.recovery_model.predict_proba(features_scaled)[0]

        # Determine risk level
        if severity_score < 30:
            risk_level = "low"
        elif severity_score < 50:
            risk_level = "moderate"
        elif severity_score < 70:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Recovery interpretation
        recovery_labels = [
            "likely_with_reforms",
            "difficult_but_possible",
            "very_difficult",
            "crisis_deepening"
        ]

        # Feature importance for this prediction
        feature_names = [
            "inflation", "budget_deficit", "oil_price", "ruble_rate",
            "brain_drain", "cb_rate", "sanctions", "war_spending",
            "capacity_util", "labor_shortage"
        ]
        importances = dict(zip(feature_names, self.severity_model.feature_importances_))

        # Generate specific recommendations based on most impactful factors
        recommendations = self._generate_recommendations(features[0], importances)

        return {
            "severity_score": round(severity_score, 1),
            "risk_level": risk_level,
            "recovery_outlook": recovery_labels[recovery_class],
            "recovery_probabilities": {
                "likely_recovery": round(recovery_proba[0], 3),
                "difficult_recovery": round(recovery_proba[1], 3),
                "very_difficult": round(recovery_proba[2], 3),
                "crisis_deepening": round(recovery_proba[3], 3) if len(recovery_proba) > 3 else 0.0
            },
            "key_risk_factors": self._identify_key_risks(features[0], feature_names),
            "feature_importance": {k: round(v, 3) for k, v in sorted(importances.items(), key=lambda x: -x[1])},
            "recommendations": recommendations,
            "scenario_analysis": self._scenario_analysis(features[0])
        }

    def _identify_key_risks(self, features: np.ndarray, feature_names: List[str]) -> List[Dict[str, Any]]:
        """Identify the most critical risk factors"""
        thresholds = {
            "inflation": (15, 25, "high", "critical"),
            "budget_deficit": (3, 5, "concerning", "unsustainable"),
            "oil_price": (60, 50, "concerning", "critical"),  # lower is worse
            "ruble_rate": (90, 120, "weak", "crisis"),
            "brain_drain": (300, 600, "significant", "severe"),
            "cb_rate": (15, 20, "restrictive", "crisis_mode"),
            "sanctions": (0.5, 0.8, "significant", "severe"),
            "war_spending": (5, 8, "high", "unsustainable"),
            "capacity_util": (90, 95, "near_capacity", "overheating"),
            "labor_shortage": (1.5, 2.5, "significant", "critical")
        }

        risks = []
        for i, (name, value) in enumerate(zip(feature_names, features)):
            if name in thresholds:
                t1, t2, level1, level2 = thresholds[name]
                if name == "oil_price":  # Lower is worse
                    if value < t2:
                        risks.append({"factor": name, "value": value, "severity": level2})
                    elif value < t1:
                        risks.append({"factor": name, "value": value, "severity": level1})
                else:
                    if value > t2:
                        risks.append({"factor": name, "value": value, "severity": level2})
                    elif value > t1:
                        risks.append({"factor": name, "value": value, "severity": level1})

        return sorted(risks, key=lambda x: 1 if x["severity"] in ["critical", "severe", "unsustainable", "crisis", "crisis_mode", "overheating"] else 0, reverse=True)

    def _generate_recommendations(
        self, features: np.ndarray, importances: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        recommendations = []

        inflation, budget_deficit, oil_price, ruble_rate, brain_drain, cb_rate, sanctions, war_spending, capacity_util, labor_shortage = features

        if inflation > 15:
            recommendations.append({
                "priority": "immediate",
                "area": "monetary_policy",
                "action": "Inflation control through targeted measures rather than just rate hikes",
                "rationale": f"Inflation at {inflation}% is eroding purchasing power and destabilizing economy",
                "expected_impact": "Reduce real inflation to single digits"
            })

        if brain_drain > 500:
            recommendations.append({
                "priority": "immediate",
                "area": "talent_retention",
                "action": "Emergency talent retention program with mobilization exemptions",
                "rationale": f"Brain drain of {brain_drain}k is crippling innovation and productivity",
                "expected_impact": "Halt emigration, begin repatriation"
            })

        if war_spending > 6:
            recommendations.append({
                "priority": "medium_term",
                "area": "fiscal",
                "action": "Reduce non-essential defense spending, reallocate to civilian economy",
                "rationale": f"War spending at {war_spending}% of GDP is crowding out productive investment",
                "expected_impact": "Free up resources for economic development"
            })

        if cb_rate > 18:
            recommendations.append({
                "priority": "medium_term",
                "area": "monetary_policy",
                "action": "Coordinate gradual rate reduction with inflation control",
                "rationale": f"CB rate at {cb_rate}% is killing investment and mortgages",
                "expected_impact": "Revive investment and housing market"
            })

        if capacity_util > 92:
            recommendations.append({
                "priority": "short_term",
                "area": "industrial",
                "action": "Capacity expansion through investment and automation",
                "rationale": f"Capacity utilization at {capacity_util}% leaves no room for growth",
                "expected_impact": "Enable sustainable production growth"
            })

        if labor_shortage > 2:
            recommendations.append({
                "priority": "immediate",
                "area": "labor_market",
                "action": "Immigration facilitation and automation incentives",
                "rationale": f"Labor shortage of {labor_shortage}M workers is constraining output",
                "expected_impact": "Alleviate labor constraints, reduce wage pressure"
            })

        return recommendations

    def _scenario_analysis(self, current_features: np.ndarray) -> Dict[str, Any]:
        """Run scenario analysis for different policy paths"""
        scenarios = {}

        # Scenario 1: Status quo (no changes)
        scenarios["status_quo"] = self._predict_scenario(current_features, "No policy changes")

        # Scenario 2: Moderate reform
        moderate_reform = current_features.copy()
        moderate_reform[0] *= 0.8  # 20% inflation reduction
        moderate_reform[1] *= 0.8  # Budget improvement
        moderate_reform[4] *= 0.9  # Slight brain drain reduction
        scenarios["moderate_reform"] = self._predict_scenario(moderate_reform, "Moderate reforms implemented")

        # Scenario 3: Aggressive reform
        aggressive_reform = current_features.copy()
        aggressive_reform[0] *= 0.5  # 50% inflation reduction
        aggressive_reform[1] *= 0.5  # Significant budget improvement
        aggressive_reform[4] *= 0.7  # Brain drain reduction
        aggressive_reform[7] *= 0.7  # War spending reduction
        scenarios["aggressive_reform"] = self._predict_scenario(aggressive_reform, "Aggressive reforms + reduced war spending")

        # Scenario 4: Crisis deepening
        crisis_deepening = current_features.copy()
        crisis_deepening[0] *= 1.3  # Inflation worsens
        crisis_deepening[1] *= 1.3  # Deficit worsens
        crisis_deepening[4] *= 1.2  # More brain drain
        scenarios["crisis_deepening"] = self._predict_scenario(crisis_deepening, "Crisis deepens without intervention")

        return scenarios

    def _predict_scenario(self, features: np.ndarray, description: str) -> Dict[str, Any]:
        """Predict outcome for a given scenario"""
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        severity = float(self.severity_model.predict(features_scaled)[0])
        recovery_class = int(self.recovery_model.predict(features_scaled)[0])

        recovery_labels = ["likely_recovery", "difficult_recovery", "very_difficult", "crisis_deepening"]

        return {
            "description": description,
            "severity_score": round(severity, 1),
            "recovery_outlook": recovery_labels[min(recovery_class, 3)]
        }

    def compare_policy_interventions(
        self,
        base_features: np.ndarray,
        interventions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compare multiple policy intervention scenarios"""
        results = []

        for intervention in interventions:
            modified_features = base_features.copy()

            # Apply intervention effects
            for effect in intervention.get("effects", []):
                idx = effect["feature_index"]
                modifier = effect["modifier"]
                modified_features[idx] *= modifier

            features_scaled = self.scaler.transform(modified_features.reshape(1, -1))
            severity = float(self.severity_model.predict(features_scaled)[0])

            results.append({
                "intervention": intervention["name"],
                "severity_score": round(severity, 1),
                "improvement": round(self.severity_model.predict(self.scaler.transform(base_features.reshape(1, -1)))[0] - severity, 1)
            })

        return sorted(results, key=lambda x: x["improvement"], reverse=True)
