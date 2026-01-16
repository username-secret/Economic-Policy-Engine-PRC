"""
Russian Policy Impact Predictor
Predicts the impact of various policy interventions on economic outcomes
"""
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PolicyImpactPredictor:
    """
    Predicts the impact of policy interventions on Russian economic indicators
    Uses gradient boosting to model complex policy-outcome relationships
    """

    def __init__(self):
        self.gdp_model = None
        self.inflation_model = None
        self.investment_model = None
        self.scaler = StandardScaler()
        self._initialize_models()

    def _initialize_models(self):
        """Initialize prediction models"""
        logger.info("Initializing policy impact prediction models...")

        X_train, y_gdp, y_inflation, y_investment = self._generate_training_data()
        X_scaled = self.scaler.fit_transform(X_train)

        # GDP impact model
        self.gdp_model = GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.gdp_model.fit(X_scaled, y_gdp)

        # Inflation impact model
        self.inflation_model = GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.inflation_model.fit(X_scaled, y_inflation)

        # Investment impact model
        self.investment_model = GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
        self.investment_model.fit(X_scaled, y_investment)

        logger.info("Policy impact models trained successfully")

    def _generate_training_data(self):
        """Generate training data for policy impact prediction"""
        np.random.seed(42)
        n_samples = 500

        # Policy intervention features:
        # [fiscal_stimulus%, monetary_ease%, trade_openness, tech_investment%,
        #  labor_reform_intensity, sanctions_relief, war_spending_change%,
        #  brain_drain_reversal%, privatization_intensity, corruption_reduction]

        fiscal_stimulus = np.random.uniform(-5, 10, n_samples)
        monetary_ease = np.random.uniform(-10, 10, n_samples)
        trade_openness = np.random.uniform(0, 1, n_samples)
        tech_investment = np.random.uniform(0, 5, n_samples)
        labor_reform = np.random.uniform(0, 1, n_samples)
        sanctions_relief = np.random.uniform(0, 1, n_samples)
        war_spending_change = np.random.uniform(-5, 5, n_samples)
        brain_drain_reversal = np.random.uniform(0, 1, n_samples)
        privatization = np.random.uniform(0, 1, n_samples)
        corruption_reduction = np.random.uniform(0, 1, n_samples)

        X = np.column_stack([
            fiscal_stimulus, monetary_ease, trade_openness, tech_investment,
            labor_reform, sanctions_relief, war_spending_change,
            brain_drain_reversal, privatization, corruption_reduction
        ])

        # GDP impact (percentage points)
        y_gdp = (
            0.3 * fiscal_stimulus +
            0.2 * monetary_ease +
            1.5 * trade_openness +
            0.8 * tech_investment +
            0.5 * labor_reform +
            2.0 * sanctions_relief -
            0.3 * war_spending_change +
            0.7 * brain_drain_reversal +
            0.3 * privatization +
            1.0 * corruption_reduction +
            np.random.normal(0, 0.5, n_samples)
        )

        # Inflation impact (change in percentage points)
        y_inflation = (
            0.5 * fiscal_stimulus -
            0.3 * monetary_ease -
            0.5 * trade_openness +
            0.1 * tech_investment -
            0.2 * labor_reform -
            1.0 * sanctions_relief +
            0.8 * war_spending_change -
            0.1 * brain_drain_reversal -
            0.3 * privatization -
            0.5 * corruption_reduction +
            np.random.normal(0, 0.3, n_samples)
        )

        # Investment impact (percentage change)
        y_investment = (
            0.5 * fiscal_stimulus +
            1.5 * monetary_ease +
            2.0 * trade_openness +
            3.0 * tech_investment +
            1.0 * labor_reform +
            5.0 * sanctions_relief -
            2.0 * war_spending_change +
            2.0 * brain_drain_reversal +
            1.5 * privatization +
            3.0 * corruption_reduction +
            np.random.normal(0, 1.0, n_samples)
        )

        return X, y_gdp, y_inflation, y_investment

    def predict_policy_impact(
        self,
        fiscal_stimulus: float = 0.0,
        monetary_ease: float = 0.0,
        trade_openness: float = 0.3,
        tech_investment: float = 1.0,
        labor_reform: float = 0.2,
        sanctions_relief: float = 0.0,
        war_spending_change: float = 0.0,
        brain_drain_reversal: float = 0.1,
        privatization: float = 0.1,
        corruption_reduction: float = 0.1
    ) -> Dict[str, Any]:
        """
        Predict the impact of a policy package

        Args:
            fiscal_stimulus: Fiscal stimulus as % of GDP (-5 to 10)
            monetary_ease: Monetary policy ease (rate cuts, -10 to 10)
            trade_openness: Trade liberalization intensity (0-1)
            tech_investment: Tech investment as % of GDP (0-5)
            labor_reform: Labor market reform intensity (0-1)
            sanctions_relief: Expected sanctions relief (0-1)
            war_spending_change: Change in war spending % of GDP
            brain_drain_reversal: Success in reversing brain drain (0-1)
            privatization: Privatization intensity (0-1)
            corruption_reduction: Anti-corruption success (0-1)

        Returns:
            Dict with predicted impacts on GDP, inflation, investment
        """
        features = np.array([[
            fiscal_stimulus, monetary_ease, trade_openness, tech_investment,
            labor_reform, sanctions_relief, war_spending_change,
            brain_drain_reversal, privatization, corruption_reduction
        ]])

        features_scaled = self.scaler.transform(features)

        gdp_impact = float(self.gdp_model.predict(features_scaled)[0])
        inflation_impact = float(self.inflation_model.predict(features_scaled)[0])
        investment_impact = float(self.investment_model.predict(features_scaled)[0])

        return {
            "policy_package": {
                "fiscal_stimulus_pct": fiscal_stimulus,
                "monetary_ease": monetary_ease,
                "trade_openness": trade_openness,
                "tech_investment_pct": tech_investment,
                "labor_reform_intensity": labor_reform,
                "sanctions_relief_probability": sanctions_relief,
                "war_spending_change_pct": war_spending_change,
                "brain_drain_reversal": brain_drain_reversal,
                "privatization_intensity": privatization,
                "corruption_reduction": corruption_reduction
            },
            "predicted_impacts": {
                "gdp_growth_change_pp": round(gdp_impact, 2),
                "inflation_change_pp": round(inflation_impact, 2),
                "investment_change_pct": round(investment_impact, 2)
            },
            "interpretation": self._interpret_results(gdp_impact, inflation_impact, investment_impact),
            "confidence": self._calculate_confidence(features[0])
        }

    def _interpret_results(
        self, gdp_impact: float, inflation_impact: float, investment_impact: float
    ) -> Dict[str, str]:
        """Interpret prediction results"""
        interpretations = {}

        if gdp_impact > 2:
            interpretations["gdp"] = "strong_positive_growth_expected"
        elif gdp_impact > 0:
            interpretations["gdp"] = "moderate_growth_expected"
        elif gdp_impact > -1:
            interpretations["gdp"] = "stagnation_likely"
        else:
            interpretations["gdp"] = "contraction_risk"

        if inflation_impact < -2:
            interpretations["inflation"] = "significant_disinflation"
        elif inflation_impact < 0:
            interpretations["inflation"] = "mild_disinflation"
        elif inflation_impact < 2:
            interpretations["inflation"] = "stable_inflation"
        else:
            interpretations["inflation"] = "inflation_acceleration_risk"

        if investment_impact > 10:
            interpretations["investment"] = "investment_boom_potential"
        elif investment_impact > 0:
            interpretations["investment"] = "investment_recovery"
        else:
            interpretations["investment"] = "continued_investment_weakness"

        return interpretations

    def _calculate_confidence(self, features: np.ndarray) -> str:
        """Calculate confidence level based on feature values"""
        # More extreme values = lower confidence
        extremity = np.mean(np.abs(features - np.mean(features)) / (np.std(features) + 1e-6))

        if extremity < 1:
            return "high"
        elif extremity < 2:
            return "medium"
        else:
            return "low"

    def compare_reform_packages(self) -> List[Dict[str, Any]]:
        """Compare predefined reform packages"""
        packages = [
            {
                "name": "Status Quo",
                "params": {"fiscal_stimulus": 0, "monetary_ease": -5, "trade_openness": 0.2,
                          "tech_investment": 0.5, "sanctions_relief": 0, "war_spending_change": 2}
            },
            {
                "name": "Moderate Reform",
                "params": {"fiscal_stimulus": 2, "monetary_ease": 2, "trade_openness": 0.4,
                          "tech_investment": 2, "labor_reform": 0.4, "brain_drain_reversal": 0.3,
                          "corruption_reduction": 0.3}
            },
            {
                "name": "Aggressive Reform",
                "params": {"fiscal_stimulus": 3, "monetary_ease": 5, "trade_openness": 0.6,
                          "tech_investment": 3, "labor_reform": 0.6, "brain_drain_reversal": 0.5,
                          "privatization": 0.4, "corruption_reduction": 0.5}
            },
            {
                "name": "Peace Dividend",
                "params": {"fiscal_stimulus": 5, "monetary_ease": 5, "trade_openness": 0.7,
                          "tech_investment": 3, "sanctions_relief": 0.5, "war_spending_change": -5,
                          "brain_drain_reversal": 0.6, "corruption_reduction": 0.4}
            },
            {
                "name": "Full Normalization",
                "params": {"fiscal_stimulus": 3, "monetary_ease": 8, "trade_openness": 0.9,
                          "tech_investment": 4, "labor_reform": 0.7, "sanctions_relief": 0.9,
                          "war_spending_change": -6, "brain_drain_reversal": 0.8,
                          "privatization": 0.5, "corruption_reduction": 0.7}
            }
        ]

        results = []
        for pkg in packages:
            impact = self.predict_policy_impact(**pkg["params"])
            results.append({
                "package_name": pkg["name"],
                "gdp_impact": impact["predicted_impacts"]["gdp_growth_change_pp"],
                "inflation_impact": impact["predicted_impacts"]["inflation_change_pp"],
                "investment_impact": impact["predicted_impacts"]["investment_change_pct"],
                "overall_assessment": impact["interpretation"]
            })

        return sorted(results, key=lambda x: x["gdp_impact"], reverse=True)
