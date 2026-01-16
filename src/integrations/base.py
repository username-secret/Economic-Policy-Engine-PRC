"""
Base classes for government data source integrations
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type
from enum import Enum
import httpx
import json

logger = logging.getLogger(__name__)


class AuthenticationType(str, Enum):
    """Authentication types for data sources"""
    API_KEY = "api_key"
    CERTIFICATE = "certificate"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    OPEN = "open"


class DataFormat(str, Enum):
    """Data formats supported by data sources"""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    EDIFACT = "edifact"


@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    name: str
    name_en: str
    endpoint: str
    auth_type: AuthenticationType
    data_types: List[str]
    update_frequency: str
    format: DataFormat
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # Authentication credentials (set at runtime)
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    certificate_path: Optional[str] = None
    certificate_password: Optional[str] = None


@dataclass
class DataPoint:
    """A single data point from a data source"""
    source: str
    data_type: str
    timestamp: datetime
    value: Any
    unit: Optional[str] = None
    region: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class DataFetchResult:
    """Result of a data fetch operation"""
    success: bool
    source: str
    data_type: str
    data_points: List[DataPoint] = field(default_factory=list)
    error_message: Optional[str] = None
    fetch_time: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0


class DataSourceClient(ABC):
    """
    Abstract base class for government data source clients
    Handles authentication, request/response, and error handling
    """

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self._http_client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._rate_limiter = asyncio.Semaphore(10)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        """Establish connection to data source"""
        self._http_client = httpx.AsyncClient(
            timeout=self.config.timeout,
            follow_redirects=True
        )
        await self._authenticate()

    async def disconnect(self):
        """Close connection to data source"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def _authenticate(self):
        """Authenticate with the data source"""
        if self.config.auth_type == AuthenticationType.OPEN:
            return

        if self.config.auth_type == AuthenticationType.API_KEY:
            # API key is included in headers
            pass

        elif self.config.auth_type == AuthenticationType.OAUTH2:
            await self._oauth2_authenticate()

        elif self.config.auth_type == AuthenticationType.CERTIFICATE:
            await self._certificate_authenticate()

    async def _oauth2_authenticate(self):
        """Perform OAuth 2.0 client credentials authentication"""
        try:
            response = await self._http_client.post(
                f"{self.config.endpoint}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                }
            )
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        except Exception as e:
            logger.error(f"OAuth2 authentication failed: {e}")
            raise

    async def _certificate_authenticate(self):
        """Authenticate using client certificate"""
        # In production, this would use mutual TLS with client certificate
        # The httpx client would be configured with cert parameter
        pass

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.config.auth_type == AuthenticationType.API_KEY:
            headers["X-API-Key"] = self.config.api_key or ""

        elif self.config.auth_type == AuthenticationType.OAUTH2:
            if self._access_token:
                headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    async def _ensure_authenticated(self):
        """Ensure we have valid authentication"""
        if self.config.auth_type == AuthenticationType.OAUTH2:
            if self._token_expiry and datetime.utcnow() >= self._token_expiry:
                await self._oauth2_authenticate()

    async def _make_request(self, method: str, path: str,
                            params: Optional[Dict[str, Any]] = None,
                            data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make an authenticated request with retry logic"""
        await self._ensure_authenticated()

        url = f"{self.config.endpoint}{path}"
        headers = self._get_headers()

        for attempt in range(self.config.retry_attempts):
            try:
                async with self._rate_limiter:
                    if method.upper() == "GET":
                        response = await self._http_client.get(
                            url, headers=headers, params=params
                        )
                    elif method.upper() == "POST":
                        response = await self._http_client.post(
                            url, headers=headers, json=data, params=params
                        )
                    else:
                        raise ValueError(f"Unsupported method: {method}")

                    if response.status_code == 429:  # Rate limited
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    return response

            except httpx.TimeoutException:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise

        raise Exception(f"Request failed after {self.config.retry_attempts} attempts")

    @abstractmethod
    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         **kwargs) -> DataFetchResult:
        """
        Fetch data of specified type from the source

        Args:
            data_type: Type of data to fetch (e.g., 'gdp', 'cpi')
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataFetchResult containing fetched data points
        """
        pass

    @abstractmethod
    def parse_response(self, response_data: Any,
                        data_type: str) -> List[DataPoint]:
        """
        Parse response data into DataPoint objects

        Args:
            response_data: Raw response data
            data_type: Type of data being parsed

        Returns:
            List of DataPoint objects
        """
        pass


class DataIngestionService(ABC):
    """
    Abstract base class for data ingestion services
    Coordinates fetching data from multiple sources and storing it
    """

    def __init__(self, clients: List[DataSourceClient]):
        self.clients = {client.config.name: client for client in clients}
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        """Start the ingestion service"""
        self._running = True
        for client in self.clients.values():
            await client.connect()

    async def stop(self):
        """Stop the ingestion service"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        for client in self.clients.values():
            await client.disconnect()

    async def fetch_all(self, data_types: Optional[List[str]] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[DataFetchResult]:
        """
        Fetch data from all sources

        Args:
            data_types: Types of data to fetch (None = all)
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of DataFetchResult from all sources
        """
        results = []
        tasks = []

        for name, client in self.clients.items():
            types_to_fetch = data_types or client.config.data_types
            for data_type in types_to_fetch:
                if data_type in client.config.data_types:
                    task = asyncio.create_task(
                        client.fetch_data(data_type, start_date, end_date)
                    )
                    tasks.append((name, data_type, task))

        for name, data_type, task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to fetch {data_type} from {name}: {e}")
                results.append(DataFetchResult(
                    success=False,
                    source=name,
                    data_type=data_type,
                    error_message=str(e)
                ))

        return results

    @abstractmethod
    async def store_data(self, results: List[DataFetchResult]) -> int:
        """
        Store fetched data to the database

        Args:
            results: List of DataFetchResult to store

        Returns:
            Number of data points stored
        """
        pass

    async def run_ingestion_cycle(self, data_types: Optional[List[str]] = None):
        """Run a single ingestion cycle"""
        logger.info("Starting ingestion cycle")
        start_time = datetime.utcnow()

        results = await self.fetch_all(data_types)
        stored = await self.store_data(results)

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Ingestion cycle completed: {stored} points in {elapsed:.2f}s")

        return stored

    async def run_scheduled(self, interval_seconds: int = 3600):
        """Run ingestion on a schedule"""
        while self._running:
            try:
                await self.run_ingestion_cycle()
            except Exception as e:
                logger.error(f"Ingestion cycle failed: {e}")

            await asyncio.sleep(interval_seconds)
