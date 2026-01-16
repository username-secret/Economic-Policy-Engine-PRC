"""
Russian Federation economic policy schemas - National Projects, S&T Programs, and Crisis Analysis
Covers Putin-era economic programs and their challenges with proposed solutions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class NationalProjectCategory(str, Enum):
    """Categories of Russian National Projects"""
    HUMAN_CAPITAL = "human_capital"
    COMFORTABLE_LIVING = "comfortable_living"
    ECONOMIC_GROWTH = "economic_growth"
    INFRASTRUCTURE = "infrastructure"
    DIGITAL_ECONOMY = "digital_economy"
    DEFENSE_SECURITY = "defense_security"


class ProjectStatus(str, Enum):
    """Status of national projects"""
    ON_TRACK = "on_track"
    DELAYED = "delayed"
    SEVERELY_DELAYED = "severely_delayed"
    UNDERFUNDED = "underfunded"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EconomicCrisisType(str, Enum):
    """Types of economic crisis factors"""
    INFLATION = "inflation"
    BUDGET_DEFICIT = "budget_deficit"
    SANCTIONS_IMPACT = "sanctions_impact"
    LABOR_SHORTAGE = "labor_shortage"
    CAPITAL_FLIGHT = "capital_flight"
    BRAIN_DRAIN = "brain_drain"
    CURRENCY_DEPRECIATION = "currency_depreciation"
    ENERGY_REVENUE_DECLINE = "energy_revenue_decline"
    INVESTMENT_CRISIS = "investment_crisis"
    PRODUCTION_CAPACITY = "production_capacity_exhaustion"


class STSectorType(str, Enum):
    """Science and Technology sectors"""
    SPACE_PROGRAM = "space_program"
    NUCLEAR_TECH = "nuclear_technology"
    HYPERSONICS = "hypersonics"
    AI_COMPUTING = "ai_computing"
    SEMICONDUCTORS = "semiconductors"
    QUANTUM_TECH = "quantum_technology"
    BIOTECH = "biotechnology"
    MATERIALS_SCIENCE = "materials_science"
    ROBOTICS = "robotics"
    AVIATION = "aviation"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class SolutionPriority(str, Enum):
    """Solution implementation priority"""
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


# ==================== NATIONAL PROJECTS ====================

class NationalProject(BaseModel):
    """Russian National Project (2018-2030)"""
    project_id: str = Field(..., description="Project identifier")
    name: str = Field(..., description="Project name")
    name_ru: str = Field(..., description="Project name in Russian")
    category: NationalProjectCategory = Field(..., description="Project category")
    description: str = Field(..., description="Project description")

    # Funding
    total_budget_trillion_rub: float = Field(..., description="Total budget in trillion rubles")
    spent_to_date_trillion_rub: float = Field(0.0, description="Amount spent to date")
    federal_share_percent: float = Field(..., description="Federal budget share")
    regional_share_percent: float = Field(0.0, description="Regional budget share")
    private_share_percent: float = Field(0.0, description="Private investment share")

    # Timeline
    start_year: int = Field(..., description="Start year")
    original_end_year: int = Field(..., description="Originally planned end year")
    revised_end_year: Optional[int] = Field(None, description="Revised end year if delayed")

    # Status
    status: ProjectStatus = Field(..., description="Current status")
    completion_percentage: float = Field(0.0, description="Completion percentage")

    # Key targets
    key_targets: List[Dict[str, Any]] = Field(..., description="Key targets and metrics")
    achievements: List[str] = Field(default_factory=list, description="Achievements to date")

    # Problems and challenges
    challenges: List[str] = Field(default_factory=list, description="Current challenges")
    blocking_issues: List[str] = Field(default_factory=list, description="Critical blocking issues")
    sanctions_impact: str = Field("none", description="Impact from Western sanctions")

    class Config:
        schema_extra = {
            "example": {
                "project_id": "NP-DEMOGRAPHY",
                "name": "Demography",
                "name_ru": "Демография",
                "category": "human_capital",
                "total_budget_trillion_rub": 3.1,
                "status": "delayed",
                "challenges": ["Declining birth rate", "Emigration of young population"]
            }
        }


class NationalProjectFailureAnalysis(BaseModel):
    """Analysis of why a national project is struggling"""
    project_id: str = Field(..., description="Project identifier")
    analysis_date: datetime = Field(default_factory=datetime.now)

    # Root causes
    funding_issues: List[str] = Field(..., description="Funding-related issues")
    implementation_gaps: List[str] = Field(..., description="Implementation gaps")
    external_factors: List[str] = Field(..., description="External factors affecting project")
    governance_issues: List[str] = Field(..., description="Governance and management issues")
    capacity_constraints: List[str] = Field(..., description="Capacity constraints")

    # Quantified impact
    budget_shortfall_percent: float = Field(0.0, description="Budget shortfall percentage")
    timeline_delay_months: int = Field(0, description="Delay in months from original plan")
    target_achievement_rate: float = Field(0.0, description="Rate of target achievement (%)")

    # Severity assessment
    overall_risk_level: RiskLevel = Field(..., description="Overall risk level")
    recovery_feasibility: str = Field(..., description="Feasibility of getting back on track")

    class Config:
        schema_extra = {
            "example": {
                "project_id": "NP-ROADS",
                "funding_issues": ["Inflation eroding purchasing power", "Budget reallocation to defense"],
                "overall_risk_level": "high",
                "recovery_feasibility": "requires_significant_intervention"
            }
        }


# ==================== ECONOMIC CRISIS FACTORS ====================

class EconomicCrisisFactor(BaseModel):
    """Individual economic crisis factor analysis"""
    factor_id: str = Field(..., description="Factor identifier")
    factor_type: EconomicCrisisType = Field(..., description="Type of crisis factor")
    name: str = Field(..., description="Factor name")
    description: str = Field(..., description="Detailed description")

    # Current state
    severity: RiskLevel = Field(..., description="Current severity")
    trend: str = Field(..., description="improving/stable/worsening")

    # Quantitative measures
    current_value: float = Field(..., description="Current quantitative value")
    historical_average: float = Field(..., description="Historical average for comparison")
    critical_threshold: float = Field(..., description="Critical threshold value")
    unit: str = Field(..., description="Measurement unit")

    # Impact assessment
    gdp_impact_percent: float = Field(0.0, description="Estimated GDP impact (%)")
    affected_sectors: List[str] = Field(..., description="Most affected sectors")
    affected_population_groups: List[str] = Field(..., description="Affected population groups")

    # Causation
    root_causes: List[str] = Field(..., description="Root causes")
    contributing_factors: List[str] = Field(..., description="Contributing factors")
    interconnected_crises: List[str] = Field(..., description="Related crisis factors")

    class Config:
        schema_extra = {
            "example": {
                "factor_id": "CRISIS-INFLATION",
                "factor_type": "inflation",
                "name": "Hyperinflation Risk",
                "current_value": 20.0,
                "critical_threshold": 25.0,
                "unit": "percent",
                "severity": "high"
            }
        }


class RussianEconomicCrisisReport(BaseModel):
    """Comprehensive Russian economic crisis report"""
    report_id: str = Field(..., description="Report identifier")
    report_date: datetime = Field(default_factory=datetime.now)
    reporting_period: str = Field(..., description="Reporting period")

    # Overall assessment
    overall_economic_health: RiskLevel = Field(..., description="Overall health assessment")
    gdp_growth_actual: float = Field(..., description="Actual GDP growth (%)")
    gdp_growth_official: float = Field(..., description="Official GDP growth figure (%)")

    # Crisis factors
    active_crisis_factors: List[EconomicCrisisFactor] = Field(
        ..., description="Active crisis factors"
    )

    # Key metrics
    inflation_rate_official: float = Field(..., description="Official inflation rate")
    inflation_rate_estimated: float = Field(..., description="Estimated real inflation")
    ruble_exchange_rate_usd: float = Field(..., description="RUB/USD exchange rate")
    budget_deficit_percent_gdp: float = Field(..., description="Budget deficit as % of GDP")
    national_wealth_fund_trillion_rub: float = Field(..., description="NWF reserves")
    central_bank_rate: float = Field(..., description="Central bank key rate (%)")

    # Sectoral analysis
    defense_spending_percent_gdp: float = Field(..., description="Defense spending % of GDP")
    civilian_spending_trend: str = Field(..., description="Trend in civilian spending")

    # Structural issues
    structural_problems: List[str] = Field(..., description="Structural economic problems")
    sanctions_impact_summary: str = Field(..., description="Summary of sanctions impact")

    # Outlook
    short_term_outlook: str = Field(..., description="1-year outlook")
    medium_term_outlook: str = Field(..., description="3-5 year outlook")


# ==================== SCIENCE & TECHNOLOGY ====================

class STProgram(BaseModel):
    """Russian Science and Technology Program"""
    program_id: str = Field(..., description="Program identifier")
    name: str = Field(..., description="Program name")
    sector: STSectorType = Field(..., description="S&T sector")
    description: str = Field(..., description="Program description")

    # Funding
    annual_budget_billion_rub: float = Field(..., description="Annual budget in billion RUB")
    funding_trend: str = Field(..., description="increasing/stable/decreasing")

    # Status
    status: ProjectStatus = Field(..., description="Current status")
    global_competitiveness_rank: int = Field(..., description="Global ranking in sector")
    competitiveness_trend: str = Field(..., description="improving/stable/declining")

    # Key projects
    flagship_projects: List[Dict[str, Any]] = Field(..., description="Flagship projects")
    delayed_projects: List[str] = Field(default_factory=list, description="Delayed projects")
    cancelled_projects: List[str] = Field(default_factory=list, description="Cancelled projects")

    # Challenges
    key_challenges: List[str] = Field(..., description="Key challenges")
    technology_gaps: List[str] = Field(..., description="Technology gaps vs global leaders")
    brain_drain_impact: str = Field(..., description="Impact of brain drain on sector")
    sanctions_impact: str = Field(..., description="Sanctions impact on sector")

    # Dependencies
    foreign_dependencies: List[Dict[str, Any]] = Field(
        ..., description="Critical foreign dependencies"
    )
    import_substitution_status: str = Field(
        ..., description="Status of import substitution efforts"
    )


class STFailureAnalysis(BaseModel):
    """Analysis of struggling S&T programs"""
    program_id: str = Field(..., description="Program identifier")
    analysis_date: datetime = Field(default_factory=datetime.now)

    # Core problems
    funding_problems: List[str] = Field(..., description="Funding issues")
    talent_problems: List[str] = Field(..., description="Talent and brain drain issues")
    technology_access_problems: List[str] = Field(..., description="Technology access issues")
    infrastructure_problems: List[str] = Field(..., description="Infrastructure gaps")
    management_problems: List[str] = Field(..., description="Management and governance issues")

    # Competitive position
    gap_with_global_leaders: Dict[str, Any] = Field(
        ..., description="Gap analysis with US, China, EU"
    )
    years_behind_leaders: int = Field(..., description="Estimated years behind leaders")

    # Impact assessment
    economic_impact: str = Field(..., description="Economic impact of failures")
    strategic_impact: str = Field(..., description="Strategic/security impact")
    innovation_ecosystem_impact: str = Field(..., description="Impact on innovation ecosystem")

    # Recovery prospects
    recovery_difficulty: str = Field(..., description="easy/moderate/difficult/very_difficult")
    resources_needed_for_recovery: Dict[str, Any] = Field(
        ..., description="Resources needed for recovery"
    )
    estimated_recovery_timeline_years: int = Field(
        ..., description="Estimated years to recover competitiveness"
    )


# ==================== SOLUTIONS ====================

class CrisisSolution(BaseModel):
    """Proposed solution for addressing Russian economic/S&T challenges"""
    solution_id: str = Field(..., description="Solution identifier")
    title: str = Field(..., description="Solution title")
    target_problems: List[str] = Field(..., description="Problems this solution addresses")

    # Classification
    priority: SolutionPriority = Field(..., description="Implementation priority")
    solution_type: str = Field(..., description="policy/structural/investment/reform")
    affected_sectors: List[str] = Field(..., description="Affected sectors")

    # Description
    description: str = Field(..., description="Detailed description")
    implementation_steps: List[str] = Field(..., description="Implementation steps")
    key_actions: List[str] = Field(..., description="Key immediate actions")

    # Requirements
    estimated_cost_billion_rub: float = Field(..., description="Estimated cost in billion RUB")
    timeline_months: int = Field(..., description="Implementation timeline")
    prerequisites: List[str] = Field(..., description="Prerequisites for implementation")
    institutional_requirements: List[str] = Field(..., description="Institutional requirements")

    # Expected outcomes
    expected_outcomes: List[str] = Field(..., description="Expected outcomes")
    gdp_impact_percent: float = Field(0.0, description="Expected GDP impact (%)")
    employment_impact: int = Field(0, description="Expected employment impact")

    # Risks
    implementation_risks: List[str] = Field(..., description="Implementation risks")
    political_feasibility: str = Field(..., description="low/medium/high")
    dependency_on_external_factors: List[str] = Field(
        ..., description="External dependencies"
    )

    # Success metrics
    success_metrics: List[Dict[str, Any]] = Field(..., description="Success metrics")


class NationalProjectRecoveryPlan(BaseModel):
    """Recovery plan for struggling national project"""
    project_id: str = Field(..., description="National project ID")
    plan_id: str = Field(..., description="Recovery plan ID")
    plan_date: datetime = Field(default_factory=datetime.now)

    # Current state assessment
    current_status: ProjectStatus = Field(..., description="Current status")
    completion_gap_percent: float = Field(..., description="Gap from target completion")
    remaining_budget_gap_trillion_rub: float = Field(..., description="Budget gap")

    # Root cause analysis
    primary_failure_causes: List[str] = Field(..., description="Primary causes of failure")
    secondary_factors: List[str] = Field(..., description="Contributing factors")

    # Recovery strategy
    recovery_approach: str = Field(..., description="Overall recovery approach")
    funding_solutions: List[CrisisSolution] = Field(..., description="Funding solutions")
    implementation_solutions: List[CrisisSolution] = Field(
        ..., description="Implementation solutions"
    )
    governance_reforms: List[str] = Field(..., description="Governance reforms needed")

    # Timeline
    recovery_phases: List[Dict[str, Any]] = Field(..., description="Phased recovery plan")
    estimated_full_recovery_date: str = Field(..., description="Estimated full recovery date")

    # Resource requirements
    additional_funding_required_trillion_rub: float = Field(
        ..., description="Additional funding needed"
    )
    human_resources_needed: Dict[str, int] = Field(..., description="HR requirements")
    technology_imports_needed: List[str] = Field(..., description="Technology imports needed")

    # Monitoring
    key_milestones: List[Dict[str, Any]] = Field(..., description="Key milestones")
    monitoring_metrics: List[str] = Field(..., description="Monitoring metrics")


class STRecoveryPlan(BaseModel):
    """Recovery plan for struggling S&T program"""
    program_id: str = Field(..., description="S&T program ID")
    plan_id: str = Field(..., description="Recovery plan ID")

    # Talent recovery
    brain_drain_reversal_measures: List[str] = Field(
        ..., description="Measures to reverse brain drain"
    )
    talent_development_initiatives: List[str] = Field(
        ..., description="Domestic talent development"
    )
    international_collaboration_opportunities: List[str] = Field(
        ..., description="International collaboration options"
    )

    # Technology access
    import_substitution_roadmap: List[Dict[str, Any]] = Field(
        ..., description="Import substitution roadmap"
    )
    alternative_technology_sources: List[str] = Field(
        ..., description="Alternative sources (China, India, etc.)"
    )
    indigenous_development_priorities: List[str] = Field(
        ..., description="Priority indigenous developments"
    )

    # Funding restructuring
    funding_reallocation: Dict[str, float] = Field(
        ..., description="Proposed funding reallocation"
    )
    new_funding_sources: List[str] = Field(..., description="New funding sources")
    public_private_partnerships: List[Dict[str, Any]] = Field(
        ..., description="PPP opportunities"
    )

    # Implementation
    quick_wins: List[str] = Field(..., description="Quick wins achievable in 6 months")
    medium_term_goals: List[str] = Field(..., description="1-3 year goals")
    long_term_vision: str = Field(..., description="5-10 year vision")

    # Success factors
    critical_success_factors: List[str] = Field(..., description="Critical success factors")
    potential_showstoppers: List[str] = Field(..., description="Potential showstoppers")


class RussianEconomicReformPackage(BaseModel):
    """Comprehensive reform package for Russian economy"""
    package_id: str = Field(..., description="Package identifier")
    package_name: str = Field(..., description="Reform package name")
    creation_date: datetime = Field(default_factory=datetime.now)

    # Overview
    executive_summary: str = Field(..., description="Executive summary")
    target_problems: List[EconomicCrisisType] = Field(
        ..., description="Target crisis types"
    )
    reform_philosophy: str = Field(..., description="Underlying reform philosophy")

    # Components
    fiscal_reforms: List[CrisisSolution] = Field(..., description="Fiscal reform measures")
    monetary_reforms: List[CrisisSolution] = Field(..., description="Monetary measures")
    structural_reforms: List[CrisisSolution] = Field(..., description="Structural reforms")
    institutional_reforms: List[CrisisSolution] = Field(
        ..., description="Institutional reforms"
    )
    st_recovery_plans: List[STRecoveryPlan] = Field(..., description="S&T recovery plans")
    national_project_recovery: List[NationalProjectRecoveryPlan] = Field(
        ..., description="National project recovery plans"
    )

    # Implementation
    implementation_sequence: List[str] = Field(
        ..., description="Recommended implementation sequence"
    )
    first_100_days_actions: List[str] = Field(..., description="First 100 days priorities")
    political_requirements: List[str] = Field(..., description="Political requirements")

    # Impact projections
    projected_gdp_impact_5yr: float = Field(..., description="Projected 5-year GDP impact (%)")
    projected_inflation_reduction: float = Field(
        ..., description="Projected inflation reduction"
    )
    projected_investment_increase: float = Field(
        ..., description="Projected investment increase (%)"
    )

    # Constraints and risks
    implementation_constraints: List[str] = Field(..., description="Implementation constraints")
    external_dependencies: List[str] = Field(..., description="External dependencies")
    scenario_analysis: Dict[str, Any] = Field(
        ..., description="Best/base/worst case scenarios"
    )
