"""
Database models for Economic Policy Engine
SQLAlchemy ORM models for all data entities
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Index, Text, Enum as SQLEnum, JSON,
    UniqueConstraint, CheckConstraint, Numeric, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid
import enum


Base = declarative_base()


class Jurisdiction(str, enum.Enum):
    """Jurisdiction enum for data sovereignty"""
    PRC = "PRC"
    RU = "RU"
    INTERNATIONAL = "INT"


class DataClassification(str, enum.Enum):
    """Data classification levels"""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"


class UserRole(str, enum.Enum):
    """User roles"""
    SYSTEM_ADMIN = "system_admin"
    DATA_ANALYST = "data_analyst"
    POLICY_MAKER = "policy_maker"
    AUDITOR = "auditor"
    READ_ONLY = "read_only"


class EconomicIndicator(Base):
    """
    Economic indicators from various sources
    Supports both PRC and Russian data
    """
    __tablename__ = "economic_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_code = Column(String(2), nullable=False, index=True)
    indicator_type = Column(String(100), nullable=False, index=True)
    region_code = Column(String(20), index=True)
    period = Column(Date, nullable=False, index=True)
    value = Column(Numeric(20, 4), nullable=False)
    unit = Column(String(50))
    source = Column(String(200), nullable=False)
    source_indicator_code = Column(String(50))
    is_official = Column(Boolean, default=True)
    is_estimated = Column(Boolean, default=False)
    confidence_level = Column(Float)
    revision_number = Column(Integer, default=0)
    metadata = Column(JSONB)
    raw_data = Column(JSONB)
    jurisdiction = Column(SQLEnum(Jurisdiction), default=Jurisdiction.PRC)
    classification = Column(SQLEnum(DataClassification), default=DataClassification.INTERNAL)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('country_code', 'indicator_type', 'region_code',
                         'period', 'source', 'revision_number',
                         name='uq_economic_indicator'),
        Index('idx_economic_indicators_country_period', 'country_code', 'period'),
        Index('idx_economic_indicators_type', 'indicator_type'),
        Index('idx_economic_indicators_jurisdiction', 'jurisdiction'),
    )


class TradeFlow(Base):
    """
    International trade flow data
    Supports bilateral trade analysis
    """
    __tablename__ = "trade_flows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_country = Column(String(2), nullable=False, index=True)
    destination_country = Column(String(2), nullable=False, index=True)
    product_category = Column(String(20), nullable=False)
    hs_code = Column(String(10))
    hs_description = Column(String(500))
    trade_value_usd = Column(Numeric(20, 2))
    trade_value_local = Column(Numeric(20, 2))
    local_currency = Column(String(3))
    volume_tons = Column(Numeric(20, 2))
    volume_units = Column(Numeric(20, 2))
    period = Column(Date, nullable=False, index=True)
    growth_yoy = Column(Numeric(10, 4))
    growth_mom = Column(Numeric(10, 4))
    tariff_rate = Column(Numeric(6, 4))
    barriers = Column(JSONB)
    sanctions_affected = Column(Boolean, default=False)
    source = Column(String(200))
    metadata = Column(JSONB)
    jurisdiction = Column(SQLEnum(Jurisdiction), default=Jurisdiction.PRC)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_trade_flows_origin_dest', 'origin_country', 'destination_country'),
        Index('idx_trade_flows_period', 'period'),
        Index('idx_trade_flows_hs', 'hs_code'),
    )


class PropertyMarket(Base):
    """
    Property market data for PRC regions
    Supports stability analysis and intervention planning
    """
    __tablename__ = "property_markets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_code = Column(String(20), nullable=False, index=True)
    region_name = Column(String(100))
    region_name_en = Column(String(100))
    property_type = Column(String(50), nullable=False)
    period = Column(Date, nullable=False, index=True)
    price_index = Column(Numeric(10, 2))
    price_per_sqm = Column(Numeric(12, 2))
    volume_index = Column(Numeric(10, 2))
    transaction_volume = Column(Numeric(15, 2))
    vacancy_rate = Column(Numeric(5, 2))
    rental_yield = Column(Numeric(5, 2))
    debt_to_value = Column(Numeric(5, 2))
    affordability_index = Column(Numeric(10, 2))
    stability_score = Column(Numeric(5, 2))
    risk_level = Column(String(20))
    intervention_recommended = Column(Boolean, default=False)
    intervention_type = Column(String(100))
    developer_health = Column(JSONB)
    metadata = Column(JSONB)
    source = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_property_markets_region', 'region_code', 'period'),
        Index('idx_property_markets_type', 'property_type'),
    )


class NationalProject(Base):
    """
    Russian National Projects tracking
    Monitors project status, budget, and completion
    """
    __tablename__ = "national_projects"

    id = Column(String(50), primary_key=True)  # e.g., NP-DEMOGRAPHY
    name_ru = Column(String(200), nullable=False)
    name_en = Column(String(200))
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    budget_total_trillion_rub = Column(Numeric(10, 2))
    budget_spent_trillion_rub = Column(Numeric(10, 2))
    budget_remaining_trillion_rub = Column(Numeric(10, 2))
    completion_rate = Column(Numeric(5, 2))
    on_track = Column(Boolean)
    status = Column(String(50))  # on_track, delayed, critical, suspended
    delay_months = Column(Integer, default=0)
    key_metrics = Column(JSONB)
    targets = Column(JSONB)
    challenges = Column(JSONB)
    responsible_ministry = Column(String(200))
    federal_projects = Column(JSONB)  # List of sub-projects
    latest_assessment = Column(Text)
    last_updated = Column(DateTime(timezone=True))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_national_projects_status', 'status'),
    )


class STProgram(Base):
    """
    Russian Science & Technology Programs
    Tracks S&T program status and failures
    """
    __tablename__ = "st_programs"

    id = Column(String(50), primary_key=True)  # e.g., ST-SPACE
    name_ru = Column(String(200), nullable=False)
    name_en = Column(String(200))
    sector = Column(String(100))
    description = Column(Text)
    start_year = Column(Integer)
    target_year = Column(Integer)
    budget_billion_rub = Column(Numeric(12, 2))
    status = Column(String(50))
    completion_rate = Column(Numeric(5, 2))
    global_ranking = Column(Integer)
    gap_to_leader_years = Column(Integer)
    key_challenges = Column(JSONB)
    sanctions_impact = Column(String(50))  # none, moderate, severe, critical
    brain_drain_impact = Column(String(50))
    technology_access = Column(String(50))
    infrastructure_status = Column(String(50))
    key_achievements = Column(JSONB)
    failures = Column(JSONB)
    recovery_outlook = Column(String(50))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FYPTarget(Base):
    """
    PRC Five-Year Plan Targets
    Tracks targets for 15th FYP (2026-2030)
    """
    __tablename__ = "fyp_targets"

    id = Column(String(50), primary_key=True)
    fyp_number = Column(Integer, nullable=False, default=15)
    priority_area = Column(String(100), nullable=False, index=True)
    target_name_cn = Column(String(500), nullable=False)
    target_name_en = Column(String(500))
    category = Column(String(100))
    is_binding = Column(Boolean, default=False)  # 约束性指标 vs 预期性指标
    baseline_year = Column(Integer)
    baseline_value = Column(Numeric(20, 4))
    target_year = Column(Integer)
    target_value = Column(Numeric(20, 4))
    unit = Column(String(50))
    current_value = Column(Numeric(20, 4))
    current_year = Column(Integer)
    progress_pct = Column(Numeric(5, 2))
    on_track = Column(Boolean)
    trend = Column(String(20))  # improving, stable, declining
    last_assessment = Column(Text)
    responsible_ministry = Column(String(200))
    related_policies = Column(JSONB)
    regional_breakdown = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_fyp_targets_area', 'priority_area'),
        Index('idx_fyp_targets_fyp', 'fyp_number'),
    )


class User(Base):
    """
    System users with role-based access
    Supports both PRC and Russian government users
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(SQLEnum(UserRole), default=UserRole.READ_ONLY)
    jurisdiction = Column(SQLEnum(Jurisdiction), default=Jurisdiction.PRC)
    organization = Column(String(200))
    organization_code = Column(String(50))
    department = Column(String(200))
    title = Column(String(100))
    permissions = Column(ARRAY(String))
    mfa_enabled = Column(Boolean, default=True)
    mfa_secret = Column(String(255))
    external_id = Column(String(255))  # ID from external IdP
    external_provider = Column(String(50))  # prc_idp, esia, etc.
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    lock_reason = Column(String(255))
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True))
    last_login_ip = Column(INET)
    password_changed_at = Column(DateTime(timezone=True))
    session_token = Column(String(255))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_users_jurisdiction', 'jurisdiction'),
        Index('idx_users_role', 'role'),
        Index('idx_users_external', 'external_provider', 'external_id'),
    )


class AuditLog(Base):
    """
    Comprehensive audit log for compliance
    Immutable record of all system actions
    """
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    action = Column(String(50), nullable=False, index=True)
    outcome = Column(String(20), nullable=False)  # SUCCESS, FAILURE, PARTIAL
    severity = Column(String(20), default="INFO")

    # User context
    user_id = Column(UUID(as_uuid=True), index=True)
    username = Column(String(100))
    user_role = Column(String(50))
    session_id = Column(String(100))

    # Request context
    request_id = Column(String(100), index=True)
    ip_address = Column(INET)
    user_agent = Column(Text)
    http_method = Column(String(10))
    endpoint = Column(String(500))
    query_params = Column(JSONB)

    # Resource context
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    resource_name = Column(String(500))

    # Event details
    description = Column(Text)
    details = Column(JSONB)
    old_value = Column(JSONB)
    new_value = Column(JSONB)

    # Response context
    response_code = Column(Integer)
    response_time_ms = Column(Float)
    error_code = Column(String(50))
    error_message = Column(Text)

    # Compliance
    jurisdiction = Column(SQLEnum(Jurisdiction), default=Jurisdiction.PRC)
    data_classification = Column(SQLEnum(DataClassification), default=DataClassification.INTERNAL)
    compliance_tags = Column(ARRAY(String))
    checksum = Column(String(64))  # SHA-256 for integrity

    __table_args__ = (
        Index('idx_audit_log_timestamp', 'timestamp'),
        Index('idx_audit_log_user', 'user_id'),
        Index('idx_audit_log_action', 'action'),
        Index('idx_audit_log_resource', 'resource_type', 'resource_id'),
    )


class DataIngestionLog(Base):
    """
    Log of data ingestion operations
    Tracks data fetches from government sources
    """
    __tablename__ = "data_ingestion_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    source_name = Column(String(200), nullable=False, index=True)
    source_endpoint = Column(String(500))
    data_type = Column(String(100), nullable=False)
    jurisdiction = Column(SQLEnum(Jurisdiction), nullable=False)

    # Operation details
    operation = Column(String(50))  # fetch, store, transform
    status = Column(String(20), nullable=False)  # success, failure, partial
    records_fetched = Column(Integer, default=0)
    records_stored = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    bytes_transferred = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Float)

    # Error tracking
    error_code = Column(String(50))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Metadata
    request_params = Column(JSONB)
    response_metadata = Column(JSONB)
    data_period_start = Column(Date)
    data_period_end = Column(Date)

    __table_args__ = (
        Index('idx_ingestion_log_source', 'source_name'),
        Index('idx_ingestion_log_status', 'status'),
        Index('idx_ingestion_log_jurisdiction', 'jurisdiction'),
    )


class CrisisIndicator(Base):
    """
    Russian economic crisis indicators
    Real-time tracking of crisis metrics
    """
    __tablename__ = "crisis_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_name = Column(String(100), nullable=False, index=True)
    indicator_name_ru = Column(String(100))
    category = Column(String(50), nullable=False)  # inflation, fiscal, monetary, labor
    period = Column(Date, nullable=False, index=True)
    official_value = Column(Numeric(20, 4))
    estimated_value = Column(Numeric(20, 4))
    estimation_source = Column(String(200))
    discrepancy_pct = Column(Numeric(10, 4))
    severity_level = Column(String(20))  # normal, elevated, high, critical
    trend = Column(String(20))  # improving, stable, worsening
    yoy_change = Column(Numeric(10, 4))
    mom_change = Column(Numeric(10, 4))
    threshold_warning = Column(Numeric(20, 4))
    threshold_critical = Column(Numeric(20, 4))
    is_above_threshold = Column(Boolean, default=False)
    analysis_notes = Column(Text)
    data_quality = Column(String(20))  # high, medium, low, unreliable
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_crisis_indicators_period', 'period'),
        Index('idx_crisis_indicators_category', 'category'),
        Index('idx_crisis_indicators_severity', 'severity_level'),
    )


class PolicyRecommendation(Base):
    """
    Policy recommendations generated by the system
    For both PRC and Russian contexts
    """
    __tablename__ = "policy_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jurisdiction = Column(SQLEnum(Jurisdiction), nullable=False)
    policy_area = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    title_local = Column(String(500))  # Chinese or Russian title
    description = Column(Text)
    description_local = Column(Text)
    priority = Column(String(20))  # low, medium, high, critical
    urgency = Column(String(20))  # immediate, short_term, medium_term, long_term
    impact_assessment = Column(JSONB)
    implementation_steps = Column(JSONB)
    resource_requirements = Column(JSONB)
    risk_factors = Column(JSONB)
    success_metrics = Column(JSONB)
    related_indicators = Column(ARRAY(String))
    related_projects = Column(ARRAY(String))
    generated_by = Column(String(100))  # model name or analyst
    confidence_score = Column(Numeric(5, 2))
    status = Column(String(50), default="draft")  # draft, review, approved, implemented
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_policy_recommendations_jurisdiction', 'jurisdiction'),
        Index('idx_policy_recommendations_area', 'policy_area'),
        Index('idx_policy_recommendations_status', 'status'),
    )
