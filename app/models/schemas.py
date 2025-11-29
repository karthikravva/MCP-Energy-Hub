"""
Pydantic Schemas for MCP Energy Hub
These define the API request/response models and validation
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# GRID REGION SCHEMAS
# =============================================================================

class GridRegion(BaseModel):
    """
    Represents a Balancing Authority, ISO, or state-level grid region
    """
    region_id: str = Field(...,
                           description="Unique identifier (e.g., ERCOT, CAISO)")
    region_name: str = Field(..., description="Full name of the region")
    timezone: str = Field(default="UTC", description="IANA timezone")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    coverage_states: List[str] = Field(
        default_factory=list, description="US states covered")
    region_type: str = Field(..., description="Type: ISO, BA, STATE")

    class Config:
        json_schema_extra = {
            "example": {
                "region_id": "ERCOT",
                "region_name": "Electric Reliability Council of Texas",
                "timezone": "US/Central",
                "latitude": 31.0,
                "longitude": -99.0,
                "coverage_states": ["TX"],
                "region_type": "ISO"
            }
        }


class GenerationByFuel(BaseModel):
    """Breakdown of generation by fuel type in MW"""
    natural_gas_mw: float = Field(default=0, ge=0)
    coal_mw: float = Field(default=0, ge=0)
    nuclear_mw: float = Field(default=0, ge=0)
    wind_mw: float = Field(default=0, ge=0)
    solar_mw: float = Field(default=0, ge=0)
    hydro_mw: float = Field(default=0, ge=0)
    other_mw: float = Field(default=0, ge=0)


class GridMetrics(BaseModel):
    """
    Core real-time grid metrics (5-min to 1-hour resolution)
    """
    timestamp_utc: datetime
    region_id: str

    # Load metrics
    load_mw: float = Field(..., ge=0, description="Current load in MW")
    forecast_load_mw: Optional[float] = Field(
        None, ge=0, description="Forecasted load")

    # Generation metrics
    total_generation_mw: float = Field(..., ge=0)
    generation_by_fuel: GenerationByFuel

    # Interchange
    net_interchange_mw: float = Field(
        default=0, description="Positive = importing")

    # Derived metrics
    renewable_fraction_pct: float = Field(..., ge=0, le=100)
    carbon_intensity_kg_per_mwh: float = Field(..., ge=0)

    # Pricing
    lmp_energy_price_usd_mwh: Optional[float] = Field(
        None, description="Locational Marginal Price")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp_utc": "2025-01-30T17:00:00Z",
                "region_id": "ERCOT",
                "load_mw": 57550,
                "forecast_load_mw": 59000,
                "total_generation_mw": 58000,
                "generation_by_fuel": {
                    "natural_gas_mw": 21000,
                    "coal_mw": 7000,
                    "nuclear_mw": 5000,
                    "wind_mw": 15000,
                    "solar_mw": 7000,
                    "hydro_mw": 300
                },
                "net_interchange_mw": -2000,
                "renewable_fraction_pct": 41.2,
                "carbon_intensity_kg_per_mwh": 342.2,
                "lmp_energy_price_usd_mwh": 39.5
            }
        }


# =============================================================================
# DATA CENTER SCHEMAS
# =============================================================================

class Coordinates(BaseModel):
    """Geographic coordinates"""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class DataCenter(BaseModel):
    """
    Represents a physical data center facility
    """
    dc_id: str = Field(..., description="Unique data center identifier")
    name: str = Field(..., description="Data center name")
    operator: str = Field(..., description="Operating company")
    region_id: str = Field(...,
                           description="Grid region this DC is connected to")

    coordinates: Coordinates

    max_capacity_mw: float = Field(..., ge=0,
                                   description="Maximum power capacity")
    avg_pue: float = Field(default=1.5, ge=1.0, le=3.0,
                           description="Average PUE")
    cooling_type: str = Field(
        default="Unknown", description="Cooling technology")

    primary_grid_connection: str = Field(...,
                                         description="Primary grid/ISO connection")
    renewable_ppa_mw: float = Field(
        default=0, ge=0, description="Renewable PPA capacity")

    commissioned_year: Optional[int] = Field(None, ge=1990, le=2030)
    is_ai_focused: bool = Field(
        default=False, description="Primarily serves AI/ML workloads")

    class Config:
        json_schema_extra = {
            "example": {
                "dc_id": "AWS_DAL1",
                "name": "AWS Dallas Region 1",
                "operator": "AWS",
                "region_id": "ERCOT",
                "coordinates": {"lat": 32.9, "lon": -96.8},
                "max_capacity_mw": 75,
                "avg_pue": 1.25,
                "cooling_type": "Evaporative",
                "primary_grid_connection": "ERCOT",
                "renewable_ppa_mw": 120,
                "commissioned_year": 2022,
                "is_ai_focused": False
            }
        }


class DataCenterEnergyEstimate(BaseModel):
    """
    Time-series energy consumption estimate for a data center
    """
    timestamp_utc: datetime
    dc_id: str

    estimated_load_mw: float = Field(..., ge=0,
                                     description="Total facility load")
    estimated_it_load_mw: float = Field(...,
                                        ge=0, description="IT equipment load")
    estimated_cooling_load_mw: float = Field(...,
                                             ge=0, description="Cooling system load")

    pue: float = Field(..., ge=1.0, le=3.0,
                       description="Power Usage Effectiveness")
    renewable_usage_pct: float = Field(default=0, ge=0, le=100)
    carbon_intensity_kg_per_mwh: float = Field(..., ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp_utc": "2025-01-30T17:00:00Z",
                "dc_id": "AWS_DAL1",
                "estimated_load_mw": 55.2,
                "estimated_it_load_mw": 44.1,
                "estimated_cooling_load_mw": 11.1,
                "pue": 1.25,
                "renewable_usage_pct": 65.0,
                "carbon_intensity_kg_per_mwh": 342.2
            }
        }


# =============================================================================
# AI / COMPUTE CORRIDOR SCHEMAS
# =============================================================================

class ComputeCorridorMetrics(BaseModel):
    """
    Aggregated metrics for AI compute loads in a region
    """
    timestamp_utc: datetime
    region_id: str

    ai_data_centers_count: int = Field(..., ge=0)
    total_ai_load_mw: float = Field(..., ge=0)
    total_ai_cooling_mw: float = Field(..., ge=0)
    avg_pue_ai: float = Field(..., ge=1.0, le=3.0)
    gpu_utilization_proxy: float = Field(default=0.5, ge=0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp_utc": "2025-01-30T17:00:00Z",
                "region_id": "ERCOT",
                "ai_data_centers_count": 4,
                "total_ai_load_mw": 310,
                "total_ai_cooling_mw": 88,
                "avg_pue_ai": 1.30,
                "gpu_utilization_proxy": 0.72
            }
        }


# =============================================================================
# KPI / ANALYTICS SCHEMAS
# =============================================================================

class AIImpactKPIs(BaseModel):
    """
    Computed KPIs for AI impact on grid
    """
    timestamp_utc: datetime
    region_id: str

    # Grid → AI Metrics
    ai_share_of_load_pct: float = Field(..., ge=0, le=100)
    renewable_coverage_for_ai_pct: float = Field(..., ge=0, le=100)
    avg_carbon_intensity_kg_per_mwh: float = Field(..., ge=0)
    peak_ai_load_mw: float = Field(..., ge=0)
    load_flex_potential_mw: float = Field(default=0, ge=0)

    # Data Center Efficiency
    effective_pue: float = Field(..., ge=1.0, le=3.0)
    total_cooling_overhead_mw: float = Field(..., ge=0)
    renewable_mismatch_hours: int = Field(default=0, ge=0)

    # Grid Health
    grid_margin_mw: float = Field(..., description="Available capacity margin")
    grid_stress_indicator: float = Field(..., ge=0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp_utc": "2025-01-30T17:00:00Z",
                "region_id": "ERCOT",
                "ai_share_of_load_pct": 5.4,
                "renewable_coverage_for_ai_pct": 65.0,
                "avg_carbon_intensity_kg_per_mwh": 342.2,
                "peak_ai_load_mw": 310,
                "load_flex_potential_mw": 50,
                "effective_pue": 1.28,
                "total_cooling_overhead_mw": 88,
                "renewable_mismatch_hours": 4,
                "grid_margin_mw": 5000,
                "grid_stress_indicator": 0.72
            }
        }


class GridForecast(BaseModel):
    """
    Forecast data for a grid region
    """
    timestamp_utc: datetime
    region_id: str
    forecast_horizon_hours: int = Field(..., ge=1, le=168)

    forecasts: List[Dict] = Field(
        ...,
        description="List of forecast points with timestamp, load, carbon, price"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp_utc": "2025-01-30T17:00:00Z",
                "region_id": "ERCOT",
                "forecast_horizon_hours": 48,
                "forecasts": [
                    {
                        "timestamp": "2025-01-30T18:00:00Z",
                        "forecast_load_mw": 59000,
                        "forecast_carbon_intensity": 340,
                        "forecast_lmp_price": 42.5
                    }
                ]
            }
        }


# =============================================================================
# API REQUEST/RESPONSE SCHEMAS
# =============================================================================

class GridRealtimeResponse(BaseModel):
    """Response for GET /grid/{region_id}/realtime"""
    region: GridRegion
    metrics: GridMetrics
    ai_impact: Optional[AIImpactKPIs] = None


class DataCenterListResponse(BaseModel):
    """Response for GET /data-centers"""
    total_count: int
    data_centers: List[DataCenter]


class DataCenterEnergyResponse(BaseModel):
    """Response for GET /data-center/{id}/energy"""
    data_center: DataCenter
    current_estimate: DataCenterEnergyEstimate
    historical: Optional[List[DataCenterEnergyEstimate]] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    database_connected: bool
    redis_connected: bool
