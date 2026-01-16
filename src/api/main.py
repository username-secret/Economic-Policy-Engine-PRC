"""
Main API gateway for Economic Policy Engine
Covers China's Economic Headwinds, 15th Five-Year Plan, and Russian Federation Economic Analysis
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# China schemas and services
from .schemas.trade import TradeRoute, DigitalExportGatewayRequest, MarketIntelligenceReport
from .schemas.property import PropertyMarketMetrics, DebtRestructuringRequest
from .schemas.tech import TechDependencyAnalysis, InnovationProject
from .schemas.china_fyp import (
    FifteenthFiveYearPlan, FYPTarget, FYPPriorityArea, FYPProgressReport,
    FYPPolicyRecommendation, IndustrialModernizationPlan, TechSelfReliancePlan
)
from .services.trade_service import TradeBarrierService
from .services.property_service import PropertyStabilizationService
from .services.tech_service import TechResilienceService
from .services.china_fyp_service import ChinaFYPService

# Russia schemas and services
from .schemas.russia import (
    NationalProject, NationalProjectFailureAnalysis, STProgram, STFailureAnalysis,
    RussianEconomicCrisisReport, CrisisSolution, EconomicCrisisType,
    RussianEconomicReformPackage, NationalProjectRecoveryPlan, STRecoveryPlan
)
from .services.russia_service import RussianEconomicService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
trade_service = None
property_service = None
tech_service = None
china_fyp_service = None
russia_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for service initialization
    """
    global trade_service, property_service, tech_service, china_fyp_service, russia_service

    logger.info("Initializing Economic Policy Engine services...")

    # Initialize China services
    trade_service = TradeBarrierService()
    property_service = PropertyStabilizationService()
    tech_service = TechResilienceService()
    china_fyp_service = ChinaFYPService()

    # Initialize Russia services
    russia_service = RussianEconomicService()

    logger.info("All services initialized successfully")

    yield

    logger.info("Shutting down Economic Policy Engine services...")


# Create FastAPI app
app = FastAPI(
    title="Economic Policy Engine API",
    description="""
    Comprehensive technical platform for economic policy analysis covering:

    **China:**
    - Economic Headwinds Mitigation (trade barriers, property, tech)
    - 15th Five-Year Plan (2026-2030) analysis and tracking

    **Russia:**
    - National Projects analysis and failure diagnostics
    - Science & Technology program assessment
    - Economic crisis analysis and solutions
    - Comprehensive reform packages
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "Economic Policy Engine API",
        "version": "2.0.0",
        "description": "Comprehensive technical solution for China and Russia economic policy analysis",
        "modules": {
            "china": {
                "description": "China economic analysis",
                "endpoints": {
                    "trade": "/api/v1/china/trade/*",
                    "property": "/api/v1/china/property/*",
                    "tech": "/api/v1/china/tech/*",
                    "fyp": "/api/v1/china/fyp/*"
                }
            },
            "russia": {
                "description": "Russia economic analysis",
                "endpoints": {
                    "national_projects": "/api/v1/russia/national-projects/*",
                    "st_programs": "/api/v1/russia/st-programs/*",
                    "crisis": "/api/v1/russia/crisis/*",
                    "solutions": "/api/v1/russia/solutions/*"
                }
            }
        },
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "china_trade": trade_service is not None,
            "china_property": property_service is not None,
            "china_tech": tech_service is not None,
            "china_fyp": china_fyp_service is not None,
            "russia": russia_service is not None
        }
    }


# =============================================================================
# CHINA - Trade Barrier Mitigation Endpoints
# =============================================================================

@app.post("/api/v1/china/trade/routes/analyze", response_model=TradeRoute, tags=["China - Trade"])
async def analyze_trade_route(route_id: str):
    """
    Analyze a specific trade route for barriers and alternatives
    """
    try:
        return await trade_service.analyze_route(route_id)
    except Exception as e:
        logger.error(f"Error analyzing trade route: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing trade route: {str(e)}"
        )


@app.post("/api/v1/china/trade/export/digital", response_model=Dict[str, Any], tags=["China - Trade"])
async def process_digital_export(request: DigitalExportGatewayRequest):
    """
    Process digital export through the gateway
    """
    try:
        return await trade_service.process_digital_export(request)
    except Exception as e:
        logger.error(f"Error processing digital export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing digital export: {str(e)}"
        )


@app.get("/api/v1/china/trade/intelligence/{market_code}", response_model=MarketIntelligenceReport, tags=["China - Trade"])
async def get_market_intelligence(market_code: str, period: str = "2024-01"):
    """
    Get market intelligence report for specific market
    """
    try:
        return await trade_service.get_market_intelligence(market_code, period)
    except Exception as e:
        logger.error(f"Error getting market intelligence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting market intelligence: {str(e)}"
        )


# =============================================================================
# CHINA - Property Sector Stabilization Endpoints
# =============================================================================

@app.get("/api/v1/china/property/metrics/{region_code}", response_model=PropertyMarketMetrics, tags=["China - Property"])
async def get_property_metrics(region_code: str, property_type: str = "residential"):
    """
    Get property market metrics for a region
    """
    try:
        return await property_service.get_market_metrics(region_code, property_type)
    except Exception as e:
        logger.error(f"Error getting property metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting property metrics: {str(e)}"
        )


@app.post("/api/v1/china/property/debt/restructure", response_model=Dict[str, Any], tags=["China - Property"])
async def analyze_debt_restructuring(request: DebtRestructuringRequest):
    """
    Analyze debt restructuring options
    """
    try:
        return await property_service.analyze_debt_restructuring(request)
    except Exception as e:
        logger.error(f"Error analyzing debt restructuring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing debt restructuring: {str(e)}"
        )


# =============================================================================
# CHINA - Tech Sector Resilience Endpoints
# =============================================================================

@app.get("/api/v1/china/tech/dependencies/{tech_id}", response_model=TechDependencyAnalysis, tags=["China - Tech"])
async def analyze_tech_dependency(tech_id: str):
    """
    Analyze technology dependency and risks
    """
    try:
        return await tech_service.analyze_dependency(tech_id)
    except Exception as e:
        logger.error(f"Error analyzing tech dependency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing tech dependency: {str(e)}"
        )


@app.get("/api/v1/china/tech/innovation/{project_id}", response_model=InnovationProject, tags=["China - Tech"])
async def get_innovation_project(project_id: str):
    """
    Get innovation project details
    """
    try:
        return await tech_service.get_innovation_project(project_id)
    except Exception as e:
        logger.error(f"Error getting innovation project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting innovation project: {str(e)}"
        )


# =============================================================================
# CHINA - 15th Five-Year Plan (2026-2030) Endpoints
# =============================================================================

@app.get("/api/v1/china/fyp/overview", response_model=FifteenthFiveYearPlan, tags=["China - 15th FYP"])
async def get_fyp_overview():
    """
    Get complete 15th Five-Year Plan (2026-2030) overview

    Returns the full plan including:
    - GDP and development targets
    - Industrial modernization plan
    - Technology self-reliance strategy
    - Domestic consumption enhancement
    - Green development goals
    - Opening up initiatives
    """
    try:
        return await china_fyp_service.get_fyp_overview()
    except Exception as e:
        logger.error(f"Error getting FYP overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting FYP overview: {str(e)}"
        )


@app.get("/api/v1/china/fyp/targets", response_model=List[FYPTarget], tags=["China - 15th FYP"])
async def get_fyp_targets(area: Optional[FYPPriorityArea] = None):
    """
    Get quantitative targets from the 15th Five-Year Plan

    Optionally filter by priority area:
    - industrial_modernization
    - tech_self_reliance
    - domestic_consumption
    - green_development
    - opening_up
    - digital_china
    - rural_revitalization
    - social_welfare
    """
    try:
        return await china_fyp_service.get_priority_targets(area)
    except Exception as e:
        logger.error(f"Error getting FYP targets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting FYP targets: {str(e)}"
        )


@app.get("/api/v1/china/fyp/targets/{target_id}", response_model=FYPTarget, tags=["China - 15th FYP"])
async def get_fyp_target_details(target_id: str):
    """
    Get details for a specific FYP target
    """
    try:
        result = await china_fyp_service.get_target_details(target_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target {target_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting target details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting target details: {str(e)}"
        )


@app.get("/api/v1/china/fyp/industrial-modernization", response_model=IndustrialModernizationPlan, tags=["China - 15th FYP"])
async def get_industrial_modernization():
    """
    Get the industrial modernization component of the 15th FYP

    Includes:
    - Emerging industries (aerospace, hydrogen, quantum, etc.)
    - Traditional industry upgrades
    - Key technology development priorities
    """
    try:
        return await china_fyp_service.get_industrial_modernization_plan()
    except Exception as e:
        logger.error(f"Error getting industrial modernization plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting industrial modernization plan: {str(e)}"
        )


@app.get("/api/v1/china/fyp/tech-self-reliance", response_model=TechSelfReliancePlan, tags=["China - 15th FYP"])
async def get_tech_self_reliance():
    """
    Get the technology self-reliance strategy from the 15th FYP

    Includes:
    - Core technology breakthroughs
    - Semiconductor targets
    - AI development goals
    - Talent development plans
    """
    try:
        return await china_fyp_service.get_tech_self_reliance_plan()
    except Exception as e:
        logger.error(f"Error getting tech self-reliance plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting tech self-reliance plan: {str(e)}"
        )


@app.get("/api/v1/china/fyp/emerging-industries", response_model=Dict[str, Any], tags=["China - 15th FYP"])
async def get_emerging_industries_analysis():
    """
    Get analysis of emerging industries prioritized in the 15th FYP

    Covers: Low-altitude economy, hydrogen, commercial space, quantum, etc.
    """
    try:
        return await china_fyp_service.get_emerging_industries_analysis()
    except Exception as e:
        logger.error(f"Error getting emerging industries analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting emerging industries analysis: {str(e)}"
        )


@app.get("/api/v1/china/fyp/progress/{period}", response_model=FYPProgressReport, tags=["China - 15th FYP"])
async def get_fyp_progress_report(period: str):
    """
    Get progress report for a specific period (format: YYYY-MM)
    """
    try:
        return await china_fyp_service.generate_progress_report(period)
    except Exception as e:
        logger.error(f"Error generating progress report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating progress report: {str(e)}"
        )


@app.get("/api/v1/china/fyp/recommendations/{area}", response_model=List[FYPPolicyRecommendation], tags=["China - 15th FYP"])
async def get_policy_recommendations(area: FYPPriorityArea):
    """
    Get policy recommendations for a specific priority area
    """
    try:
        return await china_fyp_service.get_policy_recommendations(area)
    except Exception as e:
        logger.error(f"Error getting policy recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting policy recommendations: {str(e)}"
        )


# =============================================================================
# RUSSIA - National Projects Endpoints
# =============================================================================

@app.get("/api/v1/russia/national-projects", response_model=List[NationalProject], tags=["Russia - National Projects"])
async def get_national_projects():
    """
    Get overview of all Russian National Projects (2018-2030)

    Returns status, budget, completion rate, and challenges for each project:
    - Demography
    - Healthcare
    - Education
    - Housing
    - Roads
    - Digital Economy
    - Science and Universities
    - and more...
    """
    try:
        return await russia_service.get_national_projects_overview()
    except Exception as e:
        logger.error(f"Error getting national projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting national projects: {str(e)}"
        )


@app.get("/api/v1/russia/national-projects/{project_id}", response_model=NationalProject, tags=["Russia - National Projects"])
async def get_national_project(project_id: str):
    """
    Get details for a specific national project

    Project IDs: NP-DEMOGRAPHY, NP-HEALTHCARE, NP-ROADS, NP-DIGITAL, NP-SCIENCE, NP-HOUSING
    """
    try:
        result = await russia_service.get_national_project(project_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"National project {project_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting national project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting national project: {str(e)}"
        )


@app.get("/api/v1/russia/national-projects/{project_id}/failure-analysis", response_model=NationalProjectFailureAnalysis, tags=["Russia - National Projects"])
async def analyze_project_failure(project_id: str):
    """
    Get detailed failure analysis for a struggling national project

    Analyzes:
    - Funding issues
    - Implementation gaps
    - External factors (sanctions, war)
    - Governance issues
    - Capacity constraints
    """
    try:
        return await russia_service.analyze_project_failure(project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analyzing project failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing project failure: {str(e)}"
        )


# =============================================================================
# RUSSIA - Science & Technology Programs Endpoints
# =============================================================================

@app.get("/api/v1/russia/st-programs", response_model=List[STProgram], tags=["Russia - S&T Programs"])
async def get_st_programs():
    """
    Get overview of Russian Science & Technology programs

    Covers:
    - Space Program (Roscosmos)
    - Semiconductor Development
    - AI Development
    - Hypersonics
    - Nuclear Technology
    """
    try:
        return await russia_service.get_st_programs_overview()
    except Exception as e:
        logger.error(f"Error getting S&T programs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting S&T programs: {str(e)}"
        )


@app.get("/api/v1/russia/st-programs/{program_id}", response_model=STProgram, tags=["Russia - S&T Programs"])
async def get_st_program(program_id: str):
    """
    Get details for a specific S&T program

    Program IDs: ST-SPACE, ST-SEMI, ST-AI, ST-HYPERSONICS, ST-NUCLEAR
    """
    try:
        result = await russia_service.get_st_program(program_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"S&T program {program_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting S&T program: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting S&T program: {str(e)}"
        )


@app.get("/api/v1/russia/st-programs/{program_id}/failure-analysis", response_model=STFailureAnalysis, tags=["Russia - S&T Programs"])
async def analyze_st_failure(program_id: str):
    """
    Get detailed failure analysis for a struggling S&T program

    Analyzes:
    - Funding problems
    - Brain drain impact
    - Technology access restrictions
    - Infrastructure gaps
    - Gap with global leaders
    - Recovery prospects
    """
    try:
        return await russia_service.analyze_st_failure(program_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analyzing S&T failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing S&T failure: {str(e)}"
        )


# =============================================================================
# RUSSIA - Economic Crisis Analysis Endpoints
# =============================================================================

@app.get("/api/v1/russia/crisis/report", response_model=RussianEconomicCrisisReport, tags=["Russia - Crisis Analysis"])
async def get_economic_crisis_report():
    """
    Get comprehensive Russian economic crisis report

    Includes:
    - Overall economic health assessment
    - Inflation analysis (official vs real)
    - Budget deficit and NWF status
    - All active crisis factors
    - Sanctions impact summary
    - Short and medium-term outlook
    """
    try:
        return await russia_service.get_economic_crisis_report()
    except Exception as e:
        logger.error(f"Error getting crisis report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting crisis report: {str(e)}"
        )


# =============================================================================
# RUSSIA - Solutions and Reform Packages Endpoints
# =============================================================================

@app.get("/api/v1/russia/solutions", response_model=List[CrisisSolution], tags=["Russia - Solutions"])
async def get_crisis_solutions(crisis_type: Optional[EconomicCrisisType] = None):
    """
    Get proposed solutions for Russian economic challenges

    Optionally filter by crisis type:
    - inflation
    - budget_deficit
    - brain_drain
    - labor_shortage
    - investment_crisis
    - sanctions_impact
    """
    try:
        return await russia_service.get_crisis_solutions(crisis_type)
    except Exception as e:
        logger.error(f"Error getting crisis solutions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting crisis solutions: {str(e)}"
        )


@app.get("/api/v1/russia/reform-package", response_model=RussianEconomicReformPackage, tags=["Russia - Solutions"])
async def get_comprehensive_reform_package():
    """
    Get comprehensive economic reform package for Russia

    Includes:
    - Fiscal reforms
    - Monetary reforms
    - Structural reforms
    - S&T recovery plans
    - National project recovery plans
    - Implementation sequence
    - First 100 days priorities
    - Scenario analysis
    """
    try:
        return await russia_service.generate_reform_package()
    except Exception as e:
        logger.error(f"Error generating reform package: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating reform package: {str(e)}"
        )


# =============================================================================
# Data Lake Integration Endpoints (Legacy - maintaining backward compatibility)
# =============================================================================

@app.get("/api/v1/data/economic-indicators", tags=["Data Lake"])
async def get_economic_indicators(
    country: str = Query("CN", description="Country code: CN or RU"),
    indicator_type: str = "all",
    period: str = "2024-01"
):
    """
    Get economic indicators from data lake
    """
    if country == "RU":
        return {
            "country": "RU",
            "indicator_type": indicator_type,
            "period": period,
            "data": {
                "gdp_growth_official": 3.5,
                "gdp_growth_estimated": 0.5,
                "inflation_official": 9.0,
                "inflation_estimated": 20.0,
                "unemployment_rate": 2.5,
                "central_bank_rate": 21.0,
                "defense_spending_gdp_percent": 8.0,
                "budget_deficit_trillion_rub": 5.7
            },
            "notes": "Significant discrepancy between official and estimated figures"
        }
    return {
        "country": "CN",
        "indicator_type": indicator_type,
        "period": period,
        "data": {
            "gdp_growth": 5.2,
            "industrial_output": 6.1,
            "retail_sales": 7.3,
            "export_growth": 8.5,
            "import_growth": 6.8,
            "inflation_rate": 2.1,
            "unemployment_rate": 5.0
        }
    }


@app.get("/api/v1/data/trade-flows", tags=["Data Lake"])
async def get_trade_flows(origin: str = "CN", destination: str = "all", product: str = "all"):
    """
    Get trade flow data from data lake
    """
    return {
        "origin": origin,
        "destination": destination,
        "product": product,
        "flows": [
            {
                "destination": "US",
                "value_usd": 1500000000,
                "growth_yoy": 8.5,
                "main_products": ["electronics", "machinery", "textiles"]
            },
            {
                "destination": "EU",
                "value_usd": 1200000000,
                "growth_yoy": 6.2,
                "main_products": ["vehicles", "chemicals", "pharmaceuticals"]
            }
        ]
    }


# Legacy endpoints (backward compatibility)
@app.post("/api/v1/trade/routes/analyze", response_model=TradeRoute, tags=["Legacy"], include_in_schema=False)
async def analyze_trade_route_legacy(route_id: str):
    return await analyze_trade_route(route_id)


@app.get("/api/v1/property/metrics/{region_code}", response_model=PropertyMarketMetrics, tags=["Legacy"], include_in_schema=False)
async def get_property_metrics_legacy(region_code: str, property_type: str = "residential"):
    return await get_property_metrics(region_code, property_type)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
