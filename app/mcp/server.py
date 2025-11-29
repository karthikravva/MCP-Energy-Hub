"""
MCP Server Implementation
Implements the Model Context Protocol for AI assistant integration
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.database import GridRegionDB, GridMetricsDB, DataCenterDB
from app.mcp.tools import get_mcp_tools

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Server for Energy Grid Data
    Provides tools for AI assistants to query grid and data center information
    """

    def __init__(self):
        self.name = "mcp-energy-hub"
        self.version = "1.0.0"
        self.tools = get_mcp_tools()

    def get_server_info(self) -> Dict[str, Any]:
        """Return server information for MCP handshake"""
        return {
            "name": self.name,
            "version": self.version,
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
            }
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools"""
        return self.tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return the result
        """
        try:
            async with async_session_maker() as session:
                if name == "get_grid_realtime":
                    return await self._get_grid_realtime(session, arguments)
                elif name == "get_grid_carbon":
                    return await self._get_grid_carbon(session, arguments)
                elif name == "get_grid_forecast":
                    return await self._get_grid_forecast(session, arguments)
                elif name == "list_grid_regions":
                    return await self._list_grid_regions(session)
                elif name == "get_data_centers":
                    return await self._get_data_centers(session, arguments)
                elif name == "get_data_center_energy":
                    return await self._get_data_center_energy(session, arguments)
                elif name == "get_ai_impact":
                    return await self._get_ai_impact(session, arguments)
                elif name == "get_best_region_for_compute":
                    return await self._get_best_region_for_compute(session, arguments)
                else:
                    return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": str(e)}

    async def _get_grid_realtime(self, session: AsyncSession, args: Dict) -> Dict:
        """Get real-time grid metrics"""
        region_id = args.get("region_id")

        result = await session.execute(
            select(GridMetricsDB)
            .where(GridMetricsDB.region_id == region_id)
            .order_by(desc(GridMetricsDB.timestamp_utc))
            .limit(1)
        )
        metrics = result.scalar_one_or_none()

        if not metrics:
            return {"error": f"No data for region {region_id}"}

        return {
            "region_id": region_id,
            "timestamp": metrics.timestamp_utc.isoformat() + "Z",
            "load_mw": metrics.load_mw,
            "total_generation_mw": metrics.total_generation_mw,
            "generation_by_fuel": metrics.generation_by_fuel,
            "renewable_fraction_pct": metrics.renewable_fraction_pct,
            "carbon_intensity_kg_per_mwh": metrics.carbon_intensity_kg_per_mwh,
            "net_interchange_mw": metrics.net_interchange_mw,
        }

    async def _get_grid_carbon(self, session: AsyncSession, args: Dict) -> Dict:
        """Get current carbon intensity"""
        region_id = args.get("region_id")

        result = await session.execute(
            select(GridMetricsDB)
            .where(GridMetricsDB.region_id == region_id)
            .order_by(desc(GridMetricsDB.timestamp_utc))
            .limit(1)
        )
        metrics = result.scalar_one_or_none()

        if not metrics:
            return {"error": f"No data for region {region_id}"}

        return {
            "region_id": region_id,
            "timestamp": metrics.timestamp_utc.isoformat() + "Z",
            "carbon_intensity_kg_per_mwh": metrics.carbon_intensity_kg_per_mwh,
            "renewable_fraction_pct": metrics.renewable_fraction_pct,
            "recommendation": self._get_carbon_recommendation(metrics.carbon_intensity_kg_per_mwh)
        }

    def _get_carbon_recommendation(self, carbon_intensity: float) -> str:
        """Get recommendation based on carbon intensity"""
        if carbon_intensity < 200:
            return "Excellent - Very low carbon, ideal for compute workloads"
        elif carbon_intensity < 350:
            return "Good - Moderate carbon intensity"
        elif carbon_intensity < 500:
            return "Fair - Consider scheduling non-urgent workloads for later"
        else:
            return "Poor - High carbon intensity, defer workloads if possible"

    async def _get_grid_forecast(self, session: AsyncSession, args: Dict) -> Dict:
        """Get grid forecast"""
        region_id = args.get("region_id")
        horizon = args.get("horizon_hours", 48)

        # Get recent data for simple forecast
        result = await session.execute(
            select(GridMetricsDB)
            .where(GridMetricsDB.region_id == region_id)
            .order_by(desc(GridMetricsDB.timestamp_utc))
            .limit(24)
        )
        recent = result.scalars().all()

        if not recent:
            return {"error": f"No data for region {region_id}"}

        avg_load = sum(r.load_mw or 0 for r in recent) / len(recent)
        avg_carbon = sum(
            r.carbon_intensity_kg_per_mwh or 0 for r in recent) / len(recent)

        return {
            "region_id": region_id,
            "forecast_horizon_hours": horizon,
            "avg_forecast_load_mw": round(avg_load, 1),
            "avg_forecast_carbon_intensity": round(avg_carbon, 1),
            "trend": "stable",  # Simplified for MVP
            "confidence": "medium"
        }

    async def _list_grid_regions(self, session: AsyncSession) -> Dict:
        """List all grid regions"""
        result = await session.execute(select(GridRegionDB))
        regions = result.scalars().all()

        return {
            "regions": [
                {
                    "region_id": r.region_id,
                    "name": r.region_name,
                    "type": r.region_type,
                    "states": r.coverage_states,
                }
                for r in regions
            ]
        }

    async def _get_data_centers(self, session: AsyncSession, args: Dict) -> Dict:
        """Get data centers with optional filters"""
        query = select(DataCenterDB)

        if args.get("region_id"):
            query = query.where(DataCenterDB.region_id == args["region_id"])
        if args.get("operator"):
            query = query.where(
                DataCenterDB.operator.ilike(f"%{args['operator']}%"))
        if args.get("ai_only"):
            query = query.where(DataCenterDB.is_ai_focused == True)

        result = await session.execute(query.limit(50))
        dcs = result.scalars().all()

        return {
            "count": len(dcs),
            "data_centers": [
                {
                    "dc_id": dc.dc_id,
                    "name": dc.name,
                    "operator": dc.operator,
                    "region_id": dc.region_id,
                    "max_capacity_mw": dc.max_capacity_mw,
                    "avg_pue": dc.avg_pue,
                    "is_ai_focused": dc.is_ai_focused,
                }
                for dc in dcs
            ]
        }

    async def _get_data_center_energy(self, session: AsyncSession, args: Dict) -> Dict:
        """Get data center energy estimates"""
        dc_id = args.get("dc_id")

        result = await session.execute(
            select(DataCenterDB).where(DataCenterDB.dc_id == dc_id)
        )
        dc = result.scalar_one_or_none()

        if not dc:
            return {"error": f"Data center {dc_id} not found"}

        # Get grid carbon for the region
        grid_result = await session.execute(
            select(GridMetricsDB)
            .where(GridMetricsDB.region_id == dc.region_id)
            .order_by(desc(GridMetricsDB.timestamp_utc))
            .limit(1)
        )
        grid = grid_result.scalar_one_or_none()
        carbon_intensity = grid.carbon_intensity_kg_per_mwh if grid else 400

        # Estimate energy
        utilization = 0.6
        estimated_load = dc.max_capacity_mw * utilization
        it_load = estimated_load / dc.avg_pue
        cooling_load = estimated_load - it_load

        return {
            "dc_id": dc_id,
            "name": dc.name,
            "estimated_load_mw": round(estimated_load, 1),
            "estimated_it_load_mw": round(it_load, 1),
            "estimated_cooling_load_mw": round(cooling_load, 1),
            "pue": dc.avg_pue,
            "carbon_intensity_kg_per_mwh": carbon_intensity,
            "estimated_hourly_emissions_kg": round(estimated_load * carbon_intensity, 0),
        }

    async def _get_ai_impact(self, session: AsyncSession, args: Dict) -> Dict:
        """Get AI impact KPIs for a region"""
        region_id = args.get("region_id")

        # Get grid metrics
        grid_result = await session.execute(
            select(GridMetricsDB)
            .where(GridMetricsDB.region_id == region_id)
            .order_by(desc(GridMetricsDB.timestamp_utc))
            .limit(1)
        )
        grid = grid_result.scalar_one_or_none()

        if not grid:
            return {"error": f"No grid data for region {region_id}"}

        # Get AI data centers
        dc_result = await session.execute(
            select(DataCenterDB)
            .where(DataCenterDB.region_id == region_id)
            .where(DataCenterDB.is_ai_focused == True)
        )
        ai_dcs = dc_result.scalars().all()

        total_ai_capacity = sum(dc.max_capacity_mw for dc in ai_dcs)
        utilization = 0.6
        total_ai_load = total_ai_capacity * utilization

        ai_share = (total_ai_load / grid.load_mw *
                    100) if grid.load_mw > 0 else 0

        return {
            "region_id": region_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ai_data_centers_count": len(ai_dcs),
            "total_ai_capacity_mw": round(total_ai_capacity, 1),
            "estimated_ai_load_mw": round(total_ai_load, 1),
            "ai_share_of_grid_pct": round(ai_share, 2),
            "grid_carbon_intensity": grid.carbon_intensity_kg_per_mwh,
            "grid_renewable_pct": grid.renewable_fraction_pct,
        }

    async def _get_best_region_for_compute(self, session: AsyncSession, args: Dict) -> Dict:
        """Find best region for compute based on optimization criteria"""
        optimize_for = args.get("optimize_for", "carbon")

        # Get latest metrics for all regions
        regions_result = await session.execute(select(GridRegionDB))
        regions = regions_result.scalars().all()

        region_scores = []
        for region in regions:
            metrics_result = await session.execute(
                select(GridMetricsDB)
                .where(GridMetricsDB.region_id == region.region_id)
                .order_by(desc(GridMetricsDB.timestamp_utc))
                .limit(1)
            )
            metrics = metrics_result.scalar_one_or_none()

            if metrics:
                if optimize_for == "carbon":
                    score = -metrics.carbon_intensity_kg_per_mwh  # Lower is better
                elif optimize_for == "cost":
                    score = -(metrics.lmp_energy_price_usd_mwh or 50)
                else:  # reliability
                    margin = metrics.total_generation_mw - metrics.load_mw
                    score = margin / metrics.total_generation_mw if metrics.total_generation_mw > 0 else 0

                region_scores.append({
                    "region_id": region.region_id,
                    "region_name": region.region_name,
                    "carbon_intensity": metrics.carbon_intensity_kg_per_mwh,
                    "renewable_pct": metrics.renewable_fraction_pct,
                    "score": score,
                })

        # Sort by score (higher is better)
        region_scores.sort(key=lambda x: x["score"], reverse=True)

        best = region_scores[0] if region_scores else None

        return {
            "optimize_for": optimize_for,
            "recommendation": best["region_id"] if best else None,
            "reason": f"Lowest carbon intensity at {best['carbon_intensity']:.0f} kg CO2/MWh" if best and optimize_for == "carbon" else "Best available option",
            "rankings": region_scores[:5],
        }


# Global MCP server instance
mcp_server = MCPServer()
