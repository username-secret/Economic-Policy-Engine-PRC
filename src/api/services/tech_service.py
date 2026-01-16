"""
Technology Sector Resilience Service
Provides technology dependency analysis, localization planning, and innovation tracking
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import random

logger = logging.getLogger(__name__)


class DependencyRisk(str, Enum):
    """Technology dependency risk levels"""
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class LocalizationStatus(str, Enum):
    """Localization progress status"""
    NOT_STARTED = "not_started"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ADVANCED = "advanced"
    COMPLETE = "complete"


class TechnologyCategory(str, Enum):
    """Technology categories"""
    SEMICONDUCTOR = "semiconductor"
    SOFTWARE = "software"
    AI_ML = "ai_ml"
    TELECOM = "telecom"
    AEROSPACE = "aerospace"
    MATERIALS = "materials"
    BIOTECH = "biotech"
    QUANTUM = "quantum"
    ENERGY = "energy"


@dataclass
class TechDependencyAnalysis:
    """Technology dependency analysis result"""
    tech_id: str
    tech_name: str
    tech_name_cn: str
    category: str
    current_dependency_pct: float
    domestic_capability_pct: float
    primary_foreign_sources: List[Dict[str, Any]]
    supply_chain_risk: str
    sanctions_vulnerability: str
    localization_status: str
    localization_timeline_years: int
    key_bottlenecks: List[str]
    alternative_sources: List[Dict[str, Any]]
    investment_required_billion_cny: float
    strategic_importance: str
    recommendations: List[str]


@dataclass
class InnovationProject:
    """Innovation project details"""
    project_id: str
    project_name: str
    project_name_cn: str
    category: str
    description: str
    lead_organization: str
    start_date: str
    target_completion: str
    budget_billion_cny: float
    progress_pct: float
    status: str
    key_milestones: List[Dict[str, Any]]
    expected_outcomes: List[str]
    commercialization_potential: str


class TechResilienceService:
    """
    Service for technology sector resilience analysis
    Supports China's tech self-reliance strategy
    """

    def __init__(self):
        self._tech_data = self._initialize_tech_data()
        self._project_data = self._initialize_project_data()

    def _initialize_tech_data(self) -> Dict[str, Dict]:
        """Initialize technology configuration data"""
        return {
            "SEMI-ADV": {
                "name": "Advanced Semiconductors (< 7nm)",
                "name_cn": "先进制程芯片 (< 7nm)",
                "category": TechnologyCategory.SEMICONDUCTOR,
                "foreign_dependency": 95,
                "domestic_capability": 5,
                "sanctions_exposure": "critical",
                "primary_sources": ["Taiwan", "South Korea", "USA"],
                "localization_years": 8
            },
            "SEMI-MID": {
                "name": "Mid-range Semiconductors (14-28nm)",
                "name_cn": "中端制程芯片 (14-28nm)",
                "category": TechnologyCategory.SEMICONDUCTOR,
                "foreign_dependency": 45,
                "domestic_capability": 55,
                "sanctions_exposure": "moderate",
                "primary_sources": ["Taiwan", "South Korea"],
                "localization_years": 3
            },
            "SEMI-LEGACY": {
                "name": "Legacy Semiconductors (> 28nm)",
                "name_cn": "成熟制程芯片 (> 28nm)",
                "category": TechnologyCategory.SEMICONDUCTOR,
                "foreign_dependency": 15,
                "domestic_capability": 85,
                "sanctions_exposure": "low",
                "primary_sources": ["Domestic"],
                "localization_years": 0
            },
            "SEMI-EQUIP": {
                "name": "Semiconductor Manufacturing Equipment",
                "name_cn": "半导体制造设备",
                "category": TechnologyCategory.SEMICONDUCTOR,
                "foreign_dependency": 85,
                "domestic_capability": 15,
                "sanctions_exposure": "critical",
                "primary_sources": ["Netherlands", "Japan", "USA"],
                "localization_years": 10
            },
            "EDA-TOOLS": {
                "name": "EDA Software Tools",
                "name_cn": "EDA工具软件",
                "category": TechnologyCategory.SOFTWARE,
                "foreign_dependency": 90,
                "domestic_capability": 10,
                "sanctions_exposure": "high",
                "primary_sources": ["USA"],
                "localization_years": 7
            },
            "OS-MOBILE": {
                "name": "Mobile Operating Systems",
                "name_cn": "移动操作系统",
                "category": TechnologyCategory.SOFTWARE,
                "foreign_dependency": 30,
                "domestic_capability": 70,
                "sanctions_exposure": "moderate",
                "primary_sources": ["USA", "Domestic (HarmonyOS)"],
                "localization_years": 2
            },
            "AI-GPU": {
                "name": "AI Training GPUs",
                "name_cn": "AI训练GPU",
                "category": TechnologyCategory.AI_ML,
                "foreign_dependency": 80,
                "domestic_capability": 20,
                "sanctions_exposure": "critical",
                "primary_sources": ["USA"],
                "localization_years": 5
            },
            "AI-FRAMEWORK": {
                "name": "AI Development Frameworks",
                "name_cn": "AI开发框架",
                "category": TechnologyCategory.AI_ML,
                "foreign_dependency": 25,
                "domestic_capability": 75,
                "sanctions_exposure": "low",
                "primary_sources": ["Domestic (PaddlePaddle, MindSpore)"],
                "localization_years": 0
            },
            "5G-CORE": {
                "name": "5G Core Network Equipment",
                "name_cn": "5G核心网设备",
                "category": TechnologyCategory.TELECOM,
                "foreign_dependency": 10,
                "domestic_capability": 90,
                "sanctions_exposure": "low",
                "primary_sources": ["Domestic (Huawei, ZTE)"],
                "localization_years": 0
            },
            "AERO-ENGINE": {
                "name": "Aircraft Engines",
                "name_cn": "航空发动机",
                "category": TechnologyCategory.AEROSPACE,
                "foreign_dependency": 70,
                "domestic_capability": 30,
                "sanctions_exposure": "high",
                "primary_sources": ["USA", "France", "UK"],
                "localization_years": 8
            },
            "QUANTUM-COMP": {
                "name": "Quantum Computing",
                "name_cn": "量子计算",
                "category": TechnologyCategory.QUANTUM,
                "foreign_dependency": 40,
                "domestic_capability": 60,
                "sanctions_exposure": "moderate",
                "primary_sources": ["Domestic", "USA"],
                "localization_years": 3
            }
        }

    def _initialize_project_data(self) -> Dict[str, Dict]:
        """Initialize innovation project data"""
        return {
            "PROJ-SEMI-001": {
                "name": "Advanced Node Semiconductor Development",
                "name_cn": "先进节点半导体研发项目",
                "category": TechnologyCategory.SEMICONDUCTOR,
                "lead": "中芯国际 (SMIC)",
                "budget": 120,
                "progress": 35,
                "status": "in_progress"
            },
            "PROJ-AI-001": {
                "name": "Domestic AI Chip Ecosystem",
                "name_cn": "国产AI芯片生态项目",
                "category": TechnologyCategory.AI_ML,
                "lead": "华为海思",
                "budget": 80,
                "progress": 55,
                "status": "in_progress"
            },
            "PROJ-AERO-001": {
                "name": "C919 Indigenous Engine Development",
                "name_cn": "C919国产发动机研发",
                "category": TechnologyCategory.AEROSPACE,
                "lead": "中国航发 (AECC)",
                "budget": 200,
                "progress": 45,
                "status": "in_progress"
            },
            "PROJ-QUANTUM-001": {
                "name": "Quantum Computing Prototype",
                "name_cn": "量子计算原型机项目",
                "category": TechnologyCategory.QUANTUM,
                "lead": "中科院",
                "budget": 50,
                "progress": 70,
                "status": "advanced"
            },
            "PROJ-EDA-001": {
                "name": "Indigenous EDA Platform",
                "name_cn": "国产EDA平台项目",
                "category": TechnologyCategory.SOFTWARE,
                "lead": "华大九天",
                "budget": 30,
                "progress": 40,
                "status": "in_progress"
            }
        }

    async def analyze_dependency(self, tech_id: str) -> TechDependencyAnalysis:
        """
        Analyze technology dependency for a specific technology

        Args:
            tech_id: Technology identifier

        Returns:
            TechDependencyAnalysis with comprehensive analysis
        """
        tech_info = self._tech_data.get(tech_id)

        if not tech_info:
            # Generate generic analysis for unknown tech
            tech_info = {
                "name": f"Technology {tech_id}",
                "name_cn": f"技术 {tech_id}",
                "category": TechnologyCategory.SOFTWARE,
                "foreign_dependency": 50,
                "domestic_capability": 50,
                "sanctions_exposure": "moderate",
                "primary_sources": ["Various"],
                "localization_years": 5
            }

        foreign_dep = tech_info["foreign_dependency"]
        domestic_cap = tech_info["domestic_capability"]
        sanctions_exp = tech_info["sanctions_exposure"]
        loc_years = tech_info["localization_years"]

        # Determine supply chain risk
        if foreign_dep >= 80:
            supply_risk = DependencyRisk.CRITICAL
        elif foreign_dep >= 60:
            supply_risk = DependencyRisk.HIGH
        elif foreign_dep >= 40:
            supply_risk = DependencyRisk.ELEVATED
        elif foreign_dep >= 20:
            supply_risk = DependencyRisk.MODERATE
        else:
            supply_risk = DependencyRisk.LOW

        # Determine localization status
        if domestic_cap >= 90:
            loc_status = LocalizationStatus.COMPLETE
        elif domestic_cap >= 70:
            loc_status = LocalizationStatus.ADVANCED
        elif domestic_cap >= 40:
            loc_status = LocalizationStatus.IN_PROGRESS
        elif domestic_cap >= 10:
            loc_status = LocalizationStatus.PLANNING
        else:
            loc_status = LocalizationStatus.NOT_STARTED

        # Generate bottlenecks
        bottlenecks = []
        if tech_info["category"] == TechnologyCategory.SEMICONDUCTOR:
            bottlenecks.extend([
                "Advanced lithography equipment access",
                "High-purity materials supply",
                "Experienced engineering talent"
            ])
        if sanctions_exp == "critical":
            bottlenecks.append("Export control restrictions on key components")
        if foreign_dep > 50:
            bottlenecks.append("Supply chain concentration risk")

        # Generate foreign sources
        sources = []
        for country in tech_info.get("primary_sources", []):
            if country != "Domestic":
                sources.append({
                    "country": country,
                    "market_share_pct": random.uniform(15, 45),
                    "sanctions_risk": "high" if country == "USA" else "moderate",
                    "alternative_available": domestic_cap > 30
                })

        # Generate alternative sources
        alternatives = []
        if domestic_cap > 20:
            alternatives.append({
                "source": "Domestic manufacturers",
                "capability_level": f"{domestic_cap}%",
                "timeline_months": loc_years * 12 if loc_years > 0 else 0,
                "investment_required": True
            })

        # Calculate investment required
        investment = (foreign_dep * 0.8) + (loc_years * 5)

        # Generate recommendations
        recommendations = []
        if foreign_dep >= 70:
            recommendations.append("Prioritize R&D investment in domestic alternatives")
        if sanctions_exp == "critical":
            recommendations.append("Develop sanctions-resistant supply chains")
        if loc_years > 5:
            recommendations.append("Establish international partnerships for technology transfer")
        recommendations.append("Build strategic inventory reserves")
        recommendations.append("Support talent development programs")

        return TechDependencyAnalysis(
            tech_id=tech_id,
            tech_name=tech_info["name"],
            tech_name_cn=tech_info["name_cn"],
            category=tech_info["category"].value if isinstance(tech_info["category"], Enum) else tech_info["category"],
            current_dependency_pct=foreign_dep,
            domestic_capability_pct=domestic_cap,
            primary_foreign_sources=sources,
            supply_chain_risk=supply_risk.value,
            sanctions_vulnerability=sanctions_exp,
            localization_status=loc_status.value,
            localization_timeline_years=loc_years,
            key_bottlenecks=bottlenecks,
            alternative_sources=alternatives,
            investment_required_billion_cny=round(investment, 1),
            strategic_importance="critical" if foreign_dep >= 70 else "high" if foreign_dep >= 40 else "moderate",
            recommendations=recommendations
        )

    async def get_innovation_project(self, project_id: str) -> InnovationProject:
        """
        Get details of an innovation project

        Args:
            project_id: Project identifier

        Returns:
            InnovationProject with project details
        """
        project_info = self._project_data.get(project_id)

        if not project_info:
            project_info = {
                "name": f"Project {project_id}",
                "name_cn": f"项目 {project_id}",
                "category": TechnologyCategory.SOFTWARE,
                "lead": "Research Institute",
                "budget": 50,
                "progress": 30,
                "status": "in_progress"
            }

        # Generate milestones
        milestones = [
            {
                "milestone": "Feasibility Study",
                "target_date": "2024-Q2",
                "status": "completed"
            },
            {
                "milestone": "Prototype Development",
                "target_date": "2025-Q2",
                "status": "in_progress" if project_info["progress"] >= 30 else "pending"
            },
            {
                "milestone": "Pilot Testing",
                "target_date": "2026-Q1",
                "status": "in_progress" if project_info["progress"] >= 60 else "pending"
            },
            {
                "milestone": "Mass Production",
                "target_date": "2027-Q1",
                "status": "completed" if project_info["progress"] >= 90 else "pending"
            }
        ]

        # Expected outcomes
        outcomes = [
            f"Reduce foreign dependency by {random.randint(15, 40)}%",
            "Establish domestic supply chain",
            "Create 5,000+ high-tech jobs",
            "Generate technology IP portfolio"
        ]

        return InnovationProject(
            project_id=project_id,
            project_name=project_info["name"],
            project_name_cn=project_info["name_cn"],
            category=project_info["category"].value if isinstance(project_info["category"], Enum) else project_info["category"],
            description=f"Strategic project to develop domestic capability in {project_info['name']}",
            lead_organization=project_info["lead"],
            start_date="2023-01-01",
            target_completion="2027-12-31",
            budget_billion_cny=project_info["budget"],
            progress_pct=project_info["progress"],
            status=project_info["status"],
            key_milestones=milestones,
            expected_outcomes=outcomes,
            commercialization_potential="high" if project_info["progress"] >= 50 else "medium"
        )

    async def get_sector_overview(self) -> Dict[str, Any]:
        """Get overview of technology sector resilience"""
        categories = {}

        for tech_id, tech_info in self._tech_data.items():
            cat = tech_info["category"].value if isinstance(tech_info["category"], Enum) else tech_info["category"]
            if cat not in categories:
                categories[cat] = {
                    "technologies": [],
                    "avg_dependency": 0,
                    "avg_capability": 0
                }
            categories[cat]["technologies"].append(tech_id)
            categories[cat]["avg_dependency"] += tech_info["foreign_dependency"]
            categories[cat]["avg_capability"] += tech_info["domestic_capability"]

        # Calculate averages
        for cat in categories:
            count = len(categories[cat]["technologies"])
            categories[cat]["avg_dependency"] = round(categories[cat]["avg_dependency"] / count, 1)
            categories[cat]["avg_capability"] = round(categories[cat]["avg_capability"] / count, 1)

        total_dep = sum(t["foreign_dependency"] for t in self._tech_data.values()) / len(self._tech_data)
        total_cap = sum(t["domestic_capability"] for t in self._tech_data.values()) / len(self._tech_data)

        return {
            "analysis_date": datetime.now().isoformat(),
            "technologies_monitored": len(self._tech_data),
            "active_projects": len(self._project_data),
            "overall_metrics": {
                "average_foreign_dependency": round(total_dep, 1),
                "average_domestic_capability": round(total_cap, 1),
                "self_reliance_score": round(total_cap, 1)
            },
            "categories": categories,
            "critical_gaps": [
                "Advanced semiconductor manufacturing",
                "EDA software tools",
                "High-end AI accelerators",
                "Aircraft engines"
            ],
            "progress_highlights": [
                "5G network equipment fully localized",
                "AI frameworks achieving global competitiveness",
                "Quantum computing advancing rapidly",
                "Legacy semiconductors self-sufficient"
            ],
            "strategic_priorities": [
                "Accelerate semiconductor equipment development",
                "Expand AI chip ecosystem",
                "Strengthen EDA tool capabilities",
                "Build aerospace engine expertise"
            ]
        }
