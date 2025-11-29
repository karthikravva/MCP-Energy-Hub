"""
ISO/RTO Real-time Data Collectors
Collects high-resolution data directly from ISO APIs
"""

import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.ingestion.base import BaseCollector
from app.ingestion.carbon_calculator import CarbonIntensityCalculator
from app.models.database import GridMetricsDB

logger = logging.getLogger(__name__)
settings = get_settings()


class ISOCollector(BaseCollector):
    """
    Base class for ISO-specific collectors
    Each ISO has different API formats and endpoints
    """

    def __init__(self, session: AsyncSession, api_key: Optional[str] = None):
        super().__init__(session, api_key)
        self.carbon_calc = CarbonIntensityCalculator()

    @abstractmethod
    def get_region_id(self) -> str:
        """Return the region ID for this ISO"""
        pass


class CAISOCollector(ISOCollector):
    """
    California ISO (CAISO) data collector
    API: OASIS (Open Access Same-time Information System)
    """

    def __init__(self, session: AsyncSession, api_key: Optional[str] = None):
        super().__init__(session, api_key or settings.caiso_api_key)
        self.source_name = "CAISO"
        self.base_url = "http://oasis.caiso.com/oasisapi/SingleZip"

    def get_region_id(self) -> str:
        return "CAISO"

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect real-time data from CAISO OASIS API
        """
        # CAISO provides data via XML/ZIP downloads
        # For MVP, we'll use a simplified approach

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        params = {
            "queryname": "SLD_REN_FCST",  # Renewable forecast
            "startdatetime": start_date.strftime("%Y%m%dT%H:00-0000"),
            "enddatetime": end_date.strftime("%Y%m%dT%H:00-0000"),
            "version": 1,
        }

        try:
            # Note: CAISO returns ZIP files with XML
            # This is a simplified implementation
            logger.info("CAISO collection - using EIA fallback for MVP")
            return []
        except Exception as e:
            logger.error(f"Error collecting CAISO data: {e}")
            return []

    async def transform(self, raw_data: List[Dict]) -> List[Dict[str, Any]]:
        """Transform CAISO data to normalized format"""
        return []

    async def load(self, records: List[Dict[str, Any]]) -> int:
        """Load CAISO records"""
        return 0


class ERCOTCollector(ISOCollector):
    """
    Electric Reliability Council of Texas (ERCOT) data collector
    API: ERCOT Public API
    """

    def __init__(self, session: AsyncSession, api_key: Optional[str] = None):
        super().__init__(session, api_key or settings.ercot_api_key)
        self.source_name = "ERCOT"
        self.base_url = "https://www.ercot.com/api/1/services/read"

    def get_region_id(self) -> str:
        return "ERCOT"

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect real-time data from ERCOT API
        """
        all_data = []

        # System-wide demand
        try:
            demand_url = f"{self.base_url}/SystemWideDemand.json"
            demand_data = await self.fetch_json(demand_url)
            all_data.append({"type": "demand", "data": demand_data})
        except Exception as e:
            logger.warning(f"ERCOT demand collection failed: {e}")

        # Generation by fuel
        try:
            fuel_url = f"{self.base_url}/FuelMix.json"
            fuel_data = await self.fetch_json(fuel_url)
            all_data.append({"type": "fuel_mix", "data": fuel_data})
        except Exception as e:
            logger.warning(f"ERCOT fuel mix collection failed: {e}")

        return all_data

    async def transform(self, raw_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Transform ERCOT data to normalized format
        """
        if not raw_data:
            return []

        timestamp = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        metrics = {
            "timestamp_utc": timestamp,
            "region_id": "ERCOT",
            "load_mw": 0,
            "total_generation_mw": 0,
            "generation_by_fuel": {
                "natural_gas_mw": 0,
                "coal_mw": 0,
                "nuclear_mw": 0,
                "wind_mw": 0,
                "solar_mw": 0,
                "hydro_mw": 0,
                "other_mw": 0,
            },
            "net_interchange_mw": 0,
            "source": "ERCOT",
        }

        for record in raw_data:
            if record["type"] == "demand":
                data = record.get("data", {})
                # Parse ERCOT demand format
                if "SystemWideDemand" in data:
                    metrics["load_mw"] = float(
                        data["SystemWideDemand"].get("Demand", 0))

            elif record["type"] == "fuel_mix":
                data = record.get("data", {})
                # Parse ERCOT fuel mix format
                if "FuelMix" in data:
                    for fuel in data["FuelMix"]:
                        fuel_type = fuel.get("FuelType", "").upper()
                        gen_mw = float(fuel.get("GenMW", 0))

                        if "GAS" in fuel_type:
                            metrics["generation_by_fuel"]["natural_gas_mw"] += gen_mw
                        elif "COAL" in fuel_type:
                            metrics["generation_by_fuel"]["coal_mw"] += gen_mw
                        elif "NUCLEAR" in fuel_type:
                            metrics["generation_by_fuel"]["nuclear_mw"] += gen_mw
                        elif "WIND" in fuel_type:
                            metrics["generation_by_fuel"]["wind_mw"] += gen_mw
                        elif "SOLAR" in fuel_type:
                            metrics["generation_by_fuel"]["solar_mw"] += gen_mw
                        elif "HYDRO" in fuel_type:
                            metrics["generation_by_fuel"]["hydro_mw"] += gen_mw
                        else:
                            metrics["generation_by_fuel"]["other_mw"] += gen_mw

                        metrics["total_generation_mw"] += gen_mw

        # Calculate derived metrics
        gen = metrics["generation_by_fuel"]
        total_gen = metrics["total_generation_mw"]

        renewable_mw = gen["wind_mw"] + gen["solar_mw"] + gen["hydro_mw"]
        metrics["renewable_fraction_pct"] = (
            (renewable_mw / total_gen * 100) if total_gen > 0 else 0
        )
        metrics["carbon_intensity_kg_per_mwh"] = self.carbon_calc.calculate(
            gen, total_gen)

        return [metrics] if metrics["load_mw"] > 0 or metrics["total_generation_mw"] > 0 else []

    async def load(self, records: List[Dict[str, Any]]) -> int:
        """Load ERCOT records using upsert"""
        if not records:
            return 0

        count = 0
        for record in records:
            stmt = insert(GridMetricsDB).values(
                timestamp_utc=record["timestamp_utc"],
                region_id=record["region_id"],
                load_mw=record["load_mw"],
                total_generation_mw=record["total_generation_mw"],
                generation_by_fuel=record["generation_by_fuel"],
                net_interchange_mw=record["net_interchange_mw"],
                renewable_fraction_pct=record["renewable_fraction_pct"],
                carbon_intensity_kg_per_mwh=record["carbon_intensity_kg_per_mwh"],
                source=record["source"],
            )

            stmt = stmt.on_conflict_do_update(
                constraint="uq_grid_metrics_region_time",
                set_={
                    "load_mw": stmt.excluded.load_mw,
                    "total_generation_mw": stmt.excluded.total_generation_mw,
                    "generation_by_fuel": stmt.excluded.generation_by_fuel,
                    "renewable_fraction_pct": stmt.excluded.renewable_fraction_pct,
                    "carbon_intensity_kg_per_mwh": stmt.excluded.carbon_intensity_kg_per_mwh,
                }
            )

            await self.session.execute(stmt)
            count += 1

        await self.session.commit()
        return count


class PJMCollector(ISOCollector):
    """
    PJM Interconnection data collector
    API: Data Miner 2
    """

    def __init__(self, session: AsyncSession, api_key: Optional[str] = None):
        super().__init__(session, api_key or settings.pjm_api_key)
        self.source_name = "PJM"
        self.base_url = "https://api.pjm.com/api/v1"

    def get_region_id(self) -> str:
        return "PJM"

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect real-time data from PJM API"""
        # PJM requires subscription for real-time data
        logger.info("PJM collection - using EIA fallback for MVP")
        return []

    async def transform(self, raw_data: List[Dict]) -> List[Dict[str, Any]]:
        return []

    async def load(self, records: List[Dict[str, Any]]) -> int:
        return 0


# Factory function to get appropriate collector
def get_iso_collector(iso_name: str, session: AsyncSession) -> Optional[ISOCollector]:
    """
    Factory function to get the appropriate ISO collector
    """
    collectors = {
        "CAISO": CAISOCollector,
        "ERCOT": ERCOTCollector,
        "PJM": PJMCollector,
    }

    collector_class = collectors.get(iso_name.upper())
    if collector_class:
        return collector_class(session)
    return None
