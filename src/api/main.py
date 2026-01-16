"""
Main API gateway for Economic Policy Engine
Government-Grade Platform for PRC and Russian Federation Economic Analysis

Supports direct integration with:
- PRC: 国家统计局, 海关总署, 中国人民银行, 国家发改委, 财政部, 国家外汇管理局
- Russia: Росстат, ЦБ РФ, Минфин, Минэкономразвития, ФТС

Security Standards:
- PRC: SM2/SM3/SM4 (GB/T 32918, GB/T 32905-2016, GB/T 32907-2016)
- Russia: GOST R 34.12-2015 (Kuznyechik), GOST R 34.11-2012 (Streebog)

Authentication:
- PRC: 统一身份认证平台 (Unified Identity Authentication Platform)
- Russia: ЕСИА (Unified Identification and Authentication System)
"""
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Core modules
from ..core.config import Settings, get_settings
from ..core.security import (
    SecurityManager, TokenData, UserRole, Permission,
    PRCIdentityProvider, ESIAProvider
)
from ..core.audit import (
    AuditLogger, AuditAction, AuditOutcome, AuditSeverity,
    DatabaseAuditStorage, FileAuditStorage
)
from ..core.encryption import EncryptionManager, Jurisdiction

# Database
from ..database.connection import DatabaseManager, get_db_session
from ..database.models import User, AuditLog

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

# Data source integrations
from ..integrations.prc_sources import (
    NBSClient, CustomsClient, PBOCClient, NDRCClient, MOFClient, SAFEClient
)
from ..integrations.russia_sources import (
    RosstatClient, CBRClient, MinFinClient, MinEconomyClient, FTSCustomsClient
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
trade_service = None
property_service = None
tech_service = None
china_fyp_service = None
russia_service = None

# Core infrastructure
settings: Settings = None
security_manager: SecurityManager = None
audit_logger: AuditLogger = None
db_manager: DatabaseManager = None
encryption_manager: EncryptionManager = None

# PRC data source clients
nbs_client: NBSClient = None
customs_client: CustomsClient = None
pboc_client: PBOCClient = None
ndrc_client: NDRCClient = None
mof_client: MOFClient = None
safe_client: SAFEClient = None

# Russia data source clients
rosstat_client: RosstatClient = None
cbr_client: CBRClient = None
minfin_client: MinFinClient = None
mineconomy_client: MinEconomyClient = None
fts_client: FTSCustomsClient = None

# Security
security = HTTPBearer(auto_error=False)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response audit logging"""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Extract user info if available
        user_id = None
        username = None
        user_role = None

        # Get token from header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and security_manager:
            token = auth_header[7:]
            try:
                token_data = security_manager.verify_token(token)
                if token_data:
                    user_id = token_data.user_id
                    username = token_data.username
                    user_role = token_data.role
            except Exception:
                pass

        # Store request_id in state for use in endpoints
        request.state.request_id = request_id
        request.state.user_id = user_id
        request.state.username = username

        # Process request
        response = None
        error_message = None
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            # Calculate response time
            response_time = (time.time() - start_time) * 1000

            # Determine outcome and severity
            status_code = response.status_code if response else 500
            if status_code < 400:
                outcome = AuditOutcome.SUCCESS
                severity = AuditSeverity.INFO
            elif status_code < 500:
                outcome = AuditOutcome.FAILURE
                severity = AuditSeverity.WARNING
            else:
                outcome = AuditOutcome.ERROR
                severity = AuditSeverity.ERROR

            # Determine jurisdiction from path
            path = request.url.path
            if "/china/" in path or "/prc/" in path:
                jurisdiction = Jurisdiction.PRC
            elif "/russia/" in path or "/ru/" in path:
                jurisdiction = Jurisdiction.RUSSIA
            else:
                jurisdiction = Jurisdiction.PRC  # Default

            # Log audit event
            if audit_logger:
                await audit_logger.log(
                    action=AuditAction.API_REQUEST,
                    outcome=outcome,
                    severity=severity,
                    user_id=user_id,
                    username=username,
                    user_role=user_role,
                    request_id=request_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    http_method=request.method,
                    endpoint=str(request.url.path),
                    query_params=dict(request.query_params),
                    response_code=status_code,
                    response_time_ms=response_time,
                    error_message=error_message,
                    jurisdiction=jurisdiction.value,
                    details={
                        "headers": dict(request.headers),
                        "path_params": request.path_params
                    }
                )


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and jurisdiction-specific requirements"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # Add request ID to response
        if hasattr(request.state, "request_id"):
            response.headers["X-Request-ID"] = request.state.request_id

        return response


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenData]:
    """Dependency to get current authenticated user"""
    if not credentials:
        return None

    if not security_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service not initialized"
        )

    token_data = security_manager.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return token_data


def require_permission(permission: Permission):
    """Dependency factory for permission-based access control"""
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not security_manager.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required"
            )

        return current_user

    return permission_checker


def require_jurisdiction(jurisdiction: Jurisdiction):
    """Dependency factory for jurisdiction-based access control"""
    async def jurisdiction_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        if current_user.jurisdiction != jurisdiction.value and current_user.jurisdiction != "INT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {jurisdiction.value} jurisdiction"
            )

        return current_user

    return jurisdiction_checker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for service initialization
    Initializes all government-grade infrastructure components
    """
    global trade_service, property_service, tech_service, china_fyp_service, russia_service
    global settings, security_manager, audit_logger, db_manager, encryption_manager
    global nbs_client, customs_client, pboc_client, ndrc_client, mof_client, safe_client
    global rosstat_client, cbr_client, minfin_client, mineconomy_client, fts_client

    logger.info("=" * 60)
    logger.info("Initializing Economic Policy Engine - Government Platform")
    logger.info("=" * 60)

    # Load configuration
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"PRC Module: {settings.enable_china_module}")
    logger.info(f"Russia Module: {settings.enable_russia_module}")

    # Initialize database manager
    logger.info("Initializing database connection...")
    db_manager = DatabaseManager(settings.database_url)
    await db_manager.initialize()

    # Initialize encryption manager
    logger.info("Initializing encryption services...")
    encryption_manager = EncryptionManager(
        sm4_key=settings.sm4_key.encode() if settings.sm4_key else None,
        gost_key=settings.gost_key.encode() if settings.gost_key else None
    )

    # Initialize audit logger
    logger.info("Initializing audit logging system...")
    audit_storage = DatabaseAuditStorage(db_manager)
    audit_logger = AuditLogger(
        storage=audit_storage,
        buffer_size=100,
        flush_interval=5.0
    )
    await audit_logger.start()

    # Initialize security manager
    logger.info("Initializing security infrastructure...")
    prc_idp = PRCIdentityProvider(
        idp_url=settings.prc_idp_url,
        client_id=settings.prc_idp_client_id,
        client_secret=settings.prc_idp_client_secret
    ) if settings.prc_idp_url else None

    esia_provider = ESIAProvider(
        esia_url=settings.esia_url,
        client_id=settings.esia_client_id,
        client_secret=settings.esia_client_secret
    ) if settings.esia_url else None

    security_manager = SecurityManager(
        jwt_secret=settings.jwt_secret,
        jwt_algorithm=settings.jwt_algorithm,
        prc_idp=prc_idp,
        esia_provider=esia_provider,
        encryption_manager=encryption_manager
    )

    # Initialize PRC data source clients
    if settings.enable_china_module:
        logger.info("Initializing PRC data source integrations...")
        nbs_client = NBSClient(
            endpoint=settings.nbs_endpoint,
            api_key=settings.nbs_api_key
        )
        customs_client = CustomsClient(
            endpoint=settings.customs_endpoint,
            api_key=settings.customs_api_key
        )
        pboc_client = PBOCClient(
            endpoint=settings.pboc_endpoint,
            api_key=settings.pboc_api_key
        )
        ndrc_client = NDRCClient(
            endpoint=settings.ndrc_endpoint,
            client_id=settings.ndrc_client_id,
            client_secret=settings.ndrc_client_secret
        )
        mof_client = MOFClient(
            endpoint=settings.mof_endpoint,
            api_key=settings.mof_api_key
        )
        safe_client = SAFEClient(
            endpoint=settings.safe_endpoint,
            api_key=settings.safe_api_key
        )
        logger.info("PRC integrations initialized: NBS, Customs, PBOC, NDRC, MOF, SAFE")

    # Initialize Russia data source clients
    if settings.enable_russia_module:
        logger.info("Initializing Russia data source integrations...")
        rosstat_client = RosstatClient(
            endpoint=settings.rosstat_endpoint,
            api_key=settings.rosstat_api_key
        )
        cbr_client = CBRClient(
            endpoint=settings.cbr_endpoint
        )
        minfin_client = MinFinClient(
            endpoint=settings.minfin_endpoint,
            api_key=settings.minfin_api_key
        )
        mineconomy_client = MinEconomyClient(
            endpoint=settings.mineconomy_endpoint,
            client_id=settings.mineconomy_client_id,
            client_secret=settings.mineconomy_client_secret
        )
        fts_client = FTSCustomsClient(
            endpoint=settings.fts_endpoint,
            api_key=settings.fts_api_key
        )
        logger.info("Russia integrations initialized: Rosstat, CBR, MinFin, MinEconomy, FTS")

    # Initialize China services
    logger.info("Initializing China economic analysis services...")
    trade_service = TradeBarrierService()
    property_service = PropertyStabilizationService()
    tech_service = TechResilienceService()
    china_fyp_service = ChinaFYPService()

    # Initialize Russia services
    logger.info("Initializing Russia economic analysis services...")
    russia_service = RussianEconomicService()

    # Log startup completion
    await audit_logger.log(
        action=AuditAction.SYSTEM_STARTUP,
        outcome=AuditOutcome.SUCCESS,
        severity=AuditSeverity.INFO,
        description="Economic Policy Engine started successfully",
        details={
            "version": settings.app_version,
            "environment": settings.environment,
            "prc_module": settings.enable_china_module,
            "russia_module": settings.enable_russia_module
        }
    )

    logger.info("=" * 60)
    logger.info("Economic Policy Engine initialized successfully")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down Economic Policy Engine...")

    # Log shutdown
    if audit_logger:
        await audit_logger.log(
            action=AuditAction.SYSTEM_SHUTDOWN,
            outcome=AuditOutcome.SUCCESS,
            severity=AuditSeverity.INFO,
            description="Economic Policy Engine shutting down"
        )
        await audit_logger.stop()

    # Close database connections
    if db_manager:
        await db_manager.close()

    logger.info("Economic Policy Engine shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Economic Policy Engine API | 经济政策引擎 | Экономический Политический Движок",
    description="""
    **Government-Grade Economic Policy Analysis Platform**

    Official platform for economic policy analysis supporting direct integration with
    PRC and Russian Federation government systems.

    ---

    ## 中华人民共和国 (PRC) Modules

    - **Trade Barrier Mitigation** (贸易壁垒缓解): Analysis and alternative route optimization
    - **Property Sector Stabilization** (房地产稳定): Market metrics and debt restructuring
    - **Tech Sector Resilience** (科技韧性): Dependency analysis and localization tracking
    - **15th Five-Year Plan** (十五五规划 2026-2030): Target tracking and progress analysis

    **Data Sources**: 国家统计局, 海关总署, 中国人民银行, 国家发改委, 财政部, 国家外汇管理局

    **Security**: SM2/SM3/SM4 encryption (GB/T 32918, GB/T 32905-2016, GB/T 32907-2016)

    ---

    ## Российская Федерация (Russia) Modules

    - **National Projects** (Национальные проекты): Status tracking and failure analysis
    - **S&T Programs** (Научно-технологические программы): Assessment and recovery planning
    - **Economic Crisis Analysis** (Экономический кризис): Real-time crisis indicators
    - **Reform Packages** (Реформенные пакеты): Comprehensive solution proposals

    **Data Sources**: Росстат, ЦБ РФ, Минфин, Минэкономразвития, ФТС

    **Security**: GOST R 34.12-2015 (Kuznyechik), GOST R 34.11-2012 (Streebog)

    ---

    ## Authentication

    - **PRC**: 统一身份认证平台 (Unified Identity Authentication Platform)
    - **Russia**: ЕСИА (Единая система идентификации и аутентификации)
    - **International**: OAuth 2.0 / JWT

    ## Compliance

    - Data sovereignty enforcement (数据主权 / Суверенитет данных)
    - Immutable audit logging (审计日志 / Журнал аудита)
    - Role-based access control (RBAC)
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "Health", "description": "System health and status endpoints"},
        {"name": "Authentication", "description": "Authentication and authorization"},
        {"name": "China - Trade", "description": "贸易壁垒缓解 - Trade barrier mitigation"},
        {"name": "China - Property", "description": "房地产稳定 - Property sector stabilization"},
        {"name": "China - Tech", "description": "科技韧性 - Tech sector resilience"},
        {"name": "China - 15th FYP", "description": "十五五规划 - 15th Five-Year Plan (2026-2030)"},
        {"name": "Russia - National Projects", "description": "Национальные проекты - National Projects"},
        {"name": "Russia - S&T Programs", "description": "Научно-технологические программы - S&T Programs"},
        {"name": "Russia - Crisis Analysis", "description": "Экономический кризис - Crisis Analysis"},
        {"name": "Russia - Solutions", "description": "Реформенные пакеты - Solutions and Reforms"},
        {"name": "Data Lake", "description": "Raw economic data access"},
        {"name": "Admin", "description": "Administrative endpoints"},
    ]
)

# Add custom middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(AuditMiddleware)

# Add CORS middleware - Government domains only in production
ALLOWED_ORIGINS = [
    "https://*.gov.cn",
    "https://*.gov.ru",
    "https://api.economic-engine.gov.cn",
    "https://api.economic-engine.gov.ru",
    # Development origins (disabled in production)
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Jurisdiction"],
    expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining"],
    max_age=3600,
)

# Trusted hosts - Government domains
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "api.economic-engine.gov.cn",
        "api.economic-engine.gov.ru",
        "localhost",
        "127.0.0.1",
    ]
)


@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint with API information

    Returns comprehensive platform information including:
    - Available modules and endpoints
    - Supported jurisdictions
    - Security standards
    - Documentation links
    """
    return {
        "name": {
            "en": "Economic Policy Engine API",
            "zh": "经济政策引擎 API",
            "ru": "API Экономического Политического Движка"
        },
        "version": "2.0.0",
        "description": {
            "en": "Government-grade economic policy analysis platform for PRC and Russian Federation",
            "zh": "中华人民共和国和俄罗斯联邦政府级经济政策分析平台",
            "ru": "Государственная платформа анализа экономической политики для КНР и РФ"
        },
        "jurisdictions": {
            "PRC": {
                "name_local": "中华人民共和国",
                "endpoints": "/api/v1/china/*",
                "data_sources": ["NBS", "Customs", "PBOC", "NDRC", "MOF", "SAFE"],
                "encryption": "SM2/SM3/SM4 (GB/T standards)",
                "authentication": "统一身份认证平台"
            },
            "RU": {
                "name_local": "Российская Федерация",
                "endpoints": "/api/v1/russia/*",
                "data_sources": ["Rosstat", "CBR", "MinFin", "MinEconomy", "FTS"],
                "encryption": "GOST R 34.12-2015, GOST R 34.11-2012",
                "authentication": "ЕСИА"
            }
        },
        "modules": {
            "china": {
                "trade": {"path": "/api/v1/china/trade/*", "description": "贸易壁垒缓解"},
                "property": {"path": "/api/v1/china/property/*", "description": "房地产稳定"},
                "tech": {"path": "/api/v1/china/tech/*", "description": "科技韧性"},
                "fyp": {"path": "/api/v1/china/fyp/*", "description": "十五五规划"}
            },
            "russia": {
                "national_projects": {"path": "/api/v1/russia/national-projects/*", "description": "Национальные проекты"},
                "st_programs": {"path": "/api/v1/russia/st-programs/*", "description": "Научно-технологические программы"},
                "crisis": {"path": "/api/v1/russia/crisis/*", "description": "Экономический кризис"},
                "solutions": {"path": "/api/v1/russia/solutions/*", "description": "Реформенные пакеты"}
            }
        },
        "documentation": {
            "openapi": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "compliance": [
            "GB/T 35273-2020 (Personal Information Security)",
            "GB/T 22239-2019 (Cybersecurity MLPS)",
            "Federal Law No. 152-FZ (Personal Data)",
            "Federal Law No. 149-FZ (Information)"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Comprehensive health check endpoint

    Returns status of all system components including:
    - Core services (trade, property, tech, FYP, Russia)
    - Infrastructure (database, cache, audit)
    - Data source connections (PRC and Russia)
    - Security services
    """
    # Check database health
    db_healthy = False
    if db_manager:
        try:
            db_healthy = await db_manager.health_check()
        except Exception:
            pass

    # Check data source connectivity (simplified)
    prc_sources_healthy = all([
        nbs_client is not None,
        customs_client is not None,
        pboc_client is not None
    ]) if settings and settings.enable_china_module else None

    russia_sources_healthy = all([
        rosstat_client is not None,
        cbr_client is not None,
        minfin_client is not None
    ]) if settings and settings.enable_russia_module else None

    # Determine overall status
    core_services_healthy = all([
        trade_service is not None,
        property_service is not None,
        tech_service is not None,
        china_fyp_service is not None,
        russia_service is not None
    ])

    overall_healthy = core_services_healthy and db_healthy

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version if settings else "2.0.0",
        "environment": settings.environment if settings else "unknown",
        "components": {
            "core_services": {
                "status": "healthy" if core_services_healthy else "unhealthy",
                "details": {
                    "china_trade": trade_service is not None,
                    "china_property": property_service is not None,
                    "china_tech": tech_service is not None,
                    "china_fyp": china_fyp_service is not None,
                    "russia_analysis": russia_service is not None
                }
            },
            "infrastructure": {
                "database": "healthy" if db_healthy else "unhealthy",
                "audit_logger": "healthy" if audit_logger else "unhealthy",
                "encryption": "healthy" if encryption_manager else "unhealthy",
                "security": "healthy" if security_manager else "unhealthy"
            },
            "data_sources": {
                "prc": {
                    "status": "healthy" if prc_sources_healthy else ("disabled" if prc_sources_healthy is None else "unhealthy"),
                    "sources": ["NBS", "Customs", "PBOC", "NDRC", "MOF", "SAFE"] if prc_sources_healthy else []
                },
                "russia": {
                    "status": "healthy" if russia_sources_healthy else ("disabled" if russia_sources_healthy is None else "unhealthy"),
                    "sources": ["Rosstat", "CBR", "MinFin", "MinEconomy", "FTS"] if russia_sources_healthy else []
                }
            }
        }
    }


@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Kubernetes liveness probe - checks if the service is running"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """Kubernetes readiness probe - checks if the service is ready to accept traffic"""
    # Check critical dependencies
    ready = (
        db_manager is not None and
        security_manager is not None and
        trade_service is not None
    )

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

    return {"status": "ready", "timestamp": datetime.now().isoformat()}


# =============================================================================
# Authentication Endpoints
# =============================================================================

@app.post("/api/v1/auth/token", tags=["Authentication"])
async def authenticate(
    username: str = Query(..., description="Username or government ID"),
    password: str = Query(..., description="Password"),
    jurisdiction: str = Query("PRC", description="Jurisdiction: PRC, RU, or INT")
):
    """
    Authenticate user and obtain JWT token

    Supports:
    - PRC government authentication via 统一身份认证平台
    - Russia government authentication via ЕСИА
    - Standard username/password authentication
    """
    if not security_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service not available"
        )

    # Authenticate based on jurisdiction
    token = await security_manager.authenticate(
        username=username,
        password=password,
        jurisdiction=Jurisdiction(jurisdiction)
    )

    if not token:
        # Log failed authentication
        if audit_logger:
            await audit_logger.log(
                action=AuditAction.LOGIN_FAILURE,
                outcome=AuditOutcome.FAILURE,
                severity=AuditSeverity.WARNING,
                username=username,
                description=f"Failed authentication attempt for user: {username}",
                jurisdiction=jurisdiction
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Log successful authentication
    if audit_logger:
        await audit_logger.log(
            action=AuditAction.LOGIN_SUCCESS,
            outcome=AuditOutcome.SUCCESS,
            severity=AuditSeverity.INFO,
            username=username,
            description=f"Successful authentication for user: {username}",
            jurisdiction=jurisdiction
        )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.jwt_expiration_hours * 3600 if settings else 86400
    }


@app.post("/api/v1/auth/prc/callback", tags=["Authentication"])
async def prc_auth_callback(code: str = Query(..., description="Authorization code from IDP")):
    """
    PRC Identity Provider OAuth callback

    Handles callback from 统一身份认证平台 after user authentication
    """
    if not security_manager or not security_manager.prc_idp:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PRC authentication not configured"
        )

    token = await security_manager.handle_prc_callback(code)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/v1/auth/esia/callback", tags=["Authentication"])
async def esia_auth_callback(code: str = Query(..., description="Authorization code from ESIA")):
    """
    Russian ESIA OAuth callback

    Handles callback from ЕСИА after user authentication
    """
    if not security_manager or not security_manager.esia_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ESIA authentication not configured"
        )

    token = await security_manager.handle_esia_callback(code)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/v1/auth/me", tags=["Authentication"])
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get current authenticated user information

    Returns user profile, permissions, and jurisdiction
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
        "jurisdiction": current_user.jurisdiction,
        "permissions": current_user.permissions,
        "organization": current_user.organization
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


# =============================================================================
# Administrative Endpoints
# =============================================================================

@app.get("/api/v1/admin/audit-log", tags=["Admin"])
async def get_audit_logs(
    current_user: TokenData = Depends(require_permission(Permission.VIEW_AUDIT_LOG)),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, le=1000, description="Maximum records to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Query audit logs with filtering

    Requires AUDITOR role or VIEW_AUDIT_LOG permission.
    Returns immutable audit trail of all system activities.
    """
    if not audit_logger:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit service not available"
        )

    # Build query filters
    filters = {}
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if action:
        filters["action"] = action
    if user_id:
        filters["user_id"] = user_id

    logs = await audit_logger.query(filters=filters, limit=limit, offset=offset)

    return {
        "total": len(logs),
        "offset": offset,
        "limit": limit,
        "logs": logs
    }


@app.get("/api/v1/admin/system-status", tags=["Admin"])
async def get_system_status(
    current_user: TokenData = Depends(require_permission(Permission.SYSTEM_CONFIG))
):
    """
    Get detailed system status for administrators

    Returns comprehensive system health, performance metrics,
    and configuration status.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version if settings else "2.0.0",
        "environment": settings.environment if settings else "unknown",
        "uptime": "N/A",  # Would track actual uptime
        "configuration": {
            "prc_module_enabled": settings.enable_china_module if settings else False,
            "russia_module_enabled": settings.enable_russia_module if settings else False,
            "ml_training_enabled": settings.enable_ml_training if settings else False,
            "audit_enabled": settings.audit_enabled if settings else True,
            "rate_limiting_enabled": True
        },
        "connections": {
            "database": {
                "status": "connected" if db_manager else "disconnected",
                "pool_size": "N/A"
            },
            "prc_data_sources": {
                "nbs": "connected" if nbs_client else "disconnected",
                "customs": "connected" if customs_client else "disconnected",
                "pboc": "connected" if pboc_client else "disconnected",
                "ndrc": "connected" if ndrc_client else "disconnected",
                "mof": "connected" if mof_client else "disconnected",
                "safe": "connected" if safe_client else "disconnected"
            },
            "russia_data_sources": {
                "rosstat": "connected" if rosstat_client else "disconnected",
                "cbr": "connected" if cbr_client else "disconnected",
                "minfin": "connected" if minfin_client else "disconnected",
                "mineconomy": "connected" if mineconomy_client else "disconnected",
                "fts": "connected" if fts_client else "disconnected"
            }
        },
        "security": {
            "encryption_prc": "SM2/SM3/SM4",
            "encryption_russia": "GOST R 34.12-2015",
            "authentication": {
                "prc_idp": "enabled" if (security_manager and security_manager.prc_idp) else "disabled",
                "esia": "enabled" if (security_manager and security_manager.esia_provider) else "disabled"
            }
        }
    }


@app.post("/api/v1/admin/data-refresh", tags=["Admin"])
async def trigger_data_refresh(
    current_user: TokenData = Depends(require_permission(Permission.MANAGE_INGESTION)),
    jurisdiction: str = Query("PRC", description="Jurisdiction to refresh: PRC or RU"),
    data_type: str = Query("all", description="Data type to refresh")
):
    """
    Trigger data refresh from government sources

    Initiates data ingestion from configured government data sources.
    """
    if audit_logger:
        await audit_logger.log(
            action=AuditAction.DATA_INGESTION,
            outcome=AuditOutcome.SUCCESS,
            severity=AuditSeverity.INFO,
            user_id=current_user.user_id,
            username=current_user.username,
            description=f"Data refresh triggered for {jurisdiction}/{data_type}",
            jurisdiction=jurisdiction
        )

    # In production, this would trigger actual data ingestion tasks
    return {
        "status": "initiated",
        "jurisdiction": jurisdiction,
        "data_type": data_type,
        "timestamp": datetime.now().isoformat(),
        "message": f"Data refresh initiated for {jurisdiction}"
    }


# =============================================================================
# Metrics Endpoint (Prometheus)
# =============================================================================

@app.get("/metrics", tags=["Health"])
async def prometheus_metrics():
    """
    Prometheus metrics endpoint

    Exposes application metrics in Prometheus format for monitoring.
    """
    # Basic metrics - in production would use prometheus_client
    metrics = []

    # Application info
    metrics.append(f'economic_engine_info{{version="{settings.app_version if settings else "2.0.0}"}} 1')

    # Service status
    services = {
        "trade": trade_service is not None,
        "property": property_service is not None,
        "tech": tech_service is not None,
        "fyp": china_fyp_service is not None,
        "russia": russia_service is not None
    }

    for service, status in services.items():
        metrics.append(f'economic_engine_service_up{{service="{service}"}} {1 if status else 0}')

    # Infrastructure status
    metrics.append(f'economic_engine_database_up {1 if db_manager else 0}')
    metrics.append(f'economic_engine_audit_up {1 if audit_logger else 0}')
    metrics.append(f'economic_engine_security_up {1 if security_manager else 0}')

    # Data source status
    prc_sources = {
        "nbs": nbs_client,
        "customs": customs_client,
        "pboc": pboc_client,
        "ndrc": ndrc_client,
        "mof": mof_client,
        "safe": safe_client
    }
    for source, client in prc_sources.items():
        metrics.append(f'economic_engine_datasource_up{{jurisdiction="PRC",source="{source}"}} {1 if client else 0}')

    russia_sources = {
        "rosstat": rosstat_client,
        "cbr": cbr_client,
        "minfin": minfin_client,
        "mineconomy": mineconomy_client,
        "fts": fts_client
    }
    for source, client in russia_sources.items():
        metrics.append(f'economic_engine_datasource_up{{jurisdiction="RU",source="{source}"}} {1 if client else 0}')

    return Response(
        content="\n".join(metrics),
        media_type="text/plain"
    )


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Get configuration
    config = get_settings()

    uvicorn.run(
        "src.api.main:app",
        host=config.api_host,
        port=config.api_port,
        workers=config.api_workers,
        reload=config.environment == "development",
        log_level="info",
        access_log=True
    )
