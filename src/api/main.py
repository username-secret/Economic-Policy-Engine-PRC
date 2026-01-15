"""
Main API gateway for Chinese Economic Headwinds Fix
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from .schemas.trade import TradeRoute, DigitalExportGatewayRequest, MarketIntelligenceReport
from .schemas.property import PropertyMarketMetrics, DebtRestructuringRequest
from .schemas.tech import TechDependencyAnalysis, InnovationProject
from .services.trade_service import TradeBarrierService
from .services.property_service import PropertyStabilizationService
from .services.tech_service import TechResilienceService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
trade_service = None
property_service = None
tech_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for service initialization
    """
    global trade_service, property_service, tech_service
    
    logger.info("Initializing Chinese Economic Headwinds Fix services...")
    
    # Initialize services
    trade_service = TradeBarrierService()
    property_service = PropertyStabilizationService()
    tech_service = TechResilienceService()
    
    logger.info("All services initialized successfully")
    
    yield
    
    logger.info("Shutting down Chinese Economic Headwinds Fix services...")
    # Cleanup if needed

# Create FastAPI app
app = FastAPI(
    title="Chinese Economic Headwinds Fix API",
    description="Comprehensive technical solution for China's economic challenges",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "name": "Chinese Economic Headwinds Fix API",
        "version": "1.0.0",
        "description": "Comprehensive technical solution for China's economic challenges",
        "endpoints": {
            "trade": "/api/v1/trade/*",
            "property": "/api/v1/property/*",
            "tech": "/api/v1/tech/*",
            "demand": "/api/v1/demand/*",
            "growth": "/api/v1/growth/*"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": "2024-01-13T10:08:00Z"}

# Trade Barrier Mitigation Endpoints
@app.post("/api/v1/trade/routes/analyze", response_model=TradeRoute)
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

@app.post("/api/v1/trade/export/digital", response_model=Dict[str, Any])
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

@app.get("/api/v1/trade/intelligence/{market_code}", response_model=MarketIntelligenceReport)
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

# Property Sector Stabilization Endpoints
@app.get("/api/v1/property/metrics/{region_code}", response_model=PropertyMarketMetrics)
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

@app.post("/api/v1/property/debt/restructure", response_model=Dict[str, Any])
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

# Tech Sector Resilience Endpoints
@app.get("/api/v1/tech/dependencies/{tech_id}", response_model=TechDependencyAnalysis)
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

@app.get("/api/v1/tech/innovation/{project_id}", response_model=InnovationProject)
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

# Data Lake Integration Endpoints
@app.get("/api/v1/data/economic-indicators")
async def get_economic_indicators(indicator_type: str = "all", period: str = "2024-01"):
    """
    Get economic indicators from data lake
    """
    return {
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

@app.get("/api/v1/data/trade-flows")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
