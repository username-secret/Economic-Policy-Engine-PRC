"""
Economic data ingestion for Chinese Economic Headwinds Fix
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import pandas as pd
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

class EconomicIndicator(Base):
    """Economic indicator data model"""
    __tablename__ = "economic_indicators"
    
    id = Column(String, primary_key=True)
    indicator_type = Column(String, nullable=False)
    region_code = Column(String, nullable=False)
    period = Column(String, nullable=False)  # YYYY-MM
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    source = Column(String, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)

class TradeFlow(Base):
    """Trade flow data model"""
    __tablename__ = "trade_flows"
    
    id = Column(String, primary_key=True)
    origin_country = Column(String, nullable=False)
    destination_country = Column(String, nullable=False)
    product_category = Column(String, nullable=False)
    period = Column(String, nullable=False)  # YYYY-MM
    value_usd = Column(Float, nullable=False)
    volume_metric = Column(Float, nullable=True)
    growth_yoy = Column(Float, nullable=True)
    barriers = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

class PropertyMarketData(Base):
    """Property market data model"""
    __tablename__ = "property_markets"
    
    id = Column(String, primary_key=True)
    region_code = Column(String, nullable=False)
    property_type = Column(String, nullable=False)
    period = Column(String, nullable=False)  # YYYY-MM
    price_index = Column(Float, nullable=False)
    volume_index = Column(Float, nullable=False)
    vacancy_rate = Column(Float, nullable=False)
    rental_yield = Column(Float, nullable=False)
    debt_to_value = Column(Float, nullable=False)
    affordability_index = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

class EconomicDataIngestor:
    """
    Ingests economic data from various sources
    """
    
    def __init__(self, database_url: str = "postgresql://localhost/chinese_economic_data"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Data sources configuration
        self.data_sources = {
            "nbs": {
                "name": "National Bureau of Statistics",
                "api_base": "https://data.stats.gov.cn/api",
                "indicators": ["gdp", "cpi", "ppi", "retail_sales", "industrial_output"]
            },
            "customs": {
                "name": "Customs Administration",
                "api_base": "https://www.customs.gov.cn/api",
                "indicators": ["imports", "exports", "trade_balance"]
            },
            "pbc": {
                "name": "People's Bank of China",
                "api_base": "https://www.pbc.gov.cn/api",
                "indicators": ["interest_rates", "money_supply", "foreign_reserves"]
            }
        }
    
    async def ingest_all_data(self, start_date: str = "2023-01", end_date: str = "2024-01"):
        """
        Ingest data from all sources for specified period
        
        Args:
            start_date: Start period (YYYY-MM)
            end_date: End period (YYYY-MM)
        """
        logger.info(f"Starting data ingestion for period {start_date} to {end_date}")
        
        tasks = [
            self.ingest_economic_indicators(start_date, end_date),
            self.ingest_trade_flows(start_date, end_date),
            self.ingest_property_market_data(start_date, end_date)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = 0
        failed = 0
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                logger.error(f"Data ingestion failed: {result}")
            else:
                successful += 1
        
        logger.info(f"Data ingestion completed: {successful} successful, {failed} failed")
        return {"successful": successful, "failed": failed}
    
    async def ingest_economic_indicators(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Ingest economic indicators from NBS
        
        Args:
            start_date: Start period (YYYY-MM)
            end_date: End period (YYYY-MM)
        """
        logger.info(f"Ingesting economic indicators from {start_date} to {end_date}")
        
        # Generate periods
        periods = self._generate_periods(start_date, end_date)
        
        # Mock data for demonstration
        # In production, this would make API calls to NBS
        indicators_data = []
        
        for period in periods:
            # GDP growth
            indicators_data.append({
                "id": f"GDP-{period}",
                "indicator_type": "gdp_growth",
                "region_code": "CN",
                "period": period,
                "value": 5.2 + (random.uniform(-0.5, 0.5) if period != "2024-01" else 0),
                "unit": "percent",
                "source": "nbs",
                "metadata": {"seasonally_adjusted": True}
            })
            
            # CPI
            indicators_data.append({
                "id": f"CPI-{period}",
                "indicator_type": "cpi",
                "region_code": "CN",
                "period": period,
                "value": 2.1 + (random.uniform(-0.3, 0.3) if period != "2024-01" else 0),
                "unit": "percent",
                "source": "nbs",
                "metadata": {"core_cpi": 1.8}
            })
            
            # Industrial output
            indicators_data.append({
                "id": f"INDUSTRIAL-{period}",
                "indicator_type": "industrial_output",
                "region_code": "CN",
                "period": period,
                "value": 6.1 + (random.uniform(-1.0, 1.0) if period != "2024-01" else 0),
                "unit": "percent",
                "source": "nbs",
                "metadata": {"manufacturing": 6.5, "mining": 3.2}
            })
            
            # Retail sales
            indicators_data.append({
                "id": f"RETAIL-{period}",
                "indicator_type": "retail_sales",
                "region_code": "CN",
                "period": period,
                "value": 7.3 + (random.uniform(-2.0, 2.0) if period != "2024-01" else 0),
                "unit": "percent",
                "source": "nbs",
                "metadata": {"online_retail": 15.2, "offline_retail": 5.1}
            })
        
        # Save to database
        session = self.Session()
        try:
            for data in indicators_data:
                indicator = EconomicIndicator(**data)
                session.merge(indicator)  # Update if exists
            session.commit()
            logger.info(f"Saved {len(indicators_data)} economic indicators")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving economic indicators: {e}")
            raise
        finally:
            session.close()
        
        return {"indicators": len(indicators_data), "periods": len(periods)}
    
    async def ingest_trade_flows(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Ingest trade flow data from Customs Administration
        
        Args:
            start_date: Start period (YYYY-MM)
            end_date: End period (YYYY-MM)
        """
        logger.info(f"Ingesting trade flows from {start_date} to {end_date}")
        
        periods = self._generate_periods(start_date, end_date)
        
        # Major trade partners
        trade_partners = [
            {"code": "US", "name": "United States"},
            {"code": "EU", "name": "European Union"},
            {"code": "JP", "name": "Japan"},
            {"code": "KR", "name": "South Korea"},
            {"code": "VN", "name": "Vietnam"},
            {"code": "IN", "name": "India"},
            {"code": "RU", "name": "Russia"},
            {"code": "AU", "name": "Australia"}
        ]
        
        # Product categories
        product_categories = [
            "electronics", "machinery", "textiles", "chemicals",
            "vehicles", "pharmaceuticals", "agricultural", "metals"
        ]
        
        trade_flows_data = []
        
        for period in periods:
            for partner in trade_partners:
                for product in product_categories:
                    # Generate realistic trade values
                    base_value = random.uniform(10000000, 500000000)  # 10M to 500M USD
                    
                    # Adjust based on partner and product
                    if partner["code"] == "US":
                        base_value *= 1.5
                    elif partner["code"] == "EU":
                        base_value *= 1.3
                    
                    if product == "electronics":
                        base_value *= 2.0
                    elif product == "pharmaceuticals":
                        base_value *= 0.5
                    
                    # Add some variation
                    value_usd = base_value * random.uniform(0.9, 1.1)
                    
                    # Calculate growth (simulated)
                    growth_yoy = random.uniform(-5.0, 15.0)
                    
                    trade_flows_data.append({
                        "id": f"TRADE-{period}-CN-{partner['code']}-{product}",
                        "origin_country": "CN",
                        "destination_country": partner["code"],
                        "product_category": product,
                        "period": period,
                        "value_usd": value_usd,
                        "growth_yoy": growth_yoy,
                        "barriers": self._generate_trade_barriers(partner["code"], product)
                    })
        
        # Save to database
        session = self.Session()
        try:
            for data in trade_flows_data:
                trade_flow = TradeFlow(**data)
                session.merge(trade_flow)
            session.commit()
            logger.info(f"Saved {len(trade_flows_data)} trade flows")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving trade flows: {e}")
            raise
        finally:
            session.close()
        
        return {"trade_flows": len(trade_flows_data)}
    
    async def ingest_property_market_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Ingest property market data
        
        Args:
            start_date: Start period (YYYY-MM)
            end_date: End period (YYYY-MM)
        """
        logger.info(f"Ingesting property market data from {start_date} to {end_date}")
        
        periods = self._generate_periods(start_date, end_date)
        
        # Major Chinese cities
        cities = [
            {"code": "BJ", "name": "Beijing", "tier": 1},
            {"code": "SH", "name": "Shanghai", "tier": 1},
            {"code": "SZ", "name": "Shenzhen", "tier": 1},
            {"code": "GZ", "name": "Guangzhou", "tier": 1},
            {"code": "HZ", "name": "Hangzhou", "tier": 2},
            {"code": "NJ", "name": "Nanjing", "tier": 2},
            {"code": "CD", "name": "Chengdu", "tier": 2},
            {"code": "CQ", "name": "Chongqing", "tier": 2}
        ]
        
        property_types = ["residential", "commercial", "industrial"]
        
        property_data = []
        
        for period in periods:
            for city in cities:
                for property_type in property_types:
                    # Base values based on city tier and property type
                    base_price_index = 100.0
                    
                    # Adjust for city tier
                    if city["tier"] == 1:
                        base_price_index *= 1.5
                    elif city["tier"] == 2:
                        base_price_index *= 1.2
                    
                    # Adjust for property type
                    if property_type == "commercial":
                        base_price_index *= 0.8
                    elif property_type == "industrial":
                        base_price_index *= 0.6
                    
                    # Add time trend (slight decline for recent periods)
                    trend_factor = 1.0
                    if period >= "2023-07":
                        months_from_mid_2023 = (int(period[:4]) - 2023) * 12 + (int(period[5:7]) - 7)
                        trend_factor = 1.0 - (months_from_mid_2023 * 0.01)  # 1% decline per month
                    
                    price_index = base_price_index * trend_factor * random.uniform(0.95, 1.05)
                    
                    # Generate other metrics
                    volume_index = random.uniform(60.0, 90.0) * trend_factor
                    vacancy_rate = random.uniform(8.0, 20.0)
                    rental_yield = random.uniform(1.5, 3.5)
                    debt_to_value = random.uniform(50.0, 80.0)
                    affordability_index = random.uniform(30.0, 70.0)
                    
                    property_data.append({
                        "id": f"PROP-{period}-{city['code']}-{property_type}",
                        "region_code": city["code"],
                        "property_type": property_type,
                        "period": period,
                        "price_index": round(price_index, 1),
                        "volume_index": round(volume_index, 1),
                        "vacancy_rate": round(vacancy_rate, 1),
                        "rental_yield": round(rental_yield, 1),
                        "debt_to_value": round(debt_to_value, 1),
                        "affordability_index": round(affordability_index, 1)
                    })
        
        # Save to database
        session = self.Session()
        try:
            for data in property_data:
                property_market = PropertyMarketData(**data)
                session.merge(property_market)
            session.commit()
            logger.info(f"Saved {len(property_data)} property market records")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving property market data: {e}")
            raise
        finally:
            session.close()
        
        return {"property_records": len(property_data)}
    
    def _generate_periods(self, start_date: str, end_date: str) -> List[str]:
        """Generate list of periods between start and end dates"""
        periods = []
        
        start_year, start_month = map(int, start_date.split("-"))
        end_year, end_month = map(int, end_date.split("-"))
        
        current_year = start_year
        current_month = start_month
        
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            periods.append(f"{current_year}-{current_month:02d}")
            
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        return periods
    
    def _generate_trade_barriers(self, country_code: str, product: str) -> List[str]:
        """Generate realistic trade barriers based on country and product"""
        barriers = []
        
        # US barriers
        if country_code == "US":
            if product in ["electronics", "machinery"]:
                barriers.append("tariff_25pc")
                barriers.append("export_control")
            if product == "pharmaceuticals":
                barriers.append("fda_approval")
        
        # EU barriers
        elif country_code == "EU":
            if product in ["electronics", "vehicles"]:
                barriers.append("ce_certification")
                barriers.append("rohs_compliance")
            if product == "agricultural":
                barriers.append("safety_standards")
                barriers.append("organic_certification")
        
        # General barriers
        if random.random() > 0.7:
            barriers.append("customs_inspection")
        
        return barriers
    
    async def get_economic_indicators(self, indicator_type: str = None, 
                                      region_code: str = "CN", 
                                      start_period: str = None,
                                      end_period: str = None) -> pd.DataFrame:
        """
        Get economic indicators from database
        
        Args:
            indicator_type: Type of indicator (optional)
            region_code: Region code (default: CN)
            start_period: Start period (YYYY-MM)
            end_period: End period (YYYY-MM)
            
        Returns:
            DataFrame with economic indicators
        """
        session = self.Session()
        try:
            query = session.query(EconomicIndicator).filter(
                EconomicIndicator.region_code == region_code
            )
            
            if indicator_type:
                query = query.filter(EconomicIndicator.indicator_type == indicator_type)
            
            if start_period:
                query = query.filter(EconomicIndicator.period >= start_period)
            
            if end_period:
                query = query.filter(EconomicIndicator.period <= end_period)
            
            results = query.order_by(EconomicIndicator.period).all()
            
            # Convert to DataFrame
            data = []
            for result in results:
                data.append({
                    "period": result.period,
                    "indicator_type": result.indicator
