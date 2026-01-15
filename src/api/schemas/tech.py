"""
Tech sector resilience schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TechDependencyRisk(str, Enum):
    """Technology dependency risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class TechCategory(str, Enum):
    """Technology categories"""
    OPERATING_SYSTEM = "operating_system"
    DATABASE = "database"
    CLOUD_INFRASTRUCTURE = "cloud_infrastructure"
    AI_FRAMEWORK = "ai_framework"
    DEVELOPMENT_TOOLS = "development_tools"
    SECURITY_SOFTWARE = "security_software"
    HARDWARE = "hardware"
    NETWORKING = "networking"


class TechDependencyAnalysis(BaseModel):
    """Technology dependency analysis"""
    tech_id: str = Field(..., description="Technology identifier")
    name: str = Field(..., description="Technology name")
    category: TechCategory = Field(..., description="Technology category")
    origin_country: str = Field(..., description="Country of origin")
    dependency_level: float = Field(..., description="Dependency level (0-1)")
    risk_level: TechDependencyRisk = Field(..., description="Risk level")
    alternative_technologies: List[str] = Field(..., description="Alternative technology IDs")
    migration_complexity: str = Field(..., description="Migration complexity")
    estimated_migration_cost: float = Field(..., description="Estimated migration cost in CNY")
    
    class Config:
        schema_extra = {
            "example": {
                "tech_id": "TECH-OS-001",
                "name": "Windows Server",
                "category": "operating_system",
                "origin_country": "US",
                "dependency_level": 0.85,
                "risk_level": "high",
                "alternative_technologies": ["TECH-OS-002", "TECH-OS-003"],
                "migration_complexity": "medium",
                "estimated_migration_cost": 5000000.0
            }
        }


class LocalizationAssessment(BaseModel):
    """Localization assessment for technology"""
    tech_id: str = Field(..., description="Technology identifier")
    localization_feasibility: float = Field(..., description="Feasibility score (0-1)")
    required_modifications: List[str] = Field(..., description="Required modifications")
    regulatory_compliance: Dict[str, bool] = Field(..., description="Regulatory compliance status")
    domestic_alternatives: List[str] = Field(..., description="Domestic alternative IDs")
    estimated_timeline_months: int = Field(..., description="Estimated timeline in months")
    
    class Config:
        schema_extra = {
            "example": {
                "tech_id": "TECH-DB-001",
                "localization_feasibility": 0.7,
                "required_modifications": [
                    "Chinese language support",
                    "Data sovereignty compliance",
                    "Local authentication integration"
                ],
                "regulatory_compliance": {
                    "cybersecurity_law": True,
                    "data_privacy": False,
                    "export_control": True
                },
                "domestic_alternatives": ["TECH-DB-002", "TECH-DB-003"],
                "estimated_timeline_months": 18
            }
        }


class InnovationPipelineStage(str, Enum):
    """Stages in innovation pipeline"""
    RESEARCH = "research"
    PROTOTYPE = "prototype"
    PILOT = "pilot"
    COMMERCIALIZATION = "commercialization"
    SCALE = "scale"
    MATURE = "mature"


class InnovationProject(BaseModel):
    """Innovation project in pipeline"""
    project_id: str = Field(..., description="Project identifier")
    name: str = Field(..., description="Project name")
    technology_area: str = Field(..., description="Technology area")
    current_stage: InnovationPipelineStage = Field(..., description="Current stage")
    next_stage_target_date: datetime = Field(..., description="Target date for next stage")
    funding_required: float = Field(..., description="Funding required in CNY")
    commercial_potential: float = Field(..., description="Commercial potential score (0-1)")
    strategic_importance: float = Field(..., description="Strategic importance score (0-1)")
    blocking_issues: List[str] = Field(..., description="Blocking issues")
    
    class Config:
        schema_extra = {
            "example": {
                "project_id": "INNO-AI-001",
                "name": "Domestic Large Language Model",
                "technology_area": "artificial_intelligence",
                "current_stage": "pilot",
                "next_stage_target_date": "2024-06-30T00:00:00",
                "funding_required": 50000000.0,
                "commercial_potential": 0.9,
                "strategic_importance": 0.95,
                "blocking_issues": [
                    "GPU availability",
                    "Training data quality",
                    "Talent shortage"
                ]
            }
        }


class TalentMatchRequest(BaseModel):
    """Request for talent matching"""
    required_skills: List[str] = Field(..., description="Required technical skills")
    experience_level: str = Field(..., description="Required experience level")
    industry_domain: str = Field(..., description="Industry domain")
    location_preference: List[str] = Field(..., description="Location preferences")
    strategic_priority: str = Field(..., description="Strategic priority area")
    
    class Config:
        schema_extra = {
            "example": {
                "required_skills": ["machine_learning", "python", "distributed_systems"],
                "experience_level": "senior",
                "industry_domain": "fintech",
                "location_preference": ["Beijing", "Shanghai", "Shenzhen"],
                "strategic_priority": "ai_security"
            }
        }
