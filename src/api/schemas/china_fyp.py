"""
China's 15th Five-Year Plan (2026-2030) schemas and data structures
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FYPPriorityArea(str, Enum):
    """Key priority areas of the 15th Five-Year Plan"""
    INDUSTRIAL_MODERNIZATION = "industrial_modernization"
    TECH_SELF_RELIANCE = "tech_self_reliance"
    DOMESTIC_CONSUMPTION = "domestic_consumption"
    GREEN_DEVELOPMENT = "green_development"
    OPENING_UP = "opening_up"
    DIGITAL_CHINA = "digital_china"
    RURAL_REVITALIZATION = "rural_revitalization"
    SOCIAL_WELFARE = "social_welfare"


class EmergingIndustry(str, Enum):
    """Emerging and future industries prioritized in 15th FYP"""
    AEROSPACE = "aerospace"
    BIOMANUFACTURING = "biomanufacturing"
    HYDROGEN_ENERGY = "hydrogen_energy"
    NEW_MATERIALS = "new_materials"
    QUANTUM_TECHNOLOGY = "quantum_technology"
    AI_COMPUTING = "ai_computing"
    LOW_ALTITUDE_ECONOMY = "low_altitude_economy"
    DEEP_SEA_TECH = "deep_sea_technology"
    COMMERCIAL_SPACE = "commercial_space"


class TraditionalIndustryUpgrade(str, Enum):
    """Traditional industries targeted for upgrade"""
    MINING = "mining"
    CHEMICALS = "chemicals"
    MACHINERY = "machinery"
    STEEL = "steel"
    TEXTILES = "textiles"
    CONSTRUCTION = "construction"


class FYPStatus(str, Enum):
    """Implementation status"""
    PLANNING = "planning"
    EARLY_IMPLEMENTATION = "early_implementation"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    DELAYED = "delayed"
    COMPLETED = "completed"


class FYPTarget(BaseModel):
    """Individual target within the Five-Year Plan"""
    id: str = Field(..., description="Target identifier")
    name: str = Field(..., description="Target name")
    category: FYPPriorityArea = Field(..., description="Priority area category")
    baseline_value: float = Field(..., description="Baseline value (2025)")
    target_value: float = Field(..., description="Target value (2030)")
    current_value: Optional[float] = Field(None, description="Current progress value")
    unit: str = Field(..., description="Measurement unit")
    progress_percentage: float = Field(0.0, description="Progress towards target (%)")
    status: FYPStatus = Field(FYPStatus.PLANNING, description="Current status")
    key_initiatives: List[str] = Field(default_factory=list, description="Key implementation initiatives")

    class Config:
        schema_extra = {
            "example": {
                "id": "FYP15-TECH-001",
                "name": "R&D Expenditure as % of GDP",
                "category": "tech_self_reliance",
                "baseline_value": 2.64,
                "target_value": 3.0,
                "current_value": 2.64,
                "unit": "percent",
                "progress_percentage": 0.0,
                "status": "planning",
                "key_initiatives": [
                    "Increase government R&D funding",
                    "Incentivize private sector R&D",
                    "Establish national labs for key technologies"
                ]
            }
        }


class IndustrialModernizationPlan(BaseModel):
    """Industrial modernization component of 15th FYP"""
    emerging_industries: List[Dict[str, Any]] = Field(
        ..., description="Emerging industries to cultivate"
    )
    traditional_upgrades: List[Dict[str, Any]] = Field(
        ..., description="Traditional industries to upgrade"
    )
    key_technologies: List[str] = Field(
        ..., description="Core technologies to develop"
    )
    investment_target_trillion_rmb: float = Field(
        ..., description="Total investment target in trillion RMB"
    )
    job_creation_target: int = Field(
        ..., description="Expected new jobs in emerging industries"
    )


class TechSelfReliancePlan(BaseModel):
    """Technology self-reliance component of 15th FYP"""
    core_technology_breakthroughs: List[str] = Field(
        ..., description="Core technologies for breakthrough"
    )
    semiconductor_targets: Dict[str, Any] = Field(
        ..., description="Semiconductor self-sufficiency targets"
    )
    ai_development_goals: Dict[str, Any] = Field(
        ..., description="AI development goals"
    )
    talent_development: Dict[str, Any] = Field(
        ..., description="S&T talent development targets"
    )
    rd_investment_growth: float = Field(
        ..., description="Annual R&D investment growth rate target (%)"
    )


class DomesticConsumptionPlan(BaseModel):
    """Domestic consumption enhancement plan"""
    income_growth_targets: Dict[str, float] = Field(
        ..., description="Income growth targets by category"
    )
    social_welfare_improvements: List[str] = Field(
        ..., description="Social welfare improvement measures"
    )
    consumption_incentives: List[Dict[str, Any]] = Field(
        ..., description="Consumption stimulus measures"
    )
    services_sector_targets: Dict[str, Any] = Field(
        ..., description="Services sector development targets"
    )


class GreenDevelopmentPlan(BaseModel):
    """Green and sustainable development plan"""
    carbon_peak_measures: List[str] = Field(
        ..., description="Measures for carbon peak by 2030"
    )
    renewable_energy_targets: Dict[str, float] = Field(
        ..., description="Renewable energy capacity targets (GW)"
    )
    energy_efficiency_targets: Dict[str, float] = Field(
        ..., description="Energy efficiency improvement targets"
    )
    green_finance_development: Dict[str, Any] = Field(
        ..., description="Green finance development plans"
    )


class OpeningUpPlan(BaseModel):
    """Opening up and international cooperation plan"""
    fta_expansion: List[str] = Field(
        ..., description="Free trade agreements to pursue"
    )
    services_sector_opening: List[str] = Field(
        ..., description="Services sectors to open further"
    )
    digital_trade_measures: List[str] = Field(
        ..., description="Digital trade development measures"
    )
    bri_priorities: List[str] = Field(
        ..., description="Belt and Road Initiative priorities"
    )


class FifteenthFiveYearPlan(BaseModel):
    """Complete 15th Five-Year Plan (2026-2030) representation"""
    plan_id: str = Field("FYP-15-2026-2030", description="Plan identifier")
    name: str = Field(
        "The 15th Five-Year Plan for National Economic and Social Development",
        description="Official plan name"
    )
    period_start: int = Field(2026, description="Start year")
    period_end: int = Field(2030, description="End year")
    vision_2035_alignment: bool = Field(True, description="Aligned with 2035 vision")

    # Core targets
    gdp_growth_target: str = Field(
        "around 5%", description="Annual GDP growth target"
    )
    per_capita_gdp_target: str = Field(
        "approaching moderately developed country level by 2035",
        description="Per capita GDP vision"
    )

    # Priority areas
    priority_targets: List[FYPTarget] = Field(
        default_factory=list, description="Key quantitative targets"
    )

    # Sectoral plans
    industrial_modernization: Optional[IndustrialModernizationPlan] = Field(
        None, description="Industrial modernization plan"
    )
    tech_self_reliance: Optional[TechSelfReliancePlan] = Field(
        None, description="Technology self-reliance plan"
    )
    domestic_consumption: Optional[DomesticConsumptionPlan] = Field(
        None, description="Domestic consumption plan"
    )
    green_development: Optional[GreenDevelopmentPlan] = Field(
        None, description="Green development plan"
    )
    opening_up: Optional[OpeningUpPlan] = Field(
        None, description="Opening up plan"
    )

    # Implementation
    key_challenges: List[str] = Field(
        default_factory=list, description="Key challenges to address"
    )
    implementation_mechanisms: List[str] = Field(
        default_factory=list, description="Implementation mechanisms"
    )

    # Metadata
    adoption_date: str = Field("2025-10-23", description="CPC plenary adoption date")
    formal_release_date: str = Field("2026-03", description="Expected formal release")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    class Config:
        schema_extra = {
            "example": {
                "plan_id": "FYP-15-2026-2030",
                "name": "The 15th Five-Year Plan",
                "period_start": 2026,
                "period_end": 2030,
                "gdp_growth_target": "around 5%",
                "priority_targets": [
                    {
                        "id": "FYP15-TECH-001",
                        "name": "R&D as % of GDP",
                        "target_value": 3.0
                    }
                ],
                "key_challenges": [
                    "US-China trade tensions",
                    "Property market stabilization",
                    "Deflationary pressures"
                ]
            }
        }


class FYPProgressReport(BaseModel):
    """Progress report for Five-Year Plan implementation"""
    report_id: str = Field(..., description="Report identifier")
    reporting_period: str = Field(..., description="Reporting period (YYYY-MM)")
    overall_progress: float = Field(..., description="Overall progress percentage")
    targets_on_track: int = Field(..., description="Number of targets on track")
    targets_delayed: int = Field(..., description="Number of delayed targets")
    targets_ahead: int = Field(..., description="Number of targets ahead of schedule")
    key_achievements: List[str] = Field(..., description="Key achievements")
    emerging_challenges: List[str] = Field(..., description="Emerging challenges")
    policy_adjustments: List[str] = Field(..., description="Policy adjustments made")
    next_period_priorities: List[str] = Field(..., description="Priorities for next period")


class FYPPolicyRecommendation(BaseModel):
    """Policy recommendation for FYP implementation"""
    recommendation_id: str = Field(..., description="Recommendation ID")
    target_area: FYPPriorityArea = Field(..., description="Target priority area")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    expected_impact: str = Field(..., description="Expected impact")
    implementation_complexity: str = Field(..., description="low/medium/high")
    resource_requirements: Dict[str, Any] = Field(..., description="Required resources")
    timeline_months: int = Field(..., description="Implementation timeline")
    success_metrics: List[str] = Field(..., description="Success metrics")
