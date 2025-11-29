"""
EIA (Energy Information Administration) Data Collector
Collects real-time grid data from EIA Open Data API
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.ingestion.base import BaseCollector
from app.ingestion.carbon_calculator import CarbonIntensityCalculator
from app.models.database import GridMetricsDB, GridRegionDB

logger = logging.getLogger(__name__)
settings = get_settings()


# EIA Balancing Authority mappings - includes both ISO codes and utility codes
BA_REGION_MAP = {
    # Main ISO/RTO codes (used in demand data)
    "ERCO": {"region_id": "ERCOT", "name": "Electric Reliability Council of Texas", "timezone": "US/Central", "lat": 31.0, "lon": -99.0, "states": ["TX"], "type": "ISO"},
    "CISO": {"region_id": "CAISO", "name": "California ISO", "timezone": "US/Pacific", "lat": 37.0, "lon": -120.0, "states": ["CA"], "type": "ISO"},
    "PJM": {"region_id": "PJM", "name": "PJM Interconnection", "timezone": "US/Eastern", "lat": 40.0, "lon": -77.0, "states": ["PA", "NJ", "MD", "DE", "VA", "WV", "OH", "DC"], "type": "ISO"},
    "NYIS": {"region_id": "NYISO", "name": "New York ISO", "timezone": "US/Eastern", "lat": 42.0, "lon": -75.0, "states": ["NY"], "type": "ISO"},
    "ISNE": {"region_id": "ISONE", "name": "ISO New England", "timezone": "US/Eastern", "lat": 42.0, "lon": -71.0, "states": ["MA", "CT", "RI", "NH", "VT", "ME"], "type": "ISO"},
    "MISO": {"region_id": "MISO", "name": "Midcontinent ISO", "timezone": "US/Central", "lat": 41.0, "lon": -89.0, "states": ["IL", "IN", "MI", "MN", "WI", "IA", "MO", "AR", "LA", "MS"], "type": "ISO"},
    "SWPP": {"region_id": "SPP", "name": "Southwest Power Pool", "timezone": "US/Central", "lat": 35.0, "lon": -98.0, "states": ["OK", "KS", "NE", "SD", "ND"], "type": "ISO"},
    # ERCOT utilities
    "ERCOT": {"region_id": "ERCOT"},
    # CAISO utilities
    "BANC": {"region_id": "CAISO"}, "LDWP": {"region_id": "CAISO"}, "TIDC": {"region_id": "CAISO"},
    "IID": {"region_id": "CAISO"}, "WALC": {"region_id": "CAISO"}, "AZPS": {"region_id": "CAISO"},
    # PJM utilities
    "AEP": {"region_id": "PJM"}, "AP": {"region_id": "PJM"}, "ATSI": {"region_id": "PJM"},
    "BC": {"region_id": "PJM"}, "CE": {"region_id": "PJM"}, "DAY": {"region_id": "PJM"},
    "DEOK": {"region_id": "PJM"}, "DOM": {"region_id": "PJM"}, "DPL": {"region_id": "PJM"},
    "DUK": {"region_id": "PJM"}, "EKPC": {"region_id": "PJM"}, "JC": {"region_id": "PJM"},
    "ME": {"region_id": "PJM"}, "PE": {"region_id": "PJM"}, "PEP": {"region_id": "PJM"},
    "PL": {"region_id": "PJM"}, "PN": {"region_id": "PJM"}, "PS": {"region_id": "PJM"},
    "RECO": {"region_id": "PJM"}, "UGI": {"region_id": "PJM"},
    # NYISO utilities
    "NYISO": {"region_id": "NYISO"},
    # ISONE utilities
    "ISONE": {"region_id": "ISONE"},
    # MISO utilities
    "AMIL": {"region_id": "MISO"}, "AMMO": {"region_id": "MISO"}, "BREC": {"region_id": "MISO"},
    "CIN": {"region_id": "MISO"}, "CLEC": {"region_id": "MISO"}, "CWEP": {"region_id": "MISO"},
    "CWLP": {"region_id": "MISO"}, "DECO": {"region_id": "MISO"}, "EAI": {"region_id": "MISO"},
    "EES": {"region_id": "MISO"}, "EMBA": {"region_id": "MISO"}, "GRE": {"region_id": "MISO"},
    "HE": {"region_id": "MISO"}, "LAFA": {"region_id": "MISO"}, "LAGN": {"region_id": "MISO"},
    "LEPA": {"region_id": "MISO"}, "LGEE": {"region_id": "MISO"}, "MEC": {"region_id": "MISO"},
    "MGE": {"region_id": "MISO"}, "MIUP": {"region_id": "MISO"}, "MP": {"region_id": "MISO"},
    "MPW": {"region_id": "MISO"}, "NIPS": {"region_id": "MISO"}, "NSP": {"region_id": "MISO"},
    "OVEC": {"region_id": "MISO"}, "SIGE": {"region_id": "MISO"}, "SIPC": {"region_id": "MISO"},
    "SMMP": {"region_id": "MISO"}, "SMP": {"region_id": "MISO"}, "UPPC": {"region_id": "MISO"},
    "WEC": {"region_id": "MISO"}, "WPS": {"region_id": "MISO"}, "ALTE": {"region_id": "MISO"},
    # SPP utilities
    "CSWS": {"region_id": "SPP"}, "EDE": {"region_id": "SPP"}, "GRDA": {"region_id": "SPP"},
    "INDN": {"region_id": "SPP"}, "KACY": {"region_id": "SPP"}, "KCPL": {"region_id": "SPP"},
    "LES": {"region_id": "SPP"}, "MPS": {"region_id": "SPP"}, "NPPD": {"region_id": "SPP"},
    "OKGE": {"region_id": "SPP"}, "OPPD": {"region_id": "SPP"}, "SECI": {"region_id": "SPP"},
    "SPRM": {"region_id": "SPP"}, "SPS": {"region_id": "SPP"}, "WAUE": {"region_id": "SPP"},
    "WFEC": {"region_id": "SPP"}, "WR": {"region_id": "SPP"},
}

# Fuel type mapping from EIA codes
FUEL_TYPE_MAP = {
    "NG": "natural_gas_mw",
    "GAS": "natural_gas_mw",
    "COL": "coal_mw",
    "NUC": "nuclear_mw",
    "WND": "wind_mw",
    "SUN": "solar_mw",
    "SOL": "solar_mw",
    "WAT": "hydro_mw",
    "HYD": "hydro_mw",
    "OTH": "other_mw",
    "OIL": "other_mw",
    "PET": "other_mw",
    "UNK": "other_mw",
    "BAT": "other_mw",  # Battery storage
    "PS": "other_mw",   # Pumped storage
}


class EIACollector(BaseCollector):
    """
    Collector for EIA Balancing Authority hourly data

    API Docs: https://www.eia.gov/opendata/documentation.php
    """

    def __init__(self, session: AsyncSession, api_key: Optional[str] = None):
        super().__init__(session, api_key or settings.eia_api_key)
        self.source_name = "EIA"
        self.base_url = settings.eia_base_url
        self.carbon_calc = CarbonIntensityCalculator()

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect hourly grid data from EIA API
        """
        all_data = []

        # Collect demand data
        demand_data = await self._collect_demand()
        all_data.extend(demand_data)

        # Collect generation by fuel type
        generation_data = await self._collect_generation()
        all_data.extend(generation_data)

        # Collect interchange data
        interchange_data = await self._collect_interchange()
        all_data.extend(interchange_data)

        return all_data

    async def _collect_demand(self) -> List[Dict]:
        """
        Collect demand/load data from EIA
        Endpoint: /electricity/rto/region-data/data/
        """
        # Build URL with query string directly to handle bracket encoding
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        url = (
            f"{self.base_url}/electricity/rto/region-data/data/"
            f"?api_key={self.api_key}"
            f"&frequency=hourly"
            f"&data[0]=value"
            f"&facets[type][]=D"
            f"&start={start_date.strftime('%Y-%m-%dT%H')}"
            f"&end={end_date.strftime('%Y-%m-%dT%H')}"
            f"&sort[0][column]=period"
            f"&sort[0][direction]=desc"
            f"&length=5000"
        )

        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            records = data.get("response", {}).get("data", [])
            logger.info(f"Collected {len(records)} demand records from EIA")
            return [{**r, "record_type": "demand"} for r in records]
        except Exception as e:
            logger.error(f"Error collecting EIA demand data: {e}")
            return []

    async def _collect_generation(self) -> List[Dict]:
        """
        Collect generation by fuel type from EIA
        Endpoint: /electricity/rto/fuel-type-data/data/
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        url = (
            f"{self.base_url}/electricity/rto/fuel-type-data/data/"
            f"?api_key={self.api_key}"
            f"&frequency=hourly"
            f"&data[0]=value"
            f"&start={start_date.strftime('%Y-%m-%dT%H')}"
            f"&end={end_date.strftime('%Y-%m-%dT%H')}"
            f"&sort[0][column]=period"
            f"&sort[0][direction]=desc"
            f"&length=5000"
        )

        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            records = data.get("response", {}).get("data", [])
            logger.info(
                f"Collected {len(records)} generation records from EIA")
            return [{**r, "record_type": "generation"} for r in records]
        except Exception as e:
            logger.error(f"Error collecting EIA generation data: {e}")
            return []

    async def _collect_interchange(self) -> List[Dict]:
        """
        Collect net interchange data from EIA
        Endpoint: /electricity/rto/interchange-data/data/
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        url = (
            f"{self.base_url}/electricity/rto/interchange-data/data/"
            f"?api_key={self.api_key}"
            f"&frequency=hourly"
            f"&data[0]=value"
            f"&start={start_date.strftime('%Y-%m-%dT%H')}"
            f"&end={end_date.strftime('%Y-%m-%dT%H')}"
            f"&sort[0][column]=period"
            f"&sort[0][direction]=desc"
            f"&length=5000"
        )

        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            records = data.get("response", {}).get("data", [])
            logger.info(
                f"Collected {len(records)} interchange records from EIA")
            return [{**r, "record_type": "interchange"} for r in records]
        except Exception as e:
            logger.error(f"Error collecting EIA interchange data: {e}")
            return []

    async def transform(self, raw_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Transform raw EIA data into normalized grid_metrics format
        """
        # Group by region and timestamp
        grouped = {}

        # Debug: log sample records and unique BA codes
        gen_records = [r for r in raw_data if r.get(
            "record_type") == "generation"]
        if gen_records:
            unique_bas = set(r.get("respondent") for r in gen_records)
            logger.info(
                f"Unique BA codes in generation data: {sorted(unique_bas)}")
            matched_bas = [ba for ba in unique_bas if ba in BA_REGION_MAP]
            logger.info(f"Matched BA codes: {matched_bas}")

        for record in raw_data:
            # Try both 'respondent' and 'respondent-name' fields
            ba_code = record.get("respondent") or record.get(
                "respondent-name", "").split("-")[0]
            if ba_code not in BA_REGION_MAP:
                continue

            region_info = BA_REGION_MAP[ba_code]
            region_id = region_info["region_id"]

            # Parse timestamp - EIA uses format like "2025-11-28T22" (no minutes)
            period = record.get("period")
            if not period:
                continue

            try:
                # Handle both "2025-11-28T22" and "2025-11-28T22:00:00" formats
                if len(period) == 13:  # "2025-11-28T22" format
                    timestamp = datetime.strptime(period, "%Y-%m-%dT%H")
                else:
                    timestamp = datetime.fromisoformat(
                        period.replace("Z", "+00:00"))
            except ValueError as e:
                logger.warning(f"Could not parse timestamp {period}: {e}")
                continue

            key = (region_id, timestamp)
            if key not in grouped:
                grouped[key] = {
                    "timestamp_utc": timestamp,
                    "region_id": region_id,
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
                    "source": "EIA",
                }

            value = float(record.get("value", 0) or 0)
            record_type = record.get("record_type")

            if record_type == "demand":
                # Only update load if we have a value (don't overwrite with 0)
                if value > 0:
                    grouped[key]["load_mw"] = value
            elif record_type == "generation":
                fuel_code = record.get("fueltype", "OTH")
                fuel_field = FUEL_TYPE_MAP.get(fuel_code, "other_mw")
                grouped[key]["generation_by_fuel"][fuel_field] += value
                grouped[key]["total_generation_mw"] += value
            elif record_type == "interchange":
                grouped[key]["net_interchange_mw"] = value

        # Calculate derived metrics
        result = []
        for key, metrics in grouped.items():
            gen = metrics["generation_by_fuel"]
            total_gen = metrics["total_generation_mw"]

            # Calculate renewable fraction
            renewable_mw = gen["wind_mw"] + gen["solar_mw"] + gen["hydro_mw"]
            metrics["renewable_fraction_pct"] = (
                (renewable_mw / total_gen * 100) if total_gen > 0 else 0
            )

            # Calculate carbon intensity
            metrics["carbon_intensity_kg_per_mwh"] = self.carbon_calc.calculate(
                gen, total_gen)

            result.append(metrics)

        return result

    async def load(self, records: List[Dict[str, Any]]) -> int:
        """
        Load transformed records into database
        Uses simple insert/update for SQLite compatibility
        """
        if not records:
            return 0

        count = 0
        for record in records:
            # Check if record exists
            existing = await self.session.execute(
                select(GridMetricsDB).where(
                    GridMetricsDB.region_id == record["region_id"],
                    GridMetricsDB.timestamp_utc == record["timestamp_utc"]
                )
            )
            existing_row = existing.scalar_one_or_none()

            if existing_row:
                # Update existing record, preserving non-zero values
                if record["load_mw"] > 0:
                    existing_row.load_mw = record["load_mw"]
                if record["total_generation_mw"] > 0:
                    existing_row.total_generation_mw = record["total_generation_mw"]
                    existing_row.generation_by_fuel = record["generation_by_fuel"]
                    existing_row.renewable_fraction_pct = record["renewable_fraction_pct"]
                    existing_row.carbon_intensity_kg_per_mwh = record["carbon_intensity_kg_per_mwh"]
                existing_row.net_interchange_mw = record["net_interchange_mw"]
            else:
                # Insert new record
                new_record = GridMetricsDB(
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
                self.session.add(new_record)

            count += 1

        await self.session.commit()
        return count

    async def ensure_regions_exist(self) -> None:
        """
        Ensure all BA regions exist in the database
        SQLite-compatible version
        """
        # Only process main ISO entries (those with full info)
        for ba_code, info in BA_REGION_MAP.items():
            # Skip utility mappings that only have region_id
            if "name" not in info:
                continue

            # Check if region exists
            existing = await self.session.execute(
                select(GridRegionDB).where(
                    GridRegionDB.region_id == info["region_id"])
            )
            if not existing.scalar_one_or_none():
                # Insert new region
                region = GridRegionDB(
                    region_id=info["region_id"],
                    region_name=info["name"],
                    timezone=info["timezone"],
                    latitude=info["lat"],
                    longitude=info["lon"],
                    coverage_states=info["states"],
                    region_type=info["type"],
                )
                self.session.add(region)

        await self.session.commit()
