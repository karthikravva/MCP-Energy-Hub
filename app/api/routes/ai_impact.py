"""
AI Impact Endpoints
KPIs and analytics for AI compute impact on the grid
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.database import (
    GridRegionDB,
    GridMetricsDB,
    DataCenterDB,
    DataCenterEnergyEstimateDB,
    ComputeCorridorMetricsDB,
)
from app.models.schemas import AIImpactKPIs, ComputeCorridorMetrics

router = APIRouter(prefix="/ai-impact", tags=["AI Impact"])


@router.get("/{region_id}", response_model=AIImpactKPIs)
async def get_ai_impact(
    region_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI impact KPIs for a specific region

    Returns:
    - AI share of regional load
    - Renewable coverage for AI workloads
    - Average carbon intensity
    - Peak AI load
    - Grid stress indicators
    """
    # Verify region exists
    region_result = await db.execute(
        select(GridRegionDB).where(GridRegionDB.region_id == region_id)
    )
    if not region_result.scalar_one_or_none():
        raise HTTPException(
            status_code=404, detail=f"Region {region_id} not found")

    # Get latest grid metrics
    grid_result = await db.execute(
        select(GridMetricsDB)
        .where(GridMetricsDB.region_id == region_id)
        .order_by(desc(GridMetricsDB.timestamp_utc))
        .limit(1)
    )
    grid_metrics = grid_result.scalar_one_or_none()

    if not grid_metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No grid metrics available for region {region_id}"
        )

    # Get AI-focused data centers in region
    dc_result = await db.execute(
        select(DataCenterDB)
        .where(DataCenterDB.region_id == region_id)
        .where(DataCenterDB.is_ai_focused == True)
    )
    ai_data_centers = dc_result.scalars().all()

    # Calculate AI metrics
    total_ai_capacity = sum(dc.max_capacity_mw for dc in ai_data_centers)
    avg_pue = (
        sum(dc.avg_pue * dc.max_capacity_mw for dc in ai_data_centers) /
        total_ai_capacity
        if total_ai_capacity > 0 else 1.5
    )

    # Estimate AI load (assume 60% utilization)
    utilization = 0.6
    total_ai_load = total_ai_capacity * utilization
    total_ai_it_load = total_ai_load / avg_pue
    total_cooling = total_ai_load - total_ai_it_load

    # Calculate renewable coverage
    total_ppa = sum(dc.renewable_ppa_mw for dc in ai_data_centers)
    renewable_coverage = min(
        100, (total_ppa / total_ai_load * 100)) if total_ai_load > 0 else 0

    # Calculate AI share of load
    ai_share = (total_ai_load / grid_metrics.load_mw *
                100) if grid_metrics.load_mw > 0 else 0

    # Grid margin and stress
    grid_margin = grid_metrics.total_generation_mw - grid_metrics.load_mw
    grid_stress = (
        (grid_metrics.load_mw + total_ai_load) /
        (grid_metrics.total_generation_mw + 5000)  # Assume 5GW reserve
    ) if grid_metrics.total_generation_mw > 0 else 0.5

    return AIImpactKPIs(
        timestamp_utc=datetime.utcnow(),
        region_id=region_id,
        ai_share_of_load_pct=round(ai_share, 2),
        renewable_coverage_for_ai_pct=round(renewable_coverage, 2),
        avg_carbon_intensity_kg_per_mwh=grid_metrics.carbon_intensity_kg_per_mwh,
        peak_ai_load_mw=round(total_ai_load, 1),
        load_flex_potential_mw=round(
            total_ai_load * 0.15, 1),  # Assume 15% flexible
        effective_pue=round(avg_pue, 2),
        total_cooling_overhead_mw=round(total_cooling, 1),
        renewable_mismatch_hours=0,  # Would need historical analysis
        grid_margin_mw=round(grid_margin, 1),
        grid_stress_indicator=round(min(1.0, grid_stress), 3),
    )


@router.get("/{region_id}/corridor", response_model=ComputeCorridorMetrics)
async def get_compute_corridor_metrics(
    region_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get compute corridor metrics for AI data centers in a region
    """
    # Get AI data centers
    dc_result = await db.execute(
        select(DataCenterDB)
        .where(DataCenterDB.region_id == region_id)
        .where(DataCenterDB.is_ai_focused == True)
    )
    ai_dcs = dc_result.scalars().all()

    if not ai_dcs:
        raise HTTPException(
            status_code=404,
            detail=f"No AI data centers found in region {region_id}"
        )

    # Calculate aggregated metrics
    total_capacity = sum(dc.max_capacity_mw for dc in ai_dcs)
    utilization = 0.65  # Assumed GPU utilization

    total_load = total_capacity * utilization
    avg_pue = sum(
        dc.avg_pue * dc.max_capacity_mw for dc in ai_dcs) / total_capacity
    cooling_load = total_load * (1 - 1/avg_pue)

    return ComputeCorridorMetrics(
        timestamp_utc=datetime.utcnow(),
        region_id=region_id,
        ai_data_centers_count=len(ai_dcs),
        total_ai_load_mw=round(total_load, 1),
        total_ai_cooling_mw=round(cooling_load, 1),
        avg_pue_ai=round(avg_pue, 2),
        gpu_utilization_proxy=utilization,
    )


@router.get("/{region_id}/history", response_model=List[AIImpactKPIs])
async def get_ai_impact_history(
    region_id: str,
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical AI impact KPIs for a region
    """
    # For MVP, generate from grid metrics history
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    grid_result = await db.execute(
        select(GridMetricsDB)
        .where(GridMetricsDB.region_id == region_id)
        .where(GridMetricsDB.timestamp_utc >= cutoff)
        .order_by(desc(GridMetricsDB.timestamp_utc))
    )
    grid_history = grid_result.scalars().all()

    if not grid_history:
        return []

    # Get AI data centers for calculations
    dc_result = await db.execute(
        select(DataCenterDB)
        .where(DataCenterDB.region_id == region_id)
        .where(DataCenterDB.is_ai_focused == True)
    )
    ai_dcs = dc_result.scalars().all()

    total_ai_capacity = sum(dc.max_capacity_mw for dc in ai_dcs)
    avg_pue = (
        sum(dc.avg_pue * dc.max_capacity_mw for dc in ai_dcs) / total_ai_capacity
        if total_ai_capacity > 0 else 1.5
    )
    total_ppa = sum(dc.renewable_ppa_mw for dc in ai_dcs)

    results = []
    for gm in grid_history:
        utilization = 0.6
        total_ai_load = total_ai_capacity * utilization
        cooling = total_ai_load * (1 - 1/avg_pue)

        ai_share = (total_ai_load / gm.load_mw * 100) if gm.load_mw > 0 else 0
        renewable_coverage = min(
            100, (total_ppa / total_ai_load * 100)) if total_ai_load > 0 else 0
        grid_margin = gm.total_generation_mw - gm.load_mw
        grid_stress = (gm.load_mw / (gm.total_generation_mw + 5000)
                       ) if gm.total_generation_mw > 0 else 0.5

        results.append(AIImpactKPIs(
            timestamp_utc=gm.timestamp_utc,
            region_id=region_id,
            ai_share_of_load_pct=round(ai_share, 2),
            renewable_coverage_for_ai_pct=round(renewable_coverage, 2),
            avg_carbon_intensity_kg_per_mwh=gm.carbon_intensity_kg_per_mwh,
            peak_ai_load_mw=round(total_ai_load, 1),
            load_flex_potential_mw=round(total_ai_load * 0.15, 1),
            effective_pue=round(avg_pue, 2),
            total_cooling_overhead_mw=round(cooling, 1),
            renewable_mismatch_hours=0,
            grid_margin_mw=round(grid_margin, 1),
            grid_stress_indicator=round(min(1.0, grid_stress), 3),
        ))

    return results


@router.get("/summary/all-regions")
async def get_all_regions_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI impact summary across all regions
    """
    # Get all regions
    regions_result = await db.execute(select(GridRegionDB))
    regions = regions_result.scalars().all()

    summaries = []
    for region in regions:
        # Get latest metrics
        grid_result = await db.execute(
            select(GridMetricsDB)
            .where(GridMetricsDB.region_id == region.region_id)
            .order_by(desc(GridMetricsDB.timestamp_utc))
            .limit(1)
        )
        grid_metrics = grid_result.scalar_one_or_none()

        # Count AI data centers
        dc_count_result = await db.execute(
            select(func.count(DataCenterDB.dc_id))
            .where(DataCenterDB.region_id == region.region_id)
            .where(DataCenterDB.is_ai_focused == True)
        )
        ai_dc_count = dc_count_result.scalar() or 0

        # Total AI capacity
        capacity_result = await db.execute(
            select(func.sum(DataCenterDB.max_capacity_mw))
            .where(DataCenterDB.region_id == region.region_id)
            .where(DataCenterDB.is_ai_focused == True)
        )
        total_capacity = capacity_result.scalar() or 0

        summaries.append({
            "region_id": region.region_id,
            "region_name": region.region_name,
            "ai_data_centers": ai_dc_count,
            "total_ai_capacity_mw": round(total_capacity, 1),
            "current_load_mw": grid_metrics.load_mw if grid_metrics else None,
            "carbon_intensity": grid_metrics.carbon_intensity_kg_per_mwh if grid_metrics else None,
            "renewable_fraction_pct": grid_metrics.renewable_fraction_pct if grid_metrics else None,
        })

    return {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "regions": summaries,
    }
