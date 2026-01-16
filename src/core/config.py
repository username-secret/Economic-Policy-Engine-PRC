"""
Configuration module for Economic Policy Engine
Supports PRC and Russian Federation government system integration
"""

from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from typing import Optional, List, Dict, Any
from enum import Enum
from functools import lru_cache
import os


class Jurisdiction(str, Enum):
    """Supported jurisdictions"""
    PRC = "PRC"
    RUSSIA = "RU"
    INTERNATIONAL = "INT"


class EncryptionStandard(str, Enum):
    """Supported encryption standards"""
    SM4 = "SM4"  # PRC GB/T 32907-2016
    SM2 = "SM2"  # PRC GB/T 32918
    SM3 = "SM3"  # PRC GB/T 32905-2016
    GOST_KUZNYECHIK = "GOST_KUZNYECHIK"  # Russia GOST R 34.12-2015
    GOST_MAGMA = "GOST_MAGMA"  # Russia GOST R 34.12-2015
    GOST_STREEBOG = "GOST_STREEBOG"  # Russia GOST R 34.11-2012
    AES_256_GCM = "AES_256_GCM"  # International FIPS 197


class DataClassification(str, Enum):
    """Data classification levels"""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"


class PRCDataSourceConfig:
    """Configuration for PRC government data sources"""

    NATIONAL_BUREAU_STATISTICS = {
        "name": "国家统计局",
        "name_en": "National Bureau of Statistics",
        "endpoint": "https://data.stats.gov.cn/api/v1",
        "auth_type": "api_key",
        "data_types": ["gdp", "cpi", "ppi", "industrial_output", "retail_sales",
                       "fixed_investment", "unemployment", "population"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    CUSTOMS_ADMINISTRATION = {
        "name": "海关总署",
        "name_en": "General Administration of Customs",
        "endpoint": "https://www.customs.gov.cn/api/v1",
        "auth_type": "certificate",
        "data_types": ["import_export", "trade_balance", "tariff_data",
                       "customs_revenue", "trade_partners"],
        "update_frequency": "daily",
        "format": "json",
        "timeout": 60,
        "retry_attempts": 3
    }

    PEOPLES_BANK = {
        "name": "中国人民银行",
        "name_en": "People's Bank of China",
        "endpoint": "https://www.pbc.gov.cn/api/v1",
        "auth_type": "certificate",
        "data_types": ["monetary_policy", "interest_rates", "forex_rates",
                       "m2_supply", "loan_data", "deposit_rates"],
        "update_frequency": "daily",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    NDRC = {
        "name": "国家发展和改革委员会",
        "name_en": "National Development and Reform Commission",
        "endpoint": "https://www.ndrc.gov.cn/api/v1",
        "auth_type": "oauth2",
        "data_types": ["price_indices", "investment_data", "project_approvals",
                       "energy_consumption", "fyp_targets", "industrial_policy"],
        "update_frequency": "weekly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    MINISTRY_FINANCE = {
        "name": "财政部",
        "name_en": "Ministry of Finance",
        "endpoint": "https://www.mof.gov.cn/api/v1",
        "auth_type": "certificate",
        "data_types": ["fiscal_revenue", "fiscal_expenditure", "government_debt",
                       "budget_execution", "transfer_payments", "tax_revenue"],
        "update_frequency": "monthly",
        "format": "xml",
        "timeout": 30,
        "retry_attempts": 3
    }

    SAFE = {
        "name": "国家外汇管理局",
        "name_en": "State Administration of Foreign Exchange",
        "endpoint": "https://www.safe.gov.cn/api/v1",
        "auth_type": "certificate",
        "data_types": ["forex_reserves", "balance_payments", "external_debt",
                       "fdi_data", "odi_data", "cross_border_flows"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    MIIT = {
        "name": "工业和信息化部",
        "name_en": "Ministry of Industry and Information Technology",
        "endpoint": "https://www.miit.gov.cn/api/v1",
        "auth_type": "oauth2",
        "data_types": ["industrial_output", "tech_investment", "telecom_data",
                       "manufacturing_pmi", "software_revenue", "5g_deployment"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    MOFCOM = {
        "name": "商务部",
        "name_en": "Ministry of Commerce",
        "endpoint": "https://www.mofcom.gov.cn/api/v1",
        "auth_type": "oauth2",
        "data_types": ["foreign_trade", "fdi_utilization", "retail_data",
                       "ecommerce_stats", "service_trade", "trade_agreements"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    @classmethod
    def get_all_sources(cls) -> Dict[str, Dict]:
        """Get all PRC data source configurations"""
        return {
            "national_bureau_statistics": cls.NATIONAL_BUREAU_STATISTICS,
            "customs_administration": cls.CUSTOMS_ADMINISTRATION,
            "peoples_bank": cls.PEOPLES_BANK,
            "ndrc": cls.NDRC,
            "ministry_finance": cls.MINISTRY_FINANCE,
            "safe": cls.SAFE,
            "miit": cls.MIIT,
            "mofcom": cls.MOFCOM,
        }


class RussiaDataSourceConfig:
    """Configuration for Russian Federation government data sources"""

    ROSSTAT = {
        "name": "Федеральная служба государственной статистики",
        "name_en": "Federal State Statistics Service",
        "endpoint": "https://rosstat.gov.ru/api/v1",
        "auth_type": "api_key",
        "data_types": ["gdp", "inflation", "unemployment", "industrial_production",
                       "retail_sales", "construction", "agriculture", "demographics"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    CENTRAL_BANK = {
        "name": "Центральный банк Российской Федерации",
        "name_en": "Central Bank of Russia",
        "endpoint": "https://cbr.ru/api/v1",
        "auth_type": "open",
        "data_types": ["key_rate", "forex_rates", "monetary_base", "banking_stats",
                       "inflation_expectations", "credit_data", "reserves"],
        "update_frequency": "daily",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    MINISTRY_FINANCE = {
        "name": "Министерство финансов",
        "name_en": "Ministry of Finance",
        "endpoint": "https://minfin.gov.ru/api/v1",
        "auth_type": "certificate",
        "data_types": ["federal_budget", "nwf_status", "government_debt",
                       "budget_execution", "tax_revenue", "expenditure"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    MINISTRY_ECONOMY = {
        "name": "Министерство экономического развития",
        "name_en": "Ministry of Economic Development",
        "endpoint": "https://economy.gov.ru/api/v1",
        "auth_type": "oauth2",
        "data_types": ["economic_forecasts", "national_projects", "investment_data",
                       "gdp_forecasts", "inflation_forecasts", "sez_data"],
        "update_frequency": "quarterly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    FEDERAL_TREASURY = {
        "name": "Федеральное казначейство",
        "name_en": "Federal Treasury",
        "endpoint": "https://roskazna.gov.ru/api/v1",
        "auth_type": "certificate",
        "data_types": ["budget_execution", "interbudgetary_transfers",
                       "government_contracts", "public_debt_service"],
        "update_frequency": "monthly",
        "format": "xml",
        "timeout": 30,
        "retry_attempts": 3
    }

    FTS_CUSTOMS = {
        "name": "Федеральная таможенная служба",
        "name_en": "Federal Customs Service",
        "endpoint": "https://customs.gov.ru/api/v1",
        "auth_type": "certificate",
        "data_types": ["import_export", "customs_duties", "trade_statistics",
                       "transit_data", "sanctions_enforcement"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    MINPROMTORG = {
        "name": "Министерство промышленности и торговли",
        "name_en": "Ministry of Industry and Trade",
        "endpoint": "https://minpromtorg.gov.ru/api/v1",
        "auth_type": "oauth2",
        "data_types": ["industrial_production", "defense_industry",
                       "import_substitution", "manufacturing_data"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    MINTSIFRY = {
        "name": "Министерство цифрового развития",
        "name_en": "Ministry of Digital Development",
        "endpoint": "https://digital.gov.ru/api/v1",
        "auth_type": "oauth2",
        "data_types": ["digital_economy", "it_industry", "telecom_stats",
                       "egovernment", "cybersecurity"],
        "update_frequency": "monthly",
        "format": "json",
        "timeout": 30,
        "retry_attempts": 3
    }

    @classmethod
    def get_all_sources(cls) -> Dict[str, Dict]:
        """Get all Russia data source configurations"""
        return {
            "rosstat": cls.ROSSTAT,
            "central_bank": cls.CENTRAL_BANK,
            "ministry_finance": cls.MINISTRY_FINANCE,
            "ministry_economy": cls.MINISTRY_ECONOMY,
            "federal_treasury": cls.FEDERAL_TREASURY,
            "fts_customs": cls.FTS_CUSTOMS,
            "minpromtorg": cls.MINPROMTORG,
            "mintsifry": cls.MINTSIFRY,
        }


class Settings(BaseSettings):
    """
    Application settings with support for PRC and Russian Federation government integration
    """

    # Application Settings
    app_name: str = "Economic Policy Engine"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "production"

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_prefix: str = "/api/v1"

    # Database Settings
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/economic_engine",
        description="PostgreSQL connection URL"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_max_connections: int = 100

    # Security Settings
    jwt_secret: SecretStr = Field(
        default="change-me-in-production",
        description="JWT secret key"
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Encryption Settings - PRC (SM Algorithms)
    sm4_key: Optional[SecretStr] = Field(
        default=None,
        description="SM4 encryption key (128-bit) for PRC"
    )
    sm2_private_key_path: Optional[str] = Field(
        default=None,
        description="Path to SM2 private key for PRC"
    )
    sm2_public_key_path: Optional[str] = Field(
        default=None,
        description="Path to SM2 public key for PRC"
    )

    # Encryption Settings - Russia (GOST Algorithms)
    gost_key: Optional[SecretStr] = Field(
        default=None,
        description="GOST encryption key (256-bit) for Russia"
    )
    gost_private_key_path: Optional[str] = Field(
        default=None,
        description="Path to GOST private key for Russia"
    )
    gost_public_key_path: Optional[str] = Field(
        default=None,
        description="Path to GOST public key for Russia"
    )

    # Authentication - PRC
    prc_idp_enabled: bool = Field(
        default=False,
        description="Enable PRC Unified Identity Platform integration"
    )
    prc_idp_url: Optional[str] = Field(
        default=None,
        description="PRC 统一身份认证平台 URL"
    )
    prc_idp_client_id: Optional[str] = None
    prc_idp_client_secret: Optional[SecretStr] = None

    # Authentication - Russia
    esia_enabled: bool = Field(
        default=False,
        description="Enable ESIA (ЕСИА) integration for Russia"
    )
    esia_url: Optional[str] = Field(
        default=None,
        description="ESIA (ЕСИА) URL"
    )
    esia_client_id: Optional[str] = None
    esia_client_secret: Optional[SecretStr] = None

    # Jurisdiction Settings
    primary_jurisdiction: Jurisdiction = Jurisdiction.PRC
    enabled_jurisdictions: List[Jurisdiction] = [Jurisdiction.PRC, Jurisdiction.RUSSIA]

    # Data Sovereignty - PRC
    prc_data_region: str = "cn-beijing"
    prc_backup_region: str = "cn-shanghai"
    prc_dr_region: str = "cn-shenzhen"

    # Data Sovereignty - Russia
    russia_data_region: str = "ru-moscow"
    russia_backup_region: str = "ru-spb"
    russia_dr_region: str = "ru-kazan"

    # Audit Settings
    audit_enabled: bool = True
    audit_retention_days: int = 3650  # 10 years, effectively permanent
    audit_log_path: str = "/var/log/economic-engine/audit"

    # Monitoring Settings
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    grafana_enabled: bool = True
    grafana_port: int = 3000
    sentry_dsn: Optional[str] = None

    # Feature Flags
    enable_china_module: bool = True
    enable_russia_module: bool = True
    enable_ml_training: bool = True
    enable_async_tasks: bool = True
    enable_blockchain_audit: bool = False

    # Rate Limiting
    rate_limit_requests_per_minute: int = 1000
    rate_limit_burst_size: int = 100

    # Data Source API Keys (encrypted in production)
    nbs_api_key: Optional[SecretStr] = None  # 国家统计局
    rosstat_api_key: Optional[SecretStr] = None  # Росстат

    # TLS Settings
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    tls_ca_path: Optional[str] = None

    # CORS Settings
    cors_allowed_origins: List[str] = ["*.gov.cn", "*.gov.ru"]
    cors_allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    cors_max_age: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_prc_data_sources(self) -> Dict[str, Dict]:
        """Get all configured PRC data sources"""
        return PRCDataSourceConfig.get_all_sources()

    def get_russia_data_sources(self) -> Dict[str, Dict]:
        """Get all configured Russia data sources"""
        return RussiaDataSourceConfig.get_all_sources()

    def get_encryption_standard(self, jurisdiction: Jurisdiction) -> EncryptionStandard:
        """Get the appropriate encryption standard for a jurisdiction"""
        if jurisdiction == Jurisdiction.PRC:
            return EncryptionStandard.SM4
        elif jurisdiction == Jurisdiction.RUSSIA:
            return EncryptionStandard.GOST_KUZNYECHIK
        else:
            return EncryptionStandard.AES_256_GCM


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
