"""
Russian Federation Government Data Source Integrations
Implements connections to Russian government data systems
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET

from .base import (
    DataSourceClient, DataIngestionService, DataSourceConfig,
    DataPoint, DataFetchResult, AuthenticationType, DataFormat
)

logger = logging.getLogger(__name__)


class RosstatClient(DataSourceClient):
    """
    Росстат (Federal State Statistics Service) Client
    Primary source for Russia's economic and demographic indicators
    """

    def __init__(self, api_key: Optional[str] = None):
        config = DataSourceConfig(
            name="Росстат",
            name_en="Federal State Statistics Service",
            endpoint="https://rosstat.gov.ru/api/v1",
            auth_type=AuthenticationType.API_KEY,
            data_types=[
                "gdp", "gdp_growth", "inflation_official",
                "industrial_production", "retail_sales",
                "unemployment", "real_wages",
                "construction", "agriculture",
                "population", "demographics"
            ],
            update_frequency="monthly",
            format=DataFormat.JSON,
            timeout=30,
            retry_attempts=3
        )
        config.api_key = api_key
        super().__init__(config)

        self._indicator_mapping = {
            "gdp": "GDP_Q",
            "gdp_growth": "GDP_GROWTH",
            "inflation_official": "CPI_M",
            "industrial_production": "IND_PROD_M",
            "retail_sales": "RETAIL_M",
            "unemployment": "UNEMP_M",
            "real_wages": "WAGES_REAL_M",
            "construction": "CONSTR_M",
            "agriculture": "AGRI_M",
            "population": "POP_Y",
            "demographics": "DEMO_Y",
        }

    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         region: str = "RU") -> DataFetchResult:
        """Fetch data from Rosstat"""
        start_time = datetime.utcnow()

        if data_type not in self._indicator_mapping:
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=f"Unknown data type: {data_type}"
            )

        indicator_code = self._indicator_mapping[data_type]

        params = {
            "indicator": indicator_code,
            "region": region,
            "format": "json"
        }

        if start_date:
            params["period_from"] = start_date.strftime("%Y-%m")
        if end_date:
            params["period_to"] = end_date.strftime("%Y-%m")

        try:
            response = await self._make_request("GET", "/data/query", params=params)
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                data_points = self.parse_response(data, data_type)
                return DataFetchResult(
                    success=True,
                    source=self.config.name,
                    data_type=data_type,
                    data_points=data_points,
                    response_time_ms=elapsed
                )
            else:
                return DataFetchResult(
                    success=False,
                    source=self.config.name,
                    data_type=data_type,
                    error_message=f"HTTP {response.status_code}",
                    response_time_ms=elapsed
                )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=str(e),
                response_time_ms=elapsed
            )

    def parse_response(self, response_data: Any, data_type: str) -> List[DataPoint]:
        """Parse Rosstat response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", [])
            for record in records:
                period = record.get("period", "")
                if "-" in period:
                    parts = period.split("-")
                    timestamp = datetime(int(parts[0]), int(parts[1]) if len(parts) > 1 else 1, 1)
                else:
                    timestamp = datetime.utcnow()

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value"),
                    unit=record.get("unit"),
                    region=record.get("region", "RU"),
                    metadata={
                        "indicator_code": record.get("indicator"),
                        "frequency": record.get("frequency"),
                        "revision": record.get("revision"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse Rosstat response: {e}")

        return data_points


class CBRClient(DataSourceClient):
    """
    Центральный банк России (Central Bank of Russia) Client
    Source for monetary policy, banking, and forex data
    Open API - no authentication required
    """

    def __init__(self):
        config = DataSourceConfig(
            name="Центральный банк РФ",
            name_en="Central Bank of Russia",
            endpoint="https://cbr.ru/api/v1",
            auth_type=AuthenticationType.OPEN,
            data_types=[
                "key_rate", "inflation_target",
                "forex_usd", "forex_eur", "forex_cny",
                "monetary_base", "m2_money_supply",
                "banking_sector", "reserves",
                "credit_growth", "deposit_rates"
            ],
            update_frequency="daily",
            format=DataFormat.JSON,
            timeout=30,
            retry_attempts=3
        )
        super().__init__(config)

    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         **kwargs) -> DataFetchResult:
        """Fetch monetary data from CBR"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "key_rate": "/monetary/keyrate",
            "inflation_target": "/monetary/inflation-target",
            "forex_usd": "/forex/USD",
            "forex_eur": "/forex/EUR",
            "forex_cny": "/forex/CNY",
            "monetary_base": "/monetary/base",
            "m2_money_supply": "/monetary/m2",
            "banking_sector": "/banking/overview",
            "reserves": "/reserves/international",
            "credit_growth": "/credit/growth",
            "deposit_rates": "/rates/deposits",
        }

        if data_type not in endpoint_mapping:
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=f"Unknown data type: {data_type}"
            )

        params = {}
        if start_date:
            params["date_from"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["date_to"] = end_date.strftime("%Y-%m-%d")

        try:
            response = await self._make_request(
                "GET",
                endpoint_mapping[data_type],
                params=params
            )
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                data_points = self.parse_response(data, data_type)
                return DataFetchResult(
                    success=True,
                    source=self.config.name,
                    data_type=data_type,
                    data_points=data_points,
                    response_time_ms=elapsed
                )
            else:
                return DataFetchResult(
                    success=False,
                    source=self.config.name,
                    data_type=data_type,
                    error_message=f"HTTP {response.status_code}",
                    response_time_ms=elapsed
                )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=str(e),
                response_time_ms=elapsed
            )

    def parse_response(self, response_data: Any, data_type: str) -> List[DataPoint]:
        """Parse CBR response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", response_data.get("rates", []))
            if not isinstance(records, list):
                records = [response_data]

            for record in records:
                date_str = record.get("date", record.get("effective_date", ""))
                if date_str:
                    timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.utcnow()

                unit_mapping = {
                    "key_rate": "%",
                    "inflation_target": "%",
                    "forex_usd": "RUB/USD",
                    "forex_eur": "RUB/EUR",
                    "forex_cny": "RUB/CNY",
                    "monetary_base": "млрд руб",
                    "m2_money_supply": "млрд руб",
                    "reserves": "млрд USD",
                    "credit_growth": "%",
                    "deposit_rates": "%",
                }

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value", record.get("rate")),
                    unit=unit_mapping.get(data_type),
                    metadata={
                        "currency": record.get("currency"),
                        "nominal": record.get("nominal"),
                        "change": record.get("change"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse CBR response: {e}")

        return data_points


class MinFinClient(DataSourceClient):
    """
    Министерство финансов (Ministry of Finance) Client
    Source for budget, debt, and NWF data
    """

    def __init__(self, certificate_path: Optional[str] = None,
                 certificate_password: Optional[str] = None):
        config = DataSourceConfig(
            name="Минфин России",
            name_en="Ministry of Finance of Russia",
            endpoint="https://minfin.gov.ru/api/v1",
            auth_type=AuthenticationType.CERTIFICATE,
            data_types=[
                "federal_budget_revenue", "federal_budget_expenditure",
                "budget_deficit", "nwf_size", "nwf_liquid",
                "government_debt", "external_debt",
                "oil_gas_revenue", "non_oil_gas_revenue"
            ],
            update_frequency="monthly",
            format=DataFormat.JSON,
            timeout=30,
            retry_attempts=3
        )
        config.certificate_path = certificate_path
        config.certificate_password = certificate_password
        super().__init__(config)

    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         **kwargs) -> DataFetchResult:
        """Fetch fiscal data from MinFin"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "federal_budget_revenue": "/budget/revenue",
            "federal_budget_expenditure": "/budget/expenditure",
            "budget_deficit": "/budget/deficit",
            "nwf_size": "/nwf/total",
            "nwf_liquid": "/nwf/liquid",
            "government_debt": "/debt/internal",
            "external_debt": "/debt/external",
            "oil_gas_revenue": "/budget/oil-gas-revenue",
            "non_oil_gas_revenue": "/budget/non-oil-gas-revenue",
        }

        if data_type not in endpoint_mapping:
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=f"Unknown data type: {data_type}"
            )

        params = {}
        if start_date:
            params["year"] = start_date.year
        if end_date:
            params["year_to"] = end_date.year

        try:
            response = await self._make_request(
                "GET",
                endpoint_mapping[data_type],
                params=params
            )
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                data_points = self.parse_response(data, data_type)
                return DataFetchResult(
                    success=True,
                    source=self.config.name,
                    data_type=data_type,
                    data_points=data_points,
                    response_time_ms=elapsed
                )
            else:
                return DataFetchResult(
                    success=False,
                    source=self.config.name,
                    data_type=data_type,
                    error_message=f"HTTP {response.status_code}",
                    response_time_ms=elapsed
                )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=str(e),
                response_time_ms=elapsed
            )

    def parse_response(self, response_data: Any, data_type: str) -> List[DataPoint]:
        """Parse MinFin response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", [])
            for record in records:
                year = record.get("year", datetime.utcnow().year)
                month = record.get("month", 1)
                timestamp = datetime(year, month, 1)

                unit_mapping = {
                    "federal_budget_revenue": "трлн руб",
                    "federal_budget_expenditure": "трлн руб",
                    "budget_deficit": "трлн руб",
                    "nwf_size": "трлн руб",
                    "nwf_liquid": "трлн руб",
                    "government_debt": "трлн руб",
                    "external_debt": "млрд USD",
                    "oil_gas_revenue": "трлн руб",
                    "non_oil_gas_revenue": "трлн руб",
                }

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value"),
                    unit=unit_mapping.get(data_type, "трлн руб"),
                    metadata={
                        "plan": record.get("plan"),
                        "execution_pct": record.get("execution_pct"),
                        "yoy_change": record.get("yoy_change"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse MinFin response: {e}")

        return data_points


class MinEconomyClient(DataSourceClient):
    """
    Минэкономразвития (Ministry of Economic Development) Client
    Source for economic forecasts and national projects data
    """

    def __init__(self, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        config = DataSourceConfig(
            name="Минэкономразвития",
            name_en="Ministry of Economic Development",
            endpoint="https://economy.gov.ru/api/v1",
            auth_type=AuthenticationType.OAUTH2,
            data_types=[
                "gdp_forecast", "inflation_forecast",
                "national_projects", "project_status",
                "investment_forecast", "unemployment_forecast",
                "real_income_forecast", "structural_reform"
            ],
            update_frequency="quarterly",
            format=DataFormat.JSON,
            timeout=30,
            retry_attempts=3
        )
        config.client_id = client_id
        config.client_secret = client_secret
        super().__init__(config)

    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         **kwargs) -> DataFetchResult:
        """Fetch economic development data"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "gdp_forecast": "/forecasts/gdp",
            "inflation_forecast": "/forecasts/inflation",
            "national_projects": "/national-projects/list",
            "project_status": "/national-projects/status",
            "investment_forecast": "/forecasts/investment",
            "unemployment_forecast": "/forecasts/unemployment",
            "real_income_forecast": "/forecasts/real-income",
            "structural_reform": "/reforms/structural",
        }

        if data_type not in endpoint_mapping:
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=f"Unknown data type: {data_type}"
            )

        params = {}
        if "project_id" in kwargs:
            params["project_id"] = kwargs["project_id"]
        if "scenario" in kwargs:
            params["scenario"] = kwargs["scenario"]

        try:
            response = await self._make_request(
                "GET",
                endpoint_mapping[data_type],
                params=params
            )
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                data_points = self.parse_response(data, data_type)
                return DataFetchResult(
                    success=True,
                    source=self.config.name,
                    data_type=data_type,
                    data_points=data_points,
                    response_time_ms=elapsed
                )
            else:
                return DataFetchResult(
                    success=False,
                    source=self.config.name,
                    data_type=data_type,
                    error_message=f"HTTP {response.status_code}",
                    response_time_ms=elapsed
                )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=str(e),
                response_time_ms=elapsed
            )

    def parse_response(self, response_data: Any, data_type: str) -> List[DataPoint]:
        """Parse MinEconomy response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", response_data.get("projects", []))
            for record in records:
                year = record.get("year", datetime.utcnow().year)
                timestamp = datetime(year, 1, 1)

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value", record.get("completion_pct")),
                    unit=record.get("unit", "%"),
                    metadata={
                        "project_id": record.get("project_id"),
                        "project_name": record.get("name"),
                        "scenario": record.get("scenario"),
                        "status": record.get("status"),
                        "budget": record.get("budget"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse MinEconomy response: {e}")

        return data_points


class FTSCustomsClient(DataSourceClient):
    """
    Федеральная таможенная служба (Federal Customs Service) Client
    Source for trade and customs data
    """

    def __init__(self, certificate_path: Optional[str] = None,
                 certificate_password: Optional[str] = None):
        config = DataSourceConfig(
            name="ФТС России",
            name_en="Federal Customs Service",
            endpoint="https://customs.gov.ru/api/v1",
            auth_type=AuthenticationType.CERTIFICATE,
            data_types=[
                "import_total", "export_total", "trade_balance",
                "import_by_country", "export_by_country",
                "customs_duties", "trade_sanctions"
            ],
            update_frequency="monthly",
            format=DataFormat.JSON,
            timeout=60,
            retry_attempts=3
        )
        config.certificate_path = certificate_path
        config.certificate_password = certificate_password
        super().__init__(config)

    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         **kwargs) -> DataFetchResult:
        """Fetch customs and trade data"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "import_total": "/trade/import/total",
            "export_total": "/trade/export/total",
            "trade_balance": "/trade/balance",
            "import_by_country": "/trade/import/by-country",
            "export_by_country": "/trade/export/by-country",
            "customs_duties": "/revenue/duties",
            "trade_sanctions": "/sanctions/impact",
        }

        if data_type not in endpoint_mapping:
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=f"Unknown data type: {data_type}"
            )

        params = {}
        if start_date:
            params["period_from"] = start_date.strftime("%Y-%m")
        if end_date:
            params["period_to"] = end_date.strftime("%Y-%m")
        if "country" in kwargs:
            params["country"] = kwargs["country"]

        try:
            response = await self._make_request(
                "GET",
                endpoint_mapping[data_type],
                params=params
            )
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                data = response.json()
                data_points = self.parse_response(data, data_type)
                return DataFetchResult(
                    success=True,
                    source=self.config.name,
                    data_type=data_type,
                    data_points=data_points,
                    response_time_ms=elapsed
                )
            else:
                return DataFetchResult(
                    success=False,
                    source=self.config.name,
                    data_type=data_type,
                    error_message=f"HTTP {response.status_code}",
                    response_time_ms=elapsed
                )

        except Exception as e:
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=str(e),
                response_time_ms=elapsed
            )

    def parse_response(self, response_data: Any, data_type: str) -> List[DataPoint]:
        """Parse FTS response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", [])
            for record in records:
                period = record.get("period", "")
                if len(period) >= 7:
                    timestamp = datetime(int(period[:4]), int(period[5:7]), 1)
                else:
                    timestamp = datetime.utcnow()

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value"),
                    unit=record.get("unit", "млрд USD"),
                    metadata={
                        "country": record.get("country"),
                        "country_name": record.get("country_name"),
                        "product_group": record.get("product_group"),
                        "yoy_change": record.get("yoy_change"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse FTS response: {e}")

        return data_points


class RussiaDataSourceClient:
    """
    Unified Russia data source client factory
    Creates appropriate clients based on data source configuration
    """

    @staticmethod
    def create_client(source_name: str, credentials: Dict[str, Any]) -> DataSourceClient:
        """
        Create a data source client

        Args:
            source_name: Name of the data source
            credentials: Authentication credentials

        Returns:
            Configured DataSourceClient instance
        """
        clients = {
            "rosstat": RosstatClient,
            "central_bank": CBRClient,
            "ministry_finance": MinFinClient,
            "ministry_economy": MinEconomyClient,
            "fts_customs": FTSCustomsClient,
        }

        if source_name not in clients:
            raise ValueError(f"Unknown data source: {source_name}")

        client_class = clients[source_name]

        if client_class == RosstatClient:
            return client_class(api_key=credentials.get("api_key"))
        elif client_class == CBRClient:
            return client_class()  # No auth needed
        elif client_class in (MinFinClient, FTSCustomsClient):
            return client_class(
                certificate_path=credentials.get("certificate_path"),
                certificate_password=credentials.get("certificate_password")
            )
        elif client_class == MinEconomyClient:
            return client_class(
                client_id=credentials.get("client_id"),
                client_secret=credentials.get("client_secret")
            )

        return client_class()


class RussiaDataIngestionService(DataIngestionService):
    """
    Russia-specific data ingestion service
    Handles data collection from Russian government sources
    """

    def __init__(self, credentials: Dict[str, Dict[str, Any]], database_url: str):
        """
        Initialize Russia data ingestion service

        Args:
            credentials: Dict mapping source names to credential dicts
            database_url: Database connection URL for storage
        """
        self.database_url = database_url
        self._db_pool = None

        # Create clients for configured sources
        clients = []
        for source_name, creds in credentials.items():
            try:
                client = RussiaDataSourceClient.create_client(source_name, creds)
                clients.append(client)
            except Exception as e:
                logger.error(f"Failed to create client for {source_name}: {e}")

        super().__init__(clients)

    async def store_data(self, results: List[DataFetchResult]) -> int:
        """Store fetched data to database"""
        stored_count = 0

        for result in results:
            if not result.success:
                continue

            for data_point in result.data_points:
                try:
                    await self._store_data_point(data_point)
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Failed to store data point: {e}")

        return stored_count

    async def _store_data_point(self, data_point: DataPoint):
        """Store a single data point to database"""
        logger.debug(
            f"Storing: {data_point.source} - {data_point.data_type} = {data_point.value}"
        )

    async def fetch_crisis_indicators(self) -> Dict[str, Any]:
        """
        Fetch key crisis indicators for Russia
        Returns aggregated crisis assessment data
        """
        indicators = {}

        # Fetch key indicators
        try:
            # Inflation from Rosstat
            if "Росстат" in self.clients:
                result = await self.clients["Росстат"].fetch_data("inflation_official")
                if result.success and result.data_points:
                    indicators["inflation_official"] = result.data_points[-1].value

            # Key rate from CBR
            if "Центральный банк РФ" in self.clients:
                result = await self.clients["Центральный банк РФ"].fetch_data("key_rate")
                if result.success and result.data_points:
                    indicators["key_rate"] = result.data_points[-1].value

            # Budget deficit from MinFin
            if "Минфин России" in self.clients:
                result = await self.clients["Минфин России"].fetch_data("budget_deficit")
                if result.success and result.data_points:
                    indicators["budget_deficit"] = result.data_points[-1].value

                result = await self.clients["Минфин России"].fetch_data("nwf_liquid")
                if result.success and result.data_points:
                    indicators["nwf_liquid"] = result.data_points[-1].value

            # Forex from CBR
            if "Центральный банк РФ" in self.clients:
                result = await self.clients["Центральный банк РФ"].fetch_data("forex_usd")
                if result.success and result.data_points:
                    indicators["ruble_usd_rate"] = result.data_points[-1].value

        except Exception as e:
            logger.error(f"Error fetching crisis indicators: {e}")

        return indicators
