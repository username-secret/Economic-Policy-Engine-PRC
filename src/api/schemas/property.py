"""
Property sector stabilization schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PropertyMarketHealth(str, Enum):
    """Property market health indicators"""
    HEALTHY = "healthy"
    MODERATE = "moderate"
    RISKY = "risky"
    CRITICAL = "critical"


class PropertyType(str, Enum):
    """Types of properties"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    AFFORDABLE_HOUSING = "affordable_housing"


class PropertyMarketMetrics(BaseModel):
    """Property market metrics for analysis"""
    region_code: str = Field(..., description="Region identifier")
    property_type: PropertyType = Field(..., description="Type of property")
    price_index: float = Field(..., description="Price index (base=100)")
    volume_index: float = Field(..., description="Transaction volume index")
    vacancy_rate: float = Field(..., description="Vacancy rate percentage")
    rental_yield: float = Field(..., description="Rental yield percentage")
    debt_to_value: float = Field(..., description="Average debt to value ratio")
    affordability_index: float = Field(..., description="Affordability index")
    market_health: PropertyMarketHealth = Field(..., description="Overall market health")
    
    class Config:
        schema_extra = {
            "example": {
                "region_code": "BJ-01",
                "property_type": "residential",
                "price_index": 95.2,
                "volume_index": 78.5,
                "vacancy_rate": 12.3,
                "rental_yield": 2.1,
                "debt_to_value": 65.8,
                "affordability_index": 45.2,
                "market_health": "risky"
            }
        }


class DebtRestructuringRequest(BaseModel):
    """Request for debt restructuring analysis"""
    property_id: str = Field(..., description="Property identifier")
    current_debt_amount: float = Field(..., description="Current debt amount in CNY")
    property_value: float = Field(..., description="Current property value in CNY")
    monthly_income: float = Field(..., description="Monthly income in CNY")
    monthly_expenses: float = Field(..., description="Monthly expenses in CNY")
    preferred_restructuring_type: str = Field(..., description="Preferred restructuring type")
    credit_score: int = Field(..., description="Credit score (0-1000)")
    
    class Config:
        schema_extra = {
            "example": {
                "property_id": "PROP-BJ-2024001",
                "current_debt_amount": 5000000.0,
                "property_value": 6000000.0,
                "monthly_income": 25000.0,
                "monthly_expenses": 18000.0,
                "preferred_restructuring_type": "term_extension",
                "credit_score": 720
            }
        }


class AffordableHousingProject(BaseModel):
    """Affordable housing project data"""
    project_id: str = Field(..., description="Project identifier")
    location: str = Field(..., description="Project location")
    total_units: int = Field(..., description="Total housing units")
    affordable_units: int = Field(..., description="Number of affordable units")
    average_price_per_sqm: float = Field(..., description="Average price per square meter")
    target_income_group: str = Field(..., description="Target income group")
    completion_date: datetime = Field(..., description="Expected completion date")
    funding_sources: List[str] = Field(..., description="Funding sources")
    current_status: str = Field(..., description="Current project status")
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "AFF-SH-2024001",
                "location": "Shanghai, Pudong District",
                "total_units": 1000,
                "affordable_units": 700,
                "average_price_per_sqm": 35000.0,
                "target_income_group": "middle_income",
                "completion_date": "2025-12-31T00:00:00",
                "funding_sources": ["government", "private_investment", "bank_loan"],
                "current_status": "under_construction"
            }
        }


class InvestmentReallocationRecommendation(BaseModel):
    """Recommendation for investment reallocation"""
    from_sector: str = Field(..., description="Source sector (property or specific)")
    to_sector: str = Field(..., description="Target sector")
    recommended_amount: float = Field(..., description="Recommended amount in CNY")
    expected_return: float = Field(..., description="Expected annual return percentage")
    risk_level: str = Field(..., description="Risk level (low/medium/high)")
    time_horizon: str = Field(..., description="Recommended time horizon")
    rationale: List[str] = Field(..., description="Rationale for recommendation")
    
    class Config:
        schema_extra = {
            "example": {
                "from_sector": "commercial_property",
                "to_sector": "green_technology",
                "recommended_amount": 10000000.0,
                "expected_return": 12.5,
                "risk_level": "medium",
                "time_horizon": "3-5 years",
                "rationale": [
                    "Higher growth potential in green tech",
                    "Policy support for green investments",
                    "Diversification benefits"
                ]
            }
        }
