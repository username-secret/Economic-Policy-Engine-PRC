"""
Security module for Economic Policy Engine
Handles authentication, authorization, and security operations
Supports PRC 统一身份认证平台 and Russian ЕСИА (ESIA)
"""

import jwt
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import httpx
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """User roles with bilingual labels"""
    # PRC Role Names
    SYSTEM_ADMIN = "system_admin"  # 系统管理员
    DATA_ANALYST = "data_analyst"  # 数据分析师
    POLICY_MAKER = "policy_maker"  # 政策制定者
    AUDITOR = "auditor"  # 审计员
    READ_ONLY = "read_only"  # 只读用户

    # Russian Role Names (mapped to same enum)
    # Системный администратор -> SYSTEM_ADMIN
    # Аналитик данных -> DATA_ANALYST
    # Лицо, принимающее решения -> POLICY_MAKER
    # Аудитор -> AUDITOR
    # Только чтение -> READ_ONLY

    @property
    def display_name_cn(self) -> str:
        """Chinese display name"""
        names = {
            self.SYSTEM_ADMIN: "系统管理员",
            self.DATA_ANALYST: "数据分析师",
            self.POLICY_MAKER: "政策制定者",
            self.AUDITOR: "审计员",
            self.READ_ONLY: "只读用户",
        }
        return names.get(self, self.value)

    @property
    def display_name_ru(self) -> str:
        """Russian display name"""
        names = {
            self.SYSTEM_ADMIN: "Системный администратор",
            self.DATA_ANALYST: "Аналитик данных",
            self.POLICY_MAKER: "Лицо, принимающее решения",
            self.AUDITOR: "Аудитор",
            self.READ_ONLY: "Только чтение",
        }
        return names.get(self, self.value)


class Permission(str, Enum):
    """Granular permissions for RBAC"""
    # Read permissions
    READ_CHINA_TRADE = "read:china:trade"
    READ_CHINA_PROPERTY = "read:china:property"
    READ_CHINA_TECH = "read:china:tech"
    READ_CHINA_FYP = "read:china:fyp"
    READ_RUSSIA_PROJECTS = "read:russia:projects"
    READ_RUSSIA_ST = "read:russia:st"
    READ_RUSSIA_CRISIS = "read:russia:crisis"
    READ_DATA_LAKE = "read:data_lake"

    # Write permissions
    WRITE_CHINA_TRADE = "write:china:trade"
    WRITE_CHINA_PROPERTY = "write:china:property"
    WRITE_CHINA_TECH = "write:china:tech"
    WRITE_CHINA_FYP = "write:china:fyp"
    WRITE_RUSSIA_PROJECTS = "write:russia:projects"
    WRITE_RUSSIA_ST = "write:russia:st"
    WRITE_RUSSIA_CRISIS = "write:russia:crisis"
    WRITE_DATA_LAKE = "write:data_lake"

    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_CONFIG = "admin:config"
    ADMIN_AUDIT = "admin:audit"
    ADMIN_SYSTEM = "admin:system"

    # Special permissions
    EXPORT_DATA = "export:data"
    ML_TRAINING = "ml:training"
    API_FULL_ACCESS = "api:full_access"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SYSTEM_ADMIN: set(Permission),  # All permissions

    UserRole.DATA_ANALYST: {
        Permission.READ_CHINA_TRADE,
        Permission.READ_CHINA_PROPERTY,
        Permission.READ_CHINA_TECH,
        Permission.READ_CHINA_FYP,
        Permission.READ_RUSSIA_PROJECTS,
        Permission.READ_RUSSIA_ST,
        Permission.READ_RUSSIA_CRISIS,
        Permission.READ_DATA_LAKE,
        Permission.WRITE_DATA_LAKE,
        Permission.EXPORT_DATA,
        Permission.ML_TRAINING,
    },

    UserRole.POLICY_MAKER: {
        Permission.READ_CHINA_TRADE,
        Permission.READ_CHINA_PROPERTY,
        Permission.READ_CHINA_TECH,
        Permission.READ_CHINA_FYP,
        Permission.READ_RUSSIA_PROJECTS,
        Permission.READ_RUSSIA_ST,
        Permission.READ_RUSSIA_CRISIS,
        Permission.READ_DATA_LAKE,
        Permission.WRITE_CHINA_FYP,
        Permission.WRITE_RUSSIA_PROJECTS,
        Permission.EXPORT_DATA,
    },

    UserRole.AUDITOR: {
        Permission.READ_CHINA_TRADE,
        Permission.READ_CHINA_PROPERTY,
        Permission.READ_CHINA_TECH,
        Permission.READ_CHINA_FYP,
        Permission.READ_RUSSIA_PROJECTS,
        Permission.READ_RUSSIA_ST,
        Permission.READ_RUSSIA_CRISIS,
        Permission.READ_DATA_LAKE,
        Permission.ADMIN_AUDIT,
        Permission.EXPORT_DATA,
    },

    UserRole.READ_ONLY: {
        Permission.READ_CHINA_TRADE,
        Permission.READ_CHINA_PROPERTY,
        Permission.READ_CHINA_TECH,
        Permission.READ_CHINA_FYP,
        Permission.READ_RUSSIA_PROJECTS,
        Permission.READ_RUSSIA_ST,
        Permission.READ_RUSSIA_CRISIS,
        Permission.READ_DATA_LAKE,
    },
}


@dataclass
class User:
    """User model for authenticated users"""
    user_id: str
    username: str
    email: Optional[str] = None
    role: UserRole = UserRole.READ_ONLY
    jurisdiction: str = "PRC"  # PRC or RU
    organization: Optional[str] = None
    department: Optional[str] = None
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    mfa_enabled: bool = True
    active: bool = True

    def __post_init__(self):
        # Auto-populate permissions based on role if not set
        if not self.permissions:
            self.permissions = ROLE_PERMISSIONS.get(self.role, set())

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission"""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the given permissions"""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the given permissions"""
        return all(p in self.permissions for p in permissions)


@dataclass
class TokenPayload:
    """JWT token payload structure"""
    sub: str  # Subject (user_id)
    username: str
    role: str
    jurisdiction: str
    permissions: List[str]
    iat: int  # Issued at
    exp: int  # Expiration
    jti: str  # JWT ID
    iss: str = "economic-policy-engine"
    aud: str = "government"


class AuthenticationProvider(ABC):
    """Abstract base class for authentication providers"""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate user with given credentials"""
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> Optional[User]:
        """Validate a token and return user if valid"""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        pass


class PRCIdentityProvider(AuthenticationProvider):
    """
    PRC Unified Identity Platform (统一身份认证平台) Integration
    Implements OAuth 2.0 / SAML 2.0 authentication
    """

    def __init__(self, idp_url: str, client_id: str, client_secret: str):
        self.idp_url = idp_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """
        Authenticate using PRC unified identity platform

        Args:
            credentials: Dict containing 'code' (authorization code) or
                        'username'/'password' for direct auth

        Returns:
            User object if authentication successful
        """
        try:
            if "code" in credentials:
                # OAuth 2.0 authorization code flow
                token_response = await self._exchange_code(credentials["code"])
                if not token_response:
                    return None

                user_info = await self._get_user_info(token_response["access_token"])
                if not user_info:
                    return None

                return self._map_to_user(user_info)

            elif "username" in credentials and "password" in credentials:
                # Resource owner password credentials (for internal use)
                token_response = await self._password_auth(
                    credentials["username"],
                    credentials["password"]
                )
                if not token_response:
                    return None

                user_info = await self._get_user_info(token_response["access_token"])
                if not user_info:
                    return None

                return self._map_to_user(user_info)

            return None

        except Exception as e:
            logger.error(f"PRC IDP authentication error: {e}")
            return None

    async def _exchange_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens"""
        try:
            response = await self._http_client.post(
                f"{self.idp_url}/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": f"{self.idp_url}/callback"
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Code exchange error: {e}")
            return None

    async def _password_auth(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate using username/password"""
        try:
            response = await self._http_client.post(
                f"{self.idp_url}/oauth2/token",
                data={
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Password auth error: {e}")
            return None

    async def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from IDP"""
        try:
            response = await self._http_client.get(
                f"{self.idp_url}/oauth2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Get user info error: {e}")
            return None

    def _map_to_user(self, user_info: Dict[str, Any]) -> User:
        """Map IDP user info to User model"""
        role_mapping = {
            "admin": UserRole.SYSTEM_ADMIN,
            "analyst": UserRole.DATA_ANALYST,
            "policymaker": UserRole.POLICY_MAKER,
            "auditor": UserRole.AUDITOR,
            "viewer": UserRole.READ_ONLY,
        }

        return User(
            user_id=user_info.get("sub", user_info.get("user_id")),
            username=user_info.get("preferred_username", user_info.get("name")),
            email=user_info.get("email"),
            role=role_mapping.get(user_info.get("role", "viewer"), UserRole.READ_ONLY),
            jurisdiction="PRC",
            organization=user_info.get("organization", user_info.get("org")),
            department=user_info.get("department", user_info.get("dept")),
            metadata=user_info,
        )

    async def validate_token(self, token: str) -> Optional[User]:
        """Validate access token with IDP"""
        try:
            response = await self._http_client.post(
                f"{self.idp_url}/oauth2/introspect",
                data={
                    "token": token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("active"):
                    return self._map_to_user(data)
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token"""
        try:
            response = await self._http_client.post(
                f"{self.idp_url}/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None


class ESIAProvider(AuthenticationProvider):
    """
    Russian ESIA (ЕСИА - Единая система идентификации и аутентификации) Integration
    Implements OAuth 2.0 authentication for Russian Federation
    """

    def __init__(self, esia_url: str, client_id: str, client_secret: str):
        self.esia_url = esia_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """
        Authenticate using ESIA

        Args:
            credentials: Dict containing 'code' (authorization code)

        Returns:
            User object if authentication successful
        """
        try:
            if "code" not in credentials:
                return None

            # Exchange authorization code for tokens
            token_response = await self._exchange_code(credentials["code"])
            if not token_response:
                return None

            # Get user information
            user_info = await self._get_user_info(token_response["access_token"])
            if not user_info:
                return None

            return self._map_to_user(user_info)

        except Exception as e:
            logger.error(f"ESIA authentication error: {e}")
            return None

    async def _exchange_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens"""
        try:
            # ESIA requires timestamp and signature
            timestamp = int(time.time())
            state = secrets.token_urlsafe(32)

            # Create signature (simplified - in production use GOST)
            message = f"{self.client_id}{code}{timestamp}"
            signature = hmac.new(
                self.client_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            response = await self._http_client.post(
                f"{self.esia_url}/aas/oauth2/te",
                data={
                    "client_id": self.client_id,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"https://api.economic-engine.gov.ru/callback",
                    "timestamp": timestamp,
                    "client_secret": signature,
                    "scope": "openid profile"
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"ESIA code exchange error: {e}")
            return None

    async def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from ESIA"""
        try:
            response = await self._http_client.get(
                f"{self.esia_url}/rs/prns",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"ESIA get user info error: {e}")
            return None

    def _map_to_user(self, user_info: Dict[str, Any]) -> User:
        """Map ESIA user info to User model"""
        role_mapping = {
            "ADMIN": UserRole.SYSTEM_ADMIN,
            "ANALYST": UserRole.DATA_ANALYST,
            "DECISION_MAKER": UserRole.POLICY_MAKER,
            "AUDITOR": UserRole.AUDITOR,
            "VIEWER": UserRole.READ_ONLY,
        }

        return User(
            user_id=str(user_info.get("oid", user_info.get("id"))),
            username=user_info.get("firstName", "") + " " + user_info.get("lastName", ""),
            email=user_info.get("email"),
            role=role_mapping.get(user_info.get("role", "VIEWER"), UserRole.READ_ONLY),
            jurisdiction="RU",
            organization=user_info.get("organization"),
            department=user_info.get("department"),
            metadata=user_info,
        )

    async def validate_token(self, token: str) -> Optional[User]:
        """Validate access token with ESIA"""
        try:
            response = await self._http_client.get(
                f"{self.esia_url}/rs/prns",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return self._map_to_user(response.json())
            return None
        except Exception as e:
            logger.error(f"ESIA token validation error: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token"""
        try:
            timestamp = int(time.time())
            message = f"{self.client_id}{refresh_token}{timestamp}"
            signature = hmac.new(
                self.client_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            response = await self._http_client.post(
                f"{self.esia_url}/aas/oauth2/te",
                data={
                    "client_id": self.client_id,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "timestamp": timestamp,
                    "client_secret": signature,
                }
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"ESIA token refresh error: {e}")
            return None


class LocalAuthProvider(AuthenticationProvider):
    """
    Local authentication provider for development and fallback
    Uses JWT tokens with local user store
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self._users: Dict[str, Dict[str, Any]] = {}
        self._tokens: Dict[str, str] = {}  # jti -> user_id mapping

    def register_user(self, username: str, password: str, role: UserRole,
                      jurisdiction: str = "PRC", **kwargs) -> User:
        """Register a new user"""
        user_id = secrets.token_urlsafe(16)
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        user_data = {
            "user_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "role": role.value,
            "jurisdiction": jurisdiction,
            **kwargs
        }
        self._users[username] = user_data

        return User(
            user_id=user_id,
            username=username,
            role=role,
            jurisdiction=jurisdiction,
            **{k: v for k, v in kwargs.items() if k in User.__dataclass_fields__}
        )

    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[User]:
        """Authenticate using username/password"""
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            return None

        user_data = self._users.get(username)
        if not user_data:
            return None

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user_data["password_hash"] != password_hash:
            return None

        return User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            role=UserRole(user_data["role"]),
            jurisdiction=user_data["jurisdiction"],
            email=user_data.get("email"),
            organization=user_data.get("organization"),
            department=user_data.get("department"),
        )

    def create_token(self, user: User, expires_hours: int = 24) -> str:
        """Create JWT token for user"""
        now = datetime.utcnow()
        jti = secrets.token_urlsafe(16)

        payload = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "jurisdiction": user.jurisdiction,
            "permissions": [p.value for p in user.permissions],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=expires_hours)).timestamp()),
            "jti": jti,
            "iss": "economic-policy-engine",
            "aud": "government"
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        self._tokens[jti] = user.user_id

        return token

    async def validate_token(self, token: str) -> Optional[User]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="government",
                issuer="economic-policy-engine"
            )

            # Check if token was revoked
            if payload.get("jti") not in self._tokens:
                return None

            return User(
                user_id=payload["sub"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                jurisdiction=payload["jurisdiction"],
                permissions={Permission(p) for p in payload.get("permissions", [])},
            )

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh is not supported for local auth in this implementation"""
        return None

    def revoke_token(self, jti: str):
        """Revoke a token by its JTI"""
        self._tokens.pop(jti, None)


class SecurityManager:
    """
    Main security manager coordinating authentication and authorization
    """

    def __init__(self, settings=None):
        from .config import settings as default_settings
        self.settings = settings or default_settings

        self._providers: Dict[str, AuthenticationProvider] = {}
        self._local_auth = LocalAuthProvider(
            self.settings.jwt_secret.get_secret_value(),
            self.settings.jwt_algorithm
        )

        # Initialize providers based on settings
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize authentication providers based on configuration"""
        # Local provider is always available
        self._providers["local"] = self._local_auth

        # PRC Identity Provider
        if self.settings.prc_idp_enabled and self.settings.prc_idp_url:
            self._providers["prc"] = PRCIdentityProvider(
                self.settings.prc_idp_url,
                self.settings.prc_idp_client_id,
                self.settings.prc_idp_client_secret.get_secret_value()
                if self.settings.prc_idp_client_secret else ""
            )

        # ESIA Provider for Russia
        if self.settings.esia_enabled and self.settings.esia_url:
            self._providers["esia"] = ESIAProvider(
                self.settings.esia_url,
                self.settings.esia_client_id,
                self.settings.esia_client_secret.get_secret_value()
                if self.settings.esia_client_secret else ""
            )

    async def authenticate(self, credentials: Dict[str, Any],
                           provider: str = "local") -> Optional[User]:
        """
        Authenticate user using specified provider

        Args:
            credentials: Authentication credentials
            provider: Provider name ("local", "prc", "esia")

        Returns:
            User object if authentication successful
        """
        auth_provider = self._providers.get(provider)
        if not auth_provider:
            logger.error(f"Unknown authentication provider: {provider}")
            return None

        return await auth_provider.authenticate(credentials)

    async def validate_token(self, token: str,
                             provider: str = "local") -> Optional[User]:
        """Validate token and return user"""
        auth_provider = self._providers.get(provider)
        if not auth_provider:
            # Try local provider as fallback
            auth_provider = self._local_auth

        return await auth_provider.validate_token(token)

    def create_token(self, user: User, expires_hours: int = None) -> str:
        """Create JWT token for user"""
        if expires_hours is None:
            expires_hours = self.settings.jwt_expiration_hours
        return self._local_auth.create_token(user, expires_hours)

    def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return user.has_permission(permission)

    def check_permissions(self, user: User, permissions: List[Permission],
                          require_all: bool = True) -> bool:
        """Check if user has required permissions"""
        if require_all:
            return user.has_all_permissions(permissions)
        return user.has_any_permission(permissions)

    def register_local_user(self, username: str, password: str,
                            role: UserRole, **kwargs) -> User:
        """Register a user in local auth provider"""
        return self._local_auth.register_user(username, password, role, **kwargs)

    def get_provider(self, name: str) -> Optional[AuthenticationProvider]:
        """Get authentication provider by name"""
        return self._providers.get(name)


def require_permission(permission: Permission):
    """Decorator to require specific permission for a function"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs or first arg
            user = kwargs.get("user") or kwargs.get("current_user")
            if not user:
                raise PermissionError("User not authenticated")

            if not user.has_permission(permission):
                raise PermissionError(f"Permission denied: {permission.value}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(roles: List[UserRole]):
    """Decorator to require specific role(s) for a function"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("user") or kwargs.get("current_user")
            if not user:
                raise PermissionError("User not authenticated")

            if user.role not in roles:
                raise PermissionError(f"Role required: {[r.value for r in roles]}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
