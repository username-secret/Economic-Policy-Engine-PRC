-- Economic Policy Engine Database Initialization
-- Supports PRC and Russian Federation government data management
-- Version: 2.0.0

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE jurisdiction_type AS ENUM ('PRC', 'RU', 'INT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE classification_type AS ENUM ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'SECRET');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role_type AS ENUM ('system_admin', 'data_analyst', 'policy_maker', 'auditor', 'read_only');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Economic Indicators Table
CREATE TABLE IF NOT EXISTS economic_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_code VARCHAR(2) NOT NULL,
    indicator_type VARCHAR(100) NOT NULL,
    region_code VARCHAR(20),
    period DATE NOT NULL,
    value NUMERIC(20, 4) NOT NULL,
    unit VARCHAR(50),
    source VARCHAR(200) NOT NULL,
    source_indicator_code VARCHAR(50),
    is_official BOOLEAN DEFAULT TRUE,
    is_estimated BOOLEAN DEFAULT FALSE,
    confidence_level FLOAT,
    revision_number INTEGER DEFAULT 0,
    metadata JSONB,
    raw_data JSONB,
    jurisdiction jurisdiction_type DEFAULT 'PRC',
    classification classification_type DEFAULT 'INTERNAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_economic_indicator UNIQUE (country_code, indicator_type, region_code, period, source, revision_number)
);

-- Trade Flows Table
CREATE TABLE IF NOT EXISTS trade_flows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_country VARCHAR(2) NOT NULL,
    destination_country VARCHAR(2) NOT NULL,
    product_category VARCHAR(20) NOT NULL,
    hs_code VARCHAR(10),
    hs_description VARCHAR(500),
    trade_value_usd NUMERIC(20, 2),
    trade_value_local NUMERIC(20, 2),
    local_currency VARCHAR(3),
    volume_tons NUMERIC(20, 2),
    volume_units NUMERIC(20, 2),
    period DATE NOT NULL,
    growth_yoy NUMERIC(10, 4),
    growth_mom NUMERIC(10, 4),
    tariff_rate NUMERIC(6, 4),
    barriers JSONB,
    sanctions_affected BOOLEAN DEFAULT FALSE,
    source VARCHAR(200),
    metadata JSONB,
    jurisdiction jurisdiction_type DEFAULT 'PRC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Property Markets Table (PRC)
CREATE TABLE IF NOT EXISTS property_markets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_code VARCHAR(20) NOT NULL,
    region_name VARCHAR(100),
    region_name_en VARCHAR(100),
    property_type VARCHAR(50) NOT NULL,
    period DATE NOT NULL,
    price_index NUMERIC(10, 2),
    price_per_sqm NUMERIC(12, 2),
    volume_index NUMERIC(10, 2),
    transaction_volume NUMERIC(15, 2),
    vacancy_rate NUMERIC(5, 2),
    rental_yield NUMERIC(5, 2),
    debt_to_value NUMERIC(5, 2),
    affordability_index NUMERIC(10, 2),
    stability_score NUMERIC(5, 2),
    risk_level VARCHAR(20),
    intervention_recommended BOOLEAN DEFAULT FALSE,
    intervention_type VARCHAR(100),
    developer_health JSONB,
    metadata JSONB,
    source VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- National Projects Table (Russia)
CREATE TABLE IF NOT EXISTS national_projects (
    id VARCHAR(50) PRIMARY KEY,
    name_ru VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    description TEXT,
    start_date DATE,
    end_date DATE,
    budget_total_trillion_rub NUMERIC(10, 2),
    budget_spent_trillion_rub NUMERIC(10, 2),
    budget_remaining_trillion_rub NUMERIC(10, 2),
    completion_rate NUMERIC(5, 2),
    on_track BOOLEAN,
    status VARCHAR(50),
    delay_months INTEGER DEFAULT 0,
    key_metrics JSONB,
    targets JSONB,
    challenges JSONB,
    responsible_ministry VARCHAR(200),
    federal_projects JSONB,
    latest_assessment TEXT,
    last_updated TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- S&T Programs Table (Russia)
CREATE TABLE IF NOT EXISTS st_programs (
    id VARCHAR(50) PRIMARY KEY,
    name_ru VARCHAR(200) NOT NULL,
    name_en VARCHAR(200),
    sector VARCHAR(100),
    description TEXT,
    start_year INTEGER,
    target_year INTEGER,
    budget_billion_rub NUMERIC(12, 2),
    status VARCHAR(50),
    completion_rate NUMERIC(5, 2),
    global_ranking INTEGER,
    gap_to_leader_years INTEGER,
    key_challenges JSONB,
    sanctions_impact VARCHAR(50),
    brain_drain_impact VARCHAR(50),
    technology_access VARCHAR(50),
    infrastructure_status VARCHAR(50),
    key_achievements JSONB,
    failures JSONB,
    recovery_outlook VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- FYP Targets Table (PRC 15th Five-Year Plan)
CREATE TABLE IF NOT EXISTS fyp_targets (
    id VARCHAR(50) PRIMARY KEY,
    fyp_number INTEGER NOT NULL DEFAULT 15,
    priority_area VARCHAR(100) NOT NULL,
    target_name_cn VARCHAR(500) NOT NULL,
    target_name_en VARCHAR(500),
    category VARCHAR(100),
    is_binding BOOLEAN DEFAULT FALSE,
    baseline_year INTEGER,
    baseline_value NUMERIC(20, 4),
    target_year INTEGER,
    target_value NUMERIC(20, 4),
    unit VARCHAR(50),
    current_value NUMERIC(20, 4),
    current_year INTEGER,
    progress_pct NUMERIC(5, 2),
    on_track BOOLEAN,
    trend VARCHAR(20),
    last_assessment TEXT,
    responsible_ministry VARCHAR(200),
    related_policies JSONB,
    regional_breakdown JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    role user_role_type DEFAULT 'read_only',
    jurisdiction jurisdiction_type DEFAULT 'PRC',
    organization VARCHAR(200),
    organization_code VARCHAR(50),
    department VARCHAR(200),
    title VARCHAR(100),
    permissions TEXT[],
    mfa_enabled BOOLEAN DEFAULT TRUE,
    mfa_secret VARCHAR(255),
    external_id VARCHAR(255),
    external_provider VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    lock_reason VARCHAR(255),
    failed_login_attempts INTEGER DEFAULT 0,
    last_login TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    password_changed_at TIMESTAMP WITH TIME ZONE,
    session_token VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Log Table (Immutable)
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    action VARCHAR(50) NOT NULL,
    outcome VARCHAR(20) NOT NULL,
    severity VARCHAR(20) DEFAULT 'INFO',
    user_id UUID,
    username VARCHAR(100),
    user_role VARCHAR(50),
    session_id VARCHAR(100),
    request_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    http_method VARCHAR(10),
    endpoint VARCHAR(500),
    query_params JSONB,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    resource_name VARCHAR(500),
    description TEXT,
    details JSONB,
    old_value JSONB,
    new_value JSONB,
    response_code INTEGER,
    response_time_ms FLOAT,
    error_code VARCHAR(50),
    error_message TEXT,
    jurisdiction jurisdiction_type DEFAULT 'PRC',
    data_classification classification_type DEFAULT 'INTERNAL',
    compliance_tags TEXT[],
    checksum VARCHAR(64)
);

-- Data Ingestion Log Table
CREATE TABLE IF NOT EXISTS data_ingestion_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_name VARCHAR(200) NOT NULL,
    source_endpoint VARCHAR(500),
    data_type VARCHAR(100) NOT NULL,
    jurisdiction jurisdiction_type NOT NULL,
    operation VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    records_fetched INTEGER DEFAULT 0,
    records_stored INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    bytes_transferred INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms FLOAT,
    error_code VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    request_params JSONB,
    response_metadata JSONB,
    data_period_start DATE,
    data_period_end DATE
);

-- Crisis Indicators Table (Russia)
CREATE TABLE IF NOT EXISTS crisis_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_name VARCHAR(100) NOT NULL,
    indicator_name_ru VARCHAR(100),
    category VARCHAR(50) NOT NULL,
    period DATE NOT NULL,
    official_value NUMERIC(20, 4),
    estimated_value NUMERIC(20, 4),
    estimation_source VARCHAR(200),
    discrepancy_pct NUMERIC(10, 4),
    severity_level VARCHAR(20),
    trend VARCHAR(20),
    yoy_change NUMERIC(10, 4),
    mom_change NUMERIC(10, 4),
    threshold_warning NUMERIC(20, 4),
    threshold_critical NUMERIC(20, 4),
    is_above_threshold BOOLEAN DEFAULT FALSE,
    analysis_notes TEXT,
    data_quality VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Policy Recommendations Table
CREATE TABLE IF NOT EXISTS policy_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction jurisdiction_type NOT NULL,
    policy_area VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_local VARCHAR(500),
    description TEXT,
    description_local TEXT,
    priority VARCHAR(20),
    urgency VARCHAR(20),
    impact_assessment JSONB,
    implementation_steps JSONB,
    resource_requirements JSONB,
    risk_factors JSONB,
    success_metrics JSONB,
    related_indicators TEXT[],
    related_projects TEXT[],
    generated_by VARCHAR(100),
    confidence_score NUMERIC(5, 2),
    status VARCHAR(50) DEFAULT 'draft',
    reviewed_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Indexes
CREATE INDEX IF NOT EXISTS idx_economic_indicators_country_period ON economic_indicators(country_code, period);
CREATE INDEX IF NOT EXISTS idx_economic_indicators_type ON economic_indicators(indicator_type);
CREATE INDEX IF NOT EXISTS idx_economic_indicators_jurisdiction ON economic_indicators(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_economic_indicators_source ON economic_indicators(source);

CREATE INDEX IF NOT EXISTS idx_trade_flows_origin_dest ON trade_flows(origin_country, destination_country);
CREATE INDEX IF NOT EXISTS idx_trade_flows_period ON trade_flows(period);
CREATE INDEX IF NOT EXISTS idx_trade_flows_hs ON trade_flows(hs_code);
CREATE INDEX IF NOT EXISTS idx_trade_flows_sanctions ON trade_flows(sanctions_affected) WHERE sanctions_affected = TRUE;

CREATE INDEX IF NOT EXISTS idx_property_markets_region ON property_markets(region_code, period);
CREATE INDEX IF NOT EXISTS idx_property_markets_type ON property_markets(property_type);
CREATE INDEX IF NOT EXISTS idx_property_markets_risk ON property_markets(risk_level);

CREATE INDEX IF NOT EXISTS idx_national_projects_status ON national_projects(status);
CREATE INDEX IF NOT EXISTS idx_st_programs_sector ON st_programs(sector);

CREATE INDEX IF NOT EXISTS idx_fyp_targets_area ON fyp_targets(priority_area);
CREATE INDEX IF NOT EXISTS idx_fyp_targets_fyp ON fyp_targets(fyp_number);
CREATE INDEX IF NOT EXISTS idx_fyp_targets_binding ON fyp_targets(is_binding) WHERE is_binding = TRUE;

CREATE INDEX IF NOT EXISTS idx_users_jurisdiction ON users(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_external ON users(external_provider, external_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_jurisdiction ON audit_log(jurisdiction);

CREATE INDEX IF NOT EXISTS idx_ingestion_log_source ON data_ingestion_log(source_name);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_status ON data_ingestion_log(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_jurisdiction ON data_ingestion_log(jurisdiction);

CREATE INDEX IF NOT EXISTS idx_crisis_indicators_period ON crisis_indicators(period);
CREATE INDEX IF NOT EXISTS idx_crisis_indicators_category ON crisis_indicators(category);
CREATE INDEX IF NOT EXISTS idx_crisis_indicators_severity ON crisis_indicators(severity_level);

CREATE INDEX IF NOT EXISTS idx_policy_recommendations_jurisdiction ON policy_recommendations(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_policy_recommendations_area ON policy_recommendations(policy_area);
CREATE INDEX IF NOT EXISTS idx_policy_recommendations_status ON policy_recommendations(status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
DROP TRIGGER IF EXISTS update_economic_indicators_updated_at ON economic_indicators;
CREATE TRIGGER update_economic_indicators_updated_at
    BEFORE UPDATE ON economic_indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_national_projects_updated_at ON national_projects;
CREATE TRIGGER update_national_projects_updated_at
    BEFORE UPDATE ON national_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_st_programs_updated_at ON st_programs;
CREATE TRIGGER update_st_programs_updated_at
    BEFORE UPDATE ON st_programs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_fyp_targets_updated_at ON fyp_targets;
CREATE TRIGGER update_fyp_targets_updated_at
    BEFORE UPDATE ON fyp_targets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_policy_recommendations_updated_at ON policy_recommendations;
CREATE TRIGGER update_policy_recommendations_updated_at
    BEFORE UPDATE ON policy_recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit log protection (prevent updates/deletes)
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log records cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS protect_audit_log ON audit_log;
CREATE TRIGGER protect_audit_log
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- Insert initial system user
INSERT INTO users (id, username, email, role, jurisdiction, organization, is_active, mfa_enabled)
VALUES (
    uuid_generate_v4(),
    'system',
    'system@economic-engine.gov',
    'system_admin',
    'PRC',
    'System',
    TRUE,
    FALSE
) ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO economic_engine_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO economic_engine_app;
GRANT SELECT ON audit_log TO economic_engine_app;  -- Read-only for audit log

-- Create read-only role for analysts
DO $$ BEGIN
    CREATE ROLE economic_engine_analyst;
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

GRANT SELECT ON economic_indicators, trade_flows, property_markets,
    national_projects, st_programs, fyp_targets, crisis_indicators,
    policy_recommendations TO economic_engine_analyst;

-- Create audit role
DO $$ BEGIN
    CREATE ROLE economic_engine_auditor;
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO economic_engine_auditor;

COMMENT ON DATABASE economic_engine IS 'Economic Policy Engine - Government economic analysis platform for PRC and Russian Federation';
