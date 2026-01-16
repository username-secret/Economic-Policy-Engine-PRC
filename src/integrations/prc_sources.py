"""
PRC (People's Republic of China) Government Data Source Integrations
Implements connections to Chinese government data systems
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


class NBSClient(DataSourceClient):
    """
    国家统计局 (National Bureau of Statistics) Client
    Primary source for China's economic indicators
    """

    def __init__(self, api_key: Optional[str] = None):
        config = DataSourceConfig(
            name="国家统计局",
            name_en="National Bureau of Statistics",
            endpoint="https://data.stats.gov.cn/api/v1",
            auth_type=AuthenticationType.API_KEY,
            data_types=[
                "gdp", "gdp_growth", "cpi", "ppi",
                "industrial_output", "retail_sales",
                "fixed_investment", "unemployment",
                "population", "income_per_capita"
            ],
            update_frequency="monthly",
            format=DataFormat.JSON,
            timeout=30,
            retry_attempts=3
        )
        config.api_key = api_key
        super().__init__(config)

        # Mapping from data type to NBS indicator codes
        self._indicator_mapping = {
            "gdp": "A020101",
            "gdp_growth": "A020102",
            "cpi": "A090101",
            "ppi": "A090301",
            "industrial_output": "A040101",
            "retail_sales": "A060101",
            "fixed_investment": "A050101",
            "unemployment": "A020901",
            "population": "A030101",
            "income_per_capita": "A080101",
        }

    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         region: str = "00") -> DataFetchResult:
        """
        Fetch data from NBS

        Args:
            data_type: Type of indicator (e.g., 'gdp', 'cpi')
            start_date: Start date for data
            end_date: End date for data
            region: Region code ('00' for national)
        """
        start_time = datetime.utcnow()

        if data_type not in self._indicator_mapping:
            return DataFetchResult(
                success=False,
                source=self.config.name,
                data_type=data_type,
                error_message=f"Unknown data type: {data_type}"
            )

        indicator_code = self._indicator_mapping[data_type]

        # Build query parameters
        params = {
            "m": "QueryData",
            "dbcode": "hgyd",  # Monthly data
            "rowcode": "zb",
            "colcode": "sj",
            "wds": f"[{{'wdcode':'reg','valuecode':'{region}'}}]",
            "dfwds": f"[{{'wdcode':'zb','valuecode':'{indicator_code}'}}]",
        }

        if start_date:
            params["dfwds"] += f"&startTime={start_date.strftime('%Y%m')}"
        if end_date:
            params["dfwds"] += f"&endTime={end_date.strftime('%Y%m')}"

        try:
            response = await self._make_request("GET", "/data", params=params)
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
        """Parse NBS response into DataPoint objects"""
        data_points = []

        try:
            # NBS returns data in a specific format
            if "returndata" not in response_data:
                return data_points

            return_data = response_data["returndata"]
            data_nodes = return_data.get("datanodes", [])

            for node in data_nodes:
                if "data" not in node:
                    continue

                data = node["data"]
                wds = {w["wdcode"]: w["valuecode"] for w in node.get("wds", [])}

                # Parse time period (format: YYYYMM)
                time_str = wds.get("sj", "")
                if len(time_str) == 6:
                    timestamp = datetime(int(time_str[:4]), int(time_str[4:6]), 1)
                else:
                    timestamp = datetime.utcnow()

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=data.get("data", data.get("strdata")),
                    unit=data.get("unit"),
                    region=wds.get("reg", "00"),
                    metadata={
                        "indicator_code": wds.get("zb"),
                        "has_data": data.get("hasdata", True)
                    },
                    raw_data=node
                ))

        except Exception as e:
            logger.error(f"Failed to parse NBS response: {e}")

        return data_points


class CustomsClient(DataSourceClient):
    """
    海关总署 (General Administration of Customs) Client
    Source for China's trade and customs data
    """

    def __init__(self, certificate_path: Optional[str] = None,
                 certificate_password: Optional[str] = None):
        config = DataSourceConfig(
            name="海关总署",
            name_en="General Administration of Customs",
            endpoint="https://www.customs.gov.cn/api/v1",
            auth_type=AuthenticationType.CERTIFICATE,
            data_types=[
                "import_total", "export_total", "trade_balance",
                "import_by_country", "export_by_country",
                "import_by_product", "export_by_product",
                "tariff_revenue", "customs_clearance"
            ],
            update_frequency="daily",
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
        """Fetch trade data from Customs"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "import_total": "/trade/import/total",
            "export_total": "/trade/export/total",
            "trade_balance": "/trade/balance",
            "import_by_country": "/trade/import/by-country",
            "export_by_country": "/trade/export/by-country",
            "import_by_product": "/trade/import/by-product",
            "export_by_product": "/trade/export/by-product",
            "tariff_revenue": "/revenue/tariff",
            "customs_clearance": "/clearance/statistics",
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
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")

        # Add optional filters
        if "country_code" in kwargs:
            params["country"] = kwargs["country_code"]
        if "hs_code" in kwargs:
            params["hs_code"] = kwargs["hs_code"]

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
        """Parse Customs response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", [])
            for record in records:
                timestamp = datetime.fromisoformat(record.get("period", datetime.utcnow().isoformat()))

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value"),
                    unit=record.get("unit", "USD"),
                    region=record.get("region"),
                    metadata={
                        "country": record.get("country"),
                        "hs_code": record.get("hs_code"),
                        "product_name": record.get("product_name"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse Customs response: {e}")

        return data_points


class PBOCClient(DataSourceClient):
    """
    中国人民银行 (People's Bank of China) Client
    Source for monetary and financial data
    """

    def __init__(self, certificate_path: Optional[str] = None,
                 certificate_password: Optional[str] = None):
        config = DataSourceConfig(
            name="中国人民银行",
            name_en="People's Bank of China",
            endpoint="https://www.pbc.gov.cn/api/v1",
            auth_type=AuthenticationType.CERTIFICATE,
            data_types=[
                "lpr", "mlf_rate", "rrr",
                "m0", "m1", "m2",
                "forex_reserves", "gold_reserves",
                "loan_growth", "deposit_growth",
                "forex_rate_usd", "forex_rate_eur"
            ],
            update_frequency="daily",
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
        """Fetch monetary data from PBOC"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "lpr": "/rates/lpr",
            "mlf_rate": "/rates/mlf",
            "rrr": "/rates/rrr",
            "m0": "/money-supply/m0",
            "m1": "/money-supply/m1",
            "m2": "/money-supply/m2",
            "forex_reserves": "/reserves/forex",
            "gold_reserves": "/reserves/gold",
            "loan_growth": "/credit/loans",
            "deposit_growth": "/credit/deposits",
            "forex_rate_usd": "/forex/usd-cny",
            "forex_rate_eur": "/forex/eur-cny",
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
            params["start"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end"] = end_date.strftime("%Y-%m-%d")

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
        """Parse PBOC response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", [])
            for record in records:
                timestamp = datetime.fromisoformat(
                    record.get("date", record.get("period", datetime.utcnow().isoformat()))
                )

                # Determine unit based on data type
                unit_mapping = {
                    "lpr": "%",
                    "mlf_rate": "%",
                    "rrr": "%",
                    "m0": "亿元",
                    "m1": "亿元",
                    "m2": "亿元",
                    "forex_reserves": "亿美元",
                    "gold_reserves": "吨",
                    "loan_growth": "%",
                    "deposit_growth": "%",
                    "forex_rate_usd": "CNY/USD",
                    "forex_rate_eur": "CNY/EUR",
                }

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value"),
                    unit=unit_mapping.get(data_type),
                    metadata={
                        "term": record.get("term"),  # For LPR (1Y, 5Y)
                        "adjustment": record.get("adjustment"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse PBOC response: {e}")

        return data_points


class NDRCClient(DataSourceClient):
    """
    国家发展和改革委员会 (NDRC) Client
    Source for development planning and price data
    """

    def __init__(self, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        config = DataSourceConfig(
            name="国家发展和改革委员会",
            name_en="National Development and Reform Commission",
            endpoint="https://www.ndrc.gov.cn/api/v1",
            auth_type=AuthenticationType.OAUTH2,
            data_types=[
                "fyp_targets", "fyp_progress",
                "price_index", "energy_consumption",
                "project_approvals", "regional_development",
                "industrial_policy", "investment_guidance"
            ],
            update_frequency="weekly",
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
        """Fetch development planning data from NDRC"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "fyp_targets": "/planning/fyp/targets",
            "fyp_progress": "/planning/fyp/progress",
            "price_index": "/prices/index",
            "energy_consumption": "/energy/consumption",
            "project_approvals": "/projects/approvals",
            "regional_development": "/regional/development",
            "industrial_policy": "/industrial/policy",
            "investment_guidance": "/investment/guidance",
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
            params["from"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["to"] = end_date.strftime("%Y-%m-%d")
        if "fyp_number" in kwargs:
            params["fyp"] = kwargs["fyp_number"]
        if "region" in kwargs:
            params["region"] = kwargs["region"]

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
        """Parse NDRC response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", [])
            for record in records:
                timestamp = datetime.fromisoformat(
                    record.get("date", record.get("period", datetime.utcnow().isoformat()))
                )

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value"),
                    unit=record.get("unit"),
                    region=record.get("region"),
                    metadata={
                        "target_name": record.get("target_name"),
                        "fyp_number": record.get("fyp_number"),
                        "category": record.get("category"),
                        "status": record.get("status"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse NDRC response: {e}")

        return data_points


class MOFClient(DataSourceClient):
    """
    财政部 (Ministry of Finance) Client
    Source for fiscal and budget data
    """

    def __init__(self, certificate_path: Optional[str] = None,
                 certificate_password: Optional[str] = None):
        config = DataSourceConfig(
            name="财政部",
            name_en="Ministry of Finance",
            endpoint="https://www.mof.gov.cn/api/v1",
            auth_type=AuthenticationType.CERTIFICATE,
            data_types=[
                "fiscal_revenue", "fiscal_expenditure",
                "tax_revenue", "non_tax_revenue",
                "government_debt", "local_government_debt",
                "transfer_payments", "budget_execution"
            ],
            update_frequency="monthly",
            format=DataFormat.XML,
            timeout=30,
            retry_attempts=3
        )
        config.certificate_path = certificate_path
        config.certificate_password = certificate_password
        super().__init__(config)

    def _get_headers(self) -> Dict[str, str]:
        """Override headers for XML format"""
        headers = super()._get_headers()
        headers["Accept"] = "application/xml"
        return headers

    async def fetch_data(self, data_type: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         **kwargs) -> DataFetchResult:
        """Fetch fiscal data from MOF"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "fiscal_revenue": "/budget/revenue",
            "fiscal_expenditure": "/budget/expenditure",
            "tax_revenue": "/tax/revenue",
            "non_tax_revenue": "/tax/non-tax",
            "government_debt": "/debt/central",
            "local_government_debt": "/debt/local",
            "transfer_payments": "/transfers/intergovernmental",
            "budget_execution": "/budget/execution",
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
            params["month"] = start_date.month
        if "region" in kwargs:
            params["region"] = kwargs["region"]

        try:
            response = await self._make_request(
                "GET",
                endpoint_mapping[data_type],
                params=params
            )
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                # Parse XML response
                data_points = self.parse_response(response.text, data_type)
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
        """Parse MOF XML response into DataPoint objects"""
        data_points = []

        try:
            root = ET.fromstring(response_data)

            for record in root.findall(".//record"):
                year = record.findtext("year", "")
                month = record.findtext("month", "1")
                timestamp = datetime(int(year), int(month), 1) if year else datetime.utcnow()

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=float(record.findtext("value", "0")),
                    unit=record.findtext("unit", "亿元"),
                    region=record.findtext("region"),
                    metadata={
                        "category": record.findtext("category"),
                        "subcategory": record.findtext("subcategory"),
                        "yoy_growth": record.findtext("yoy_growth"),
                    },
                    raw_data={"xml": ET.tostring(record, encoding="unicode")}
                ))

        except Exception as e:
            logger.error(f"Failed to parse MOF XML response: {e}")

        return data_points


class SAFEClient(DataSourceClient):
    """
    国家外汇管理局 (SAFE) Client
    Source for forex and balance of payments data
    """

    def __init__(self, certificate_path: Optional[str] = None,
                 certificate_password: Optional[str] = None):
        config = DataSourceConfig(
            name="国家外汇管理局",
            name_en="State Administration of Foreign Exchange",
            endpoint="https://www.safe.gov.cn/api/v1",
            auth_type=AuthenticationType.CERTIFICATE,
            data_types=[
                "forex_reserves", "balance_of_payments",
                "current_account", "capital_account",
                "fdi_inflow", "fdi_outflow",
                "external_debt", "forex_settlement"
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
        """Fetch forex data from SAFE"""
        start_time = datetime.utcnow()

        endpoint_mapping = {
            "forex_reserves": "/reserves/foreign-exchange",
            "balance_of_payments": "/bop/summary",
            "current_account": "/bop/current-account",
            "capital_account": "/bop/capital-account",
            "fdi_inflow": "/investment/fdi-in",
            "fdi_outflow": "/investment/fdi-out",
            "external_debt": "/debt/external",
            "forex_settlement": "/settlement/statistics",
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
            params["start_period"] = start_date.strftime("%Y-%m")
        if end_date:
            params["end_period"] = end_date.strftime("%Y-%m")

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
        """Parse SAFE response into DataPoint objects"""
        data_points = []

        try:
            records = response_data.get("data", [])
            for record in records:
                period = record.get("period", "")
                if len(period) >= 7:  # YYYY-MM format
                    timestamp = datetime(int(period[:4]), int(period[5:7]), 1)
                else:
                    timestamp = datetime.utcnow()

                data_points.append(DataPoint(
                    source=self.config.name,
                    data_type=data_type,
                    timestamp=timestamp,
                    value=record.get("value"),
                    unit=record.get("unit", "亿美元"),
                    metadata={
                        "category": record.get("category"),
                        "subcategory": record.get("subcategory"),
                        "currency": record.get("currency", "USD"),
                    },
                    raw_data=record
                ))

        except Exception as e:
            logger.error(f"Failed to parse SAFE response: {e}")

        return data_points


class PRCDataSourceClient:
    """
    Unified PRC data source client factory
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
            "national_bureau_statistics": NBSClient,
            "customs_administration": CustomsClient,
            "peoples_bank": PBOCClient,
            "ndrc": NDRCClient,
            "ministry_finance": MOFClient,
            "safe": SAFEClient,
        }

        if source_name not in clients:
            raise ValueError(f"Unknown data source: {source_name}")

        client_class = clients[source_name]

        if client_class == NBSClient:
            return client_class(api_key=credentials.get("api_key"))
        elif client_class in (CustomsClient, PBOCClient, MOFClient, SAFEClient):
            return client_class(
                certificate_path=credentials.get("certificate_path"),
                certificate_password=credentials.get("certificate_password")
            )
        elif client_class == NDRCClient:
            return client_class(
                client_id=credentials.get("client_id"),
                client_secret=credentials.get("client_secret")
            )

        return client_class()


class PRCDataIngestionService(DataIngestionService):
    """
    PRC-specific data ingestion service
    Handles data collection from Chinese government sources
    """

    def __init__(self, credentials: Dict[str, Dict[str, Any]], database_url: str):
        """
        Initialize PRC data ingestion service

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
                client = PRCDataSourceClient.create_client(source_name, creds)
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
        # This would use the database connection to store
        # For now, just log
        logger.debug(
            f"Storing: {data_point.source} - {data_point.data_type} = {data_point.value}"
        )
