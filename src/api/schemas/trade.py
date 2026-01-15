"""
Trade barrier mitigation schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TradeBarrierType(str, Enum):
    """Types of trade barriers"""
    TARIFF = "tariff"
    QUOTA = "quota"
    SUBSIDY = "subsidy"
    REGULATION = "regulation"
    SANCTION = "sanction"
    CUSTOMS_DELAY = "customs_delay"
    TECHNICAL_STANDARD = "technical_standard"


class ExportComplianceStatus(str, Enum):
    """Export compliance status"""
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    NON_COMPLIANT = "non_compliant"
    PENDING_REVIEW = "pending_review"


class TradeRoute(BaseModel):
    """Trade route between countries/regions"""
    id: str = Field(..., description="Unique route identifier")
    origin_country: str = Field(..., description="Origin country code (ISO 3166)")
    destination_country: str = Field(..., description="Destination country code")
    product_category: str = Field(..., description="Product/service category")
    barriers: List[TradeBarrierType] = Field(default_factory=list, description="Active trade barriers")
    compliance_status: ExportComplianceStatus = Field(..., description="Current compliance status")
    alternative_routes: List[str] = Field(default_factory=list, description="Alternative route IDs")
    estimated_cost_impact: float = Field(..., description="Cost impact percentage")
    digital_bypass_possible: bool = Field(False, description="Whether digital bypass is possible")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "CN-US-TECH-001",
                "origin_country": "CN",
                "destination_country": "US",
                "product_category": "technology",
                "barriers": ["tariff", "regulation"],
                "compliance_status": "at_risk",
                "alternative_routes": ["CN-VN-TECH-001", "CN-MX-TECH-001"],
                "estimated_cost_impact": 25.5,
                "digital_bypass_possible": True
            }
        }


class DigitalExportGatewayRequest(BaseModel):
    """Request for digital export gateway"""
    route_id: str = Field(..., description="Trade route ID")
    product_description: str = Field(..., description="Product/service description")
    value_usd: float = Field(..., description="Value in USD")
    compliance_documents: Dict[str, Any] = Field(..., description="Compliance documentation")
    preferred_delivery_channels: List[str] = Field(default_factory=list, description="Preferred delivery channels")
    
    class Config:
        schema_extra = {
            "example": {
                "route_id": "CN-US-TECH-001",
                "product_description": "Cloud-based AI analytics platform",
                "value_usd": 50000.0,
                "compliance_documents": {
                    "export_license": "EL2024001",
                    "tech_transfer_cert": "TTC2024001"
                },
                "preferred_delivery_channels": ["api", "digital_download"]
            }
        }


class MarketIntelligenceReport(BaseModel):
    """Market intelligence report for trade planning"""
    id: str = Field(..., description="Report ID")
    market_code: str = Field(..., description="Market identifier")
    analysis_period: str = Field(..., description="Analysis period (YYYY-MM)")
    key_insights: List[str] = Field(..., description="Key insights")
    risk_assessment: Dict[str, float] = Field(..., description="Risk scores by category")
    opportunity_assessment: Dict[str, float] = Field(..., description="Opportunity scores")
    recommended_actions: List[str] = Field(..., description="Recommended actions")
    data_sources: List[str] = Field(..., description="Data sources used")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "MI-2024-Q1-US-TECH",
                "market_code": "US-TECH",
                "analysis_period": "2024-01",
                "key_insights": [
                    "Increased demand for AI/ML solutions",
                    "Regulatory scrutiny on data privacy",
                    "Opportunities in edge computing"
                ],
                "risk_assessment": {"regulatory": 0.7, "competitive": 0.5, "currency": 0.3},
                "opportunity_assessment": {"ai_ml": 0.8, "cloud_services": 0.6, "iot": 0.7},
                "recommended_actions": [
                    "Focus on B2B AI solutions",
                    "Establish local compliance team",
                    "Partner with cloud providers"
                ],
                "data_sources": ["customs_data", "market_reports", "news_analysis"]
            }
        }
