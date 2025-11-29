"""
Grid Monitoring Endpoints
Real-time grid metrics, forecasts, and regional data
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.database import GridRegionDB, GridMetricsDB
from app.models.schemas import (
    GridRegion,
    GridMetrics,
    GenerationByFuel,
    GridRealtimeResponse,
    GridForecast,
)

router = APIRouter(prefix="/grid", tags=["Grid Monitoring"])


@router.get("/regions", response_model=List[GridRegion])
async def list_regions(db: AsyncSession = Depends(get_db)):
    """
    List all available grid regions (ISOs, Balancing Authorities)
    """
    result = await db.execute(select(GridRegionDB))
    regions = result.scalars().all()

    return [
        GridRegion(
            region_id=r.region_id,
            region_name=r.region_name,
            timezone=r.timezone,
            latitude=r.latitude,
            longitude=r.longitude,
            coverage_states=r.coverage_states or [],
            region_type=r.region_type,
        )
        for r in regions
    ]


@router.get("/{region_id}/realtime", response_model=GridRealtimeResponse)
async def get_realtime_metrics(
    region_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get real-time grid metrics for a specific region

    Returns the most recent metrics including:
    - Current load (MW)
    - Generation by fuel type
    - Renewable fraction
    - Carbon intensity
    - LMP price
    """
    # Get region
    region_result = await db.execute(
        select(GridRegionDB).where(GridRegionDB.region_id == region_id)
    )
    region = region_result.scalar_one_or_none()

    if not region:
        raise HTTPException(
            status_code=404, detail=f"Region {region_id} not found")

    # Get latest metrics
    metrics_result = await db.execute(
        select(GridMetricsDB)
        .where(GridMetricsDB.region_id == region_id)
        .order_by(desc(GridMetricsDB.timestamp_utc))
        .limit(1)
    )
    metrics_row = metrics_result.scalar_one_or_none()

    if not metrics_row:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics available for region {region_id}"
        )

    # Build response
    gen_fuel = metrics_row.generation_by_fuel or {}

    return GridRealtimeResponse(
        region=GridRegion(
            region_id=region.region_id,
            region_name=region.region_name,
            timezone=region.timezone,
            latitude=region.latitude,
            longitude=region.longitude,
            coverage_states=region.coverage_states or [],
            region_type=region.region_type,
        ),
        metrics=GridMetrics(
            timestamp_utc=metrics_row.timestamp_utc,
            region_id=metrics_row.region_id,
            load_mw=metrics_row.load_mw,
            forecast_load_mw=metrics_row.forecast_load_mw,
            total_generation_mw=metrics_row.total_generation_mw,
            generation_by_fuel=GenerationByFuel(
                natural_gas_mw=gen_fuel.get("natural_gas_mw", 0),
                coal_mw=gen_fuel.get("coal_mw", 0),
                nuclear_mw=gen_fuel.get("nuclear_mw", 0),
                wind_mw=gen_fuel.get("wind_mw", 0),
                solar_mw=gen_fuel.get("solar_mw", 0),
                hydro_mw=gen_fuel.get("hydro_mw", 0),
                other_mw=gen_fuel.get("other_mw", 0),
            ),
            net_interchange_mw=metrics_row.net_interchange_mw or 0,
            renewable_fraction_pct=metrics_row.renewable_fraction_pct,
            carbon_intensity_kg_per_mwh=metrics_row.carbon_intensity_kg_per_mwh,
            lmp_energy_price_usd_mwh=metrics_row.lmp_energy_price_usd_mwh,
        ),
        ai_impact=None,  # Computed separately
    )


@router.get("/{region_id}/history", response_model=List[GridMetrics])
async def get_historical_metrics(
    region_id: str,
    hours: int = Query(default=24, ge=1, le=168,
                       description="Hours of history"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical grid metrics for a region

    Args:
        region_id: Grid region identifier
        hours: Number of hours of history (1-168, default 24)
    """
    # Verify region exists
    region_result = await db.execute(
        select(GridRegionDB).where(GridRegionDB.region_id == region_id)
    )
    if not region_result.scalar_one_or_none():
        raise HTTPException(
            status_code=404, detail=f"Region {region_id} not found")

    # Get historical data
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(GridMetricsDB)
        .where(GridMetricsDB.region_id == region_id)
        .where(GridMetricsDB.timestamp_utc >= cutoff)
        .order_by(desc(GridMetricsDB.timestamp_utc))
    )
    rows = result.scalars().all()

    result_list = []
    for row in rows:
        gen_fuel = row.generation_by_fuel or {}
        result_list.append(GridMetrics(
            timestamp_utc=row.timestamp_utc,
            region_id=row.region_id,
            load_mw=row.load_mw or 0,
            forecast_load_mw=row.forecast_load_mw,
            total_generation_mw=row.total_generation_mw or 0,
            generation_by_fuel=GenerationByFuel(
                natural_gas_mw=gen_fuel.get("natural_gas_mw", 0),
                coal_mw=gen_fuel.get("coal_mw", 0),
                nuclear_mw=gen_fuel.get("nuclear_mw", 0),
                wind_mw=gen_fuel.get("wind_mw", 0),
                solar_mw=gen_fuel.get("solar_mw", 0),
                hydro_mw=gen_fuel.get("hydro_mw", 0),
                other_mw=gen_fuel.get("other_mw", 0),
            ),
            net_interchange_mw=row.net_interchange_mw or 0,
            renewable_fraction_pct=row.renewable_fraction_pct or 0,
            carbon_intensity_kg_per_mwh=row.carbon_intensity_kg_per_mwh or 0,
            lmp_energy_price_usd_mwh=row.lmp_energy_price_usd_mwh,
        ))
    return result_list


@router.get("/{region_id}/forecast", response_model=GridForecast)
async def get_forecast(
    region_id: str,
    horizon_hours: int = Query(default=48, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """
    Get load and carbon intensity forecast for a region

    Args:
        region_id: Grid region identifier
        horizon_hours: Forecast horizon in hours (1-168, default 48)
    """
    # Verify region exists
    region_result = await db.execute(
        select(GridRegionDB).where(GridRegionDB.region_id == region_id)
    )
    if not region_result.scalar_one_or_none():
        raise HTTPException(
            status_code=404, detail=f"Region {region_id} not found")

    # For MVP, generate simple forecast based on recent data
    # In production, this would call a forecasting model

    cutoff = datetime.utcnow() - timedelta(hours=24)
    result = await db.execute(
        select(GridMetricsDB)
        .where(GridMetricsDB.region_id == region_id)
        .where(GridMetricsDB.timestamp_utc >= cutoff)
        .order_by(desc(GridMetricsDB.timestamp_utc))
    )
    recent = result.scalars().all()

    if not recent:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient data for forecast in region {region_id}"
        )

    # Simple persistence forecast (use recent average)
    avg_load = sum(r.load_mw for r in recent) / len(recent)
    avg_carbon = sum(
        r.carbon_intensity_kg_per_mwh for r in recent) / len(recent)
    avg_price = sum(
        r.lmp_energy_price_usd_mwh or 0 for r in recent) / len(recent)

    forecasts = []
    base_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

    for h in range(1, horizon_hours + 1):
        forecast_time = base_time + timedelta(hours=h)
        # Add simple diurnal pattern
        hour_factor = 1.0 + 0.1 * \
            (abs(forecast_time.hour - 14) / 12)  # Peak at 2 PM

        forecasts.append({
            "timestamp": forecast_time.isoformat() + "Z",
            "forecast_load_mw": round(avg_load * hour_factor, 1),
            "forecast_carbon_intensity": round(avg_carbon, 1),
            "forecast_lmp_price": round(avg_price * hour_factor, 2),
        })

    return GridForecast(
        timestamp_utc=datetime.utcnow(),
        region_id=region_id,
        forecast_horizon_hours=horizon_hours,
        forecasts=forecasts,
    )


@router.get("/{region_id}/carbon", response_model=dict)
async def get_carbon_intensity(
    region_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current carbon intensity for a region
    Optimized endpoint for carbon-aware scheduling
    """
    result = await db.execute(
        select(GridMetricsDB)
        .where(GridMetricsDB.region_id == region_id)
        .order_by(desc(GridMetricsDB.timestamp_utc))
        .limit(1)
    )
    metrics = result.scalar_one_or_none()

    if not metrics:
        raise HTTPException(
            status_code=404, detail=f"No data for region {region_id}")

    return {
        "region_id": region_id,
        "timestamp_utc": metrics.timestamp_utc.isoformat() + "Z",
        "carbon_intensity_kg_per_mwh": metrics.carbon_intensity_kg_per_mwh,
        "renewable_fraction_pct": metrics.renewable_fraction_pct,
    }
