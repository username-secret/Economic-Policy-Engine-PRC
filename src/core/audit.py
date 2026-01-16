"""
Audit logging module for Economic Policy Engine
Provides comprehensive audit trails for government compliance
Supports both PRC and Russian Federation audit requirements
"""

import json
import logging
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Audit action types"""
    # Authentication events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    TOKEN_ISSUED = "TOKEN_ISSUED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    MFA_CHALLENGE = "MFA_CHALLENGE"
    MFA_SUCCESS = "MFA_SUCCESS"
    MFA_FAILURE = "MFA_FAILURE"

    # Authorization events
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"

    # Data access events
    DATA_READ = "DATA_READ"
    DATA_CREATE = "DATA_CREATE"
    DATA_UPDATE = "DATA_UPDATE"
    DATA_DELETE = "DATA_DELETE"
    DATA_EXPORT = "DATA_EXPORT"
    DATA_IMPORT = "DATA_IMPORT"

    # API events
    API_REQUEST = "API_REQUEST"
    API_RESPONSE = "API_RESPONSE"
    API_ERROR = "API_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Configuration events
    CONFIG_READ = "CONFIG_READ"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    SYSTEM_START = "SYSTEM_START"
    SYSTEM_STOP = "SYSTEM_STOP"
    SERVICE_START = "SERVICE_START"
    SERVICE_STOP = "SERVICE_STOP"

    # Security events
    ENCRYPTION_OPERATION = "ENCRYPTION_OPERATION"
    KEY_GENERATION = "KEY_GENERATION"
    KEY_ROTATION = "KEY_ROTATION"
    SECURITY_ALERT = "SECURITY_ALERT"
    INTRUSION_ATTEMPT = "INTRUSION_ATTEMPT"

    # Administrative events
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_LOCKED = "USER_LOCKED"
    USER_UNLOCKED = "USER_UNLOCKED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET = "PASSWORD_RESET"

    # ML/Analytics events
    MODEL_TRAINED = "MODEL_TRAINED"
    MODEL_DEPLOYED = "MODEL_DEPLOYED"
    PREDICTION_MADE = "PREDICTION_MADE"
    ANALYSIS_RUN = "ANALYSIS_RUN"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditOutcome(str, Enum):
    """Audit event outcome"""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"
    PENDING = "PENDING"


@dataclass
class AuditEvent:
    """
    Comprehensive audit event record
    Compliant with both PRC and Russian Federation audit requirements
    """
    # Core fields
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    action: AuditAction = AuditAction.API_REQUEST
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    severity: AuditSeverity = AuditSeverity.INFO

    # User context
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    session_id: Optional[str] = None

    # Request context
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    http_method: Optional[str] = None
    endpoint: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None

    # Resource context
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None

    # Event details
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    # Response context
    response_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Jurisdiction and compliance
    jurisdiction: str = "PRC"  # PRC or RU
    data_classification: str = "INTERNAL"
    compliance_tags: List[str] = field(default_factory=list)

    # Integrity
    checksum: Optional[str] = None

    def __post_init__(self):
        """Calculate checksum after initialization"""
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum for integrity verification"""
        # Create a deterministic string representation
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "action": self.action.value if isinstance(self.action, Enum) else self.action,
            "user_id": self.user_id,
            "resource_id": self.resource_id,
            "outcome": self.outcome.value if isinstance(self.outcome, Enum) else self.outcome,
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        # Convert enums to values
        for key, value in result.items():
            if isinstance(value, Enum):
                result[key] = value.value
        return result

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create AuditEvent from dictionary"""
        # Convert string enums back to enum types
        if "action" in data and isinstance(data["action"], str):
            data["action"] = AuditAction(data["action"])
        if "outcome" in data and isinstance(data["outcome"], str):
            data["outcome"] = AuditOutcome(data["outcome"])
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = AuditSeverity(data["severity"])
        return cls(**data)


class AuditStorage(ABC):
    """Abstract base class for audit storage backends"""

    @abstractmethod
    async def write(self, event: AuditEvent) -> bool:
        """Write audit event to storage"""
        pass

    @abstractmethod
    async def read(self, event_id: str) -> Optional[AuditEvent]:
        """Read audit event by ID"""
        pass

    @abstractmethod
    async def query(self, filters: Dict[str, Any],
                    limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Query audit events with filters"""
        pass


class FileAuditStorage(AuditStorage):
    """
    File-based audit storage with WORM-like properties
    Suitable for compliance requirements
    """

    def __init__(self, base_path: str, jurisdiction: str = "PRC"):
        self.base_path = Path(base_path)
        self.jurisdiction = jurisdiction
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, timestamp: str) -> Path:
        """Get file path based on timestamp (daily rotation)"""
        date_str = timestamp[:10]  # YYYY-MM-DD
        return self.base_path / f"audit_{self.jurisdiction}_{date_str}.jsonl"

    async def write(self, event: AuditEvent) -> bool:
        """Write audit event to file"""
        try:
            file_path = self._get_file_path(event.timestamp)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")
            return False

    async def read(self, event_id: str) -> Optional[AuditEvent]:
        """Read audit event by ID (searches all files)"""
        try:
            for file_path in sorted(self.base_path.glob("audit_*.jsonl"), reverse=True):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        event_data = json.loads(line.strip())
                        if event_data.get("event_id") == event_id:
                            return AuditEvent.from_dict(event_data)
            return None
        except Exception as e:
            logger.error(f"Failed to read audit event: {e}")
            return None

    async def query(self, filters: Dict[str, Any],
                    limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Query audit events with filters"""
        events = []
        count = 0
        skipped = 0

        try:
            for file_path in sorted(self.base_path.glob("audit_*.jsonl"), reverse=True):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        event_data = json.loads(line.strip())

                        # Apply filters
                        match = True
                        for key, value in filters.items():
                            if event_data.get(key) != value:
                                match = False
                                break

                        if match:
                            if skipped < offset:
                                skipped += 1
                                continue

                            events.append(AuditEvent.from_dict(event_data))
                            count += 1

                            if count >= limit:
                                return events

            return events
        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")
            return []


class DatabaseAuditStorage(AuditStorage):
    """
    Database-based audit storage using PostgreSQL
    Provides better querying capabilities
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool = None

    async def _get_pool(self):
        """Get database connection pool"""
        if self._pool is None:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(self.database_url)
            except ImportError:
                logger.warning("asyncpg not installed, using sync fallback")
                self._pool = "sync"
        return self._pool

    async def write(self, event: AuditEvent) -> bool:
        """Write audit event to database"""
        try:
            pool = await self._get_pool()
            if pool == "sync":
                # Fallback to sync
                return await self._write_sync(event)

            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO audit_log (
                        id, timestamp, action, outcome, severity,
                        user_id, username, user_role, session_id,
                        request_id, ip_address, user_agent, http_method, endpoint,
                        resource_type, resource_id, resource_name,
                        description, details, response_code, response_time_ms,
                        error_code, error_message, jurisdiction, data_classification,
                        checksum, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                              $11, $12, $13, $14, $15, $16, $17, $18, $19,
                              $20, $21, $22, $23, $24, $25, $26, $27)
                """,
                    event.event_id, event.timestamp, event.action.value,
                    event.outcome.value, event.severity.value,
                    event.user_id, event.username, event.user_role, event.session_id,
                    event.request_id, event.ip_address, event.user_agent,
                    event.http_method, event.endpoint,
                    event.resource_type, event.resource_id, event.resource_name,
                    event.description, json.dumps(event.details) if event.details else None,
                    event.response_code, event.response_time_ms,
                    event.error_code, event.error_message,
                    event.jurisdiction, event.data_classification,
                    event.checksum, json.dumps({"query_params": event.query_params,
                                                 "old_value": event.old_value,
                                                 "new_value": event.new_value,
                                                 "compliance_tags": event.compliance_tags})
                )
            return True
        except Exception as e:
            logger.error(f"Failed to write audit event to database: {e}")
            return False

    async def _write_sync(self, event: AuditEvent) -> bool:
        """Synchronous write fallback"""
        # This would use SQLAlchemy synchronously
        logger.warning("Using sync database write")
        return False

    async def read(self, event_id: str) -> Optional[AuditEvent]:
        """Read audit event by ID"""
        try:
            pool = await self._get_pool()
            if pool == "sync":
                return None

            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM audit_log WHERE id = $1", event_id
                )
                if row:
                    return self._row_to_event(row)
            return None
        except Exception as e:
            logger.error(f"Failed to read audit event: {e}")
            return None

    async def query(self, filters: Dict[str, Any],
                    limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Query audit events with filters"""
        try:
            pool = await self._get_pool()
            if pool == "sync":
                return []

            # Build WHERE clause
            conditions = []
            values = []
            idx = 1
            for key, value in filters.items():
                conditions.append(f"{key} = ${idx}")
                values.append(value)
                idx += 1

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM audit_log
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${idx} OFFSET ${idx + 1}
            """
            values.extend([limit, offset])

            async with pool.acquire() as conn:
                rows = await conn.fetch(query, *values)
                return [self._row_to_event(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to query audit events: {e}")
            return []

    def _row_to_event(self, row) -> AuditEvent:
        """Convert database row to AuditEvent"""
        return AuditEvent(
            event_id=row["id"],
            timestamp=row["timestamp"],
            action=AuditAction(row["action"]),
            outcome=AuditOutcome(row["outcome"]),
            severity=AuditSeverity(row["severity"]),
            user_id=row["user_id"],
            username=row["username"],
            user_role=row["user_role"],
            session_id=row["session_id"],
            request_id=row["request_id"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            http_method=row["http_method"],
            endpoint=row["endpoint"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            resource_name=row["resource_name"],
            description=row["description"],
            details=json.loads(row["details"]) if row["details"] else None,
            response_code=row["response_code"],
            response_time_ms=row["response_time_ms"],
            error_code=row["error_code"],
            error_message=row["error_message"],
            jurisdiction=row["jurisdiction"],
            data_classification=row["data_classification"],
            checksum=row["checksum"],
        )


class AuditLogger:
    """
    Main audit logging interface
    Handles event creation and routing to storage backends
    """

    def __init__(self, storage: Optional[AuditStorage] = None,
                 default_jurisdiction: str = "PRC"):
        self.storage = storage
        self.default_jurisdiction = default_jurisdiction
        self._buffer: List[AuditEvent] = []
        self._buffer_size = 100
        self._flush_interval = 5.0  # seconds
        self._background_task = None

    async def start(self):
        """Start background flush task"""
        self._background_task = asyncio.create_task(self._flush_loop())

    async def stop(self):
        """Stop background flush task and flush remaining events"""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        await self.flush()

    async def _flush_loop(self):
        """Background loop to periodically flush buffer"""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Audit flush error: {e}")

    async def flush(self):
        """Flush buffered events to storage"""
        if not self._buffer or not self.storage:
            return

        events = self._buffer[:]
        self._buffer.clear()

        for event in events:
            try:
                await self.storage.write(event)
            except Exception as e:
                logger.error(f"Failed to flush audit event: {e}")
                # Re-add to buffer on failure
                self._buffer.append(event)

    async def log(self, event: AuditEvent):
        """Log an audit event"""
        # Set default jurisdiction if not specified
        if not event.jurisdiction:
            event.jurisdiction = self.default_jurisdiction

        # Add to buffer
        self._buffer.append(event)

        # Flush if buffer is full
        if len(self._buffer) >= self._buffer_size:
            await self.flush()

        # Also log to standard logger
        log_msg = (f"AUDIT: {event.action.value} | "
                   f"user={event.user_id} | "
                   f"resource={event.resource_type}:{event.resource_id} | "
                   f"outcome={event.outcome.value}")

        if event.severity == AuditSeverity.ERROR:
            logger.error(log_msg)
        elif event.severity == AuditSeverity.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    async def log_request(self, user_id: Optional[str], username: Optional[str],
                          method: str, endpoint: str, ip_address: str,
                          user_agent: str, request_id: str,
                          **kwargs) -> AuditEvent:
        """Log an API request"""
        event = AuditEvent(
            action=AuditAction.API_REQUEST,
            user_id=user_id,
            username=username,
            http_method=method,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            **kwargs
        )
        await self.log(event)
        return event

    async def log_response(self, request_event: AuditEvent,
                           response_code: int, response_time_ms: float,
                           error_code: Optional[str] = None,
                           error_message: Optional[str] = None):
        """Log an API response (linked to request)"""
        outcome = AuditOutcome.SUCCESS if response_code < 400 else AuditOutcome.FAILURE
        severity = AuditSeverity.ERROR if response_code >= 500 else AuditSeverity.INFO

        event = AuditEvent(
            action=AuditAction.API_RESPONSE,
            user_id=request_event.user_id,
            username=request_event.username,
            http_method=request_event.http_method,
            endpoint=request_event.endpoint,
            ip_address=request_event.ip_address,
            request_id=request_event.request_id,
            response_code=response_code,
            response_time_ms=response_time_ms,
            error_code=error_code,
            error_message=error_message,
            outcome=outcome,
            severity=severity,
            jurisdiction=request_event.jurisdiction,
        )
        await self.log(event)

    async def log_authentication(self, action: AuditAction,
                                  user_id: Optional[str],
                                  username: Optional[str],
                                  ip_address: str,
                                  success: bool,
                                  details: Optional[Dict[str, Any]] = None):
        """Log authentication event"""
        event = AuditEvent(
            action=action,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            details=details,
            jurisdiction=self.default_jurisdiction,
        )
        await self.log(event)

    async def log_data_access(self, user_id: str, username: str,
                               action: AuditAction, resource_type: str,
                               resource_id: str, success: bool,
                               details: Optional[Dict[str, Any]] = None):
        """Log data access event"""
        event = AuditEvent(
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            severity=AuditSeverity.INFO,
            details=details,
            jurisdiction=self.default_jurisdiction,
        )
        await self.log(event)

    async def log_config_change(self, user_id: str, username: str,
                                 config_key: str, old_value: Any,
                                 new_value: Any):
        """Log configuration change"""
        event = AuditEvent(
            action=AuditAction.CONFIG_CHANGE,
            user_id=user_id,
            username=username,
            resource_type="config",
            resource_id=config_key,
            old_value=old_value,
            new_value=new_value,
            severity=AuditSeverity.WARNING,
            jurisdiction=self.default_jurisdiction,
        )
        await self.log(event)

    async def log_security_event(self, action: AuditAction,
                                  description: str,
                                  severity: AuditSeverity = AuditSeverity.WARNING,
                                  user_id: Optional[str] = None,
                                  ip_address: Optional[str] = None,
                                  details: Optional[Dict[str, Any]] = None):
        """Log security event"""
        event = AuditEvent(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            description=description,
            severity=severity,
            details=details,
            jurisdiction=self.default_jurisdiction,
            compliance_tags=["security"],
        )
        await self.log(event)

    async def query(self, filters: Dict[str, Any],
                    limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Query audit events"""
        if not self.storage:
            return []
        return await self.storage.query(filters, limit, offset)


# Factory function to create audit logger with appropriate storage
def create_audit_logger(settings=None) -> AuditLogger:
    """Create audit logger with storage based on settings"""
    from .config import settings as default_settings
    settings = settings or default_settings

    # Determine storage backend
    if settings.database_url and "postgresql" in settings.database_url:
        storage = DatabaseAuditStorage(settings.database_url)
    else:
        storage = FileAuditStorage(
            settings.audit_log_path,
            settings.primary_jurisdiction.value
        )

    return AuditLogger(
        storage=storage,
        default_jurisdiction=settings.primary_jurisdiction.value
    )
