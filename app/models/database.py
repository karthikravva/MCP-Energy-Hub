"""
SQLAlchemy Database Models for MCP Energy Hub
Supports PostgreSQL (production) and SQLite (development/HuggingFace)
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime,
    ForeignKey, JSON, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base

# Use JSON for cross-database compatibility (works with both PostgreSQL and SQLite)
# For PostgreSQL-only deployments, you can use JSONB for better performance
JSONB = JSON  # Alias for compatibility

Base = declarative_base()


# =============================================================================
# GRID REGION TABLE
# =============================================================================

class GridRegionDB(Base):
    """
    Master entity: Balancing Authority / ISO / State-level grid region
    """
    __tablename__ = "grid_regions"

    region_id = Column(String(50), primary_key=True)
    region_name = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    coverage_states = Column(JSONB, default=list)
    region_type = Column(String(20), nullable=False)  # ISO, BA, STATE

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    metrics = relationship("GridMetricsDB", back_populates="region")
    data_centers = relationship("DataCenterDB", back_populates="region")
    corridor_metrics = relationship(
        "ComputeCorridorMetricsDB", back_populates="region")


# =============================================================================
# GRID METRICS TABLE (TIME-SERIES)
# =============================================================================

class GridMetricsDB(Base):
    """
    Time-series: Real-time grid metrics (5-min to 1-hour resolution)
    Partitioned by region_id + timestamp for TimescaleDB
    """
    __tablename__ = "grid_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    region_id = Column(String(50), ForeignKey(
        "grid_regions.region_id"), nullable=False, index=True)

    # Load
    load_mw = Column(Float, nullable=False)
    forecast_load_mw = Column(Float)

    # Generation
    total_generation_mw = Column(Float, nullable=False)
    generation_by_fuel = Column(JSONB, default=dict)

    # Interchange
    net_interchange_mw = Column(Float, default=0)

    # Derived
    renewable_fraction_pct = Column(Float, nullable=False)
    carbon_intensity_kg_per_mwh = Column(Float, nullable=False)

    # Pricing
    lmp_energy_price_usd_mwh = Column(Float)

    # Metadata
    source = Column(String(50))  # EIA, CAISO, ERCOT, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    region = relationship("GridRegionDB", back_populates="metrics")

    __table_args__ = (
        Index("ix_grid_metrics_region_time", "region_id", "timestamp_utc"),
        UniqueConstraint("region_id", "timestamp_utc",
                         name="uq_grid_metrics_region_time"),
    )


# =============================================================================
# DATA CENTER TABLE
# =============================================================================

class DataCenterDB(Base):
    """
    Entity: Physical data center facility
    """
    __tablename__ = "data_centers"

    dc_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    operator = Column(String(100), nullable=False, index=True)
    region_id = Column(String(50), ForeignKey(
        "grid_regions.region_id"), nullable=False, index=True)

    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Capacity
    max_capacity_mw = Column(Float, nullable=False)
    avg_pue = Column(Float, default=1.5)
    cooling_type = Column(String(50), default="Unknown")

    # Grid connection
    primary_grid_connection = Column(String(50), nullable=False)
    renewable_ppa_mw = Column(Float, default=0)

    # Metadata
    commissioned_year = Column(Integer)
    is_ai_focused = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    region = relationship("GridRegionDB", back_populates="data_centers")
    energy_estimates = relationship(
        "DataCenterEnergyEstimateDB", back_populates="data_center")


# =============================================================================
# DATA CENTER ENERGY ESTIMATE TABLE (TIME-SERIES)
# =============================================================================

class DataCenterEnergyEstimateDB(Base):
    """
    Time-series: Data center energy consumption estimates
    """
    __tablename__ = "data_center_energy_estimates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    dc_id = Column(String(100), ForeignKey(
        "data_centers.dc_id"), nullable=False, index=True)

    # Energy breakdown
    estimated_load_mw = Column(Float, nullable=False)
    estimated_it_load_mw = Column(Float, nullable=False)
    estimated_cooling_load_mw = Column(Float, nullable=False)

    # Efficiency
    pue = Column(Float, nullable=False)
    renewable_usage_pct = Column(Float, default=0)
    carbon_intensity_kg_per_mwh = Column(Float, nullable=False)

    # Metadata
    # model, telemetry, manual
    estimation_method = Column(String(50), default="model")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    data_center = relationship(
        "DataCenterDB", back_populates="energy_estimates")

    __table_args__ = (
        Index("ix_dc_energy_dc_time", "dc_id", "timestamp_utc"),
        UniqueConstraint("dc_id", "timestamp_utc",
                         name="uq_dc_energy_dc_time"),
    )


# =============================================================================
# COMPUTE CORRIDOR METRICS TABLE (TIME-SERIES)
# =============================================================================

class ComputeCorridorMetricsDB(Base):
    """
    Time-series: Aggregated AI compute corridor metrics per region
    """
    __tablename__ = "compute_corridor_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    region_id = Column(String(50), ForeignKey(
        "grid_regions.region_id"), nullable=False, index=True)

    # AI metrics
    ai_data_centers_count = Column(Integer, nullable=False)
    total_ai_load_mw = Column(Float, nullable=False)
    total_ai_cooling_mw = Column(Float, nullable=False)
    avg_pue_ai = Column(Float, nullable=False)
    gpu_utilization_proxy = Column(Float, default=0.5)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    region = relationship("GridRegionDB", back_populates="corridor_metrics")

    __table_args__ = (
        Index("ix_corridor_region_time", "region_id", "timestamp_utc"),
        UniqueConstraint("region_id", "timestamp_utc",
                         name="uq_corridor_region_time"),
    )


# =============================================================================
# INGESTION LOG TABLE
# =============================================================================

class IngestionLogDB(Base):
    """
    Tracks data ingestion jobs for monitoring and debugging
    """
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # EIA, CAISO, ERCOT, etc.
    job_type = Column(String(50), nullable=False)  # realtime, batch, backfill

    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)

    status = Column(String(20), nullable=False)  # running, success, failed
    records_processed = Column(Integer, default=0)
    error_message = Column(Text)

    job_metadata = Column(JSONB, default=dict)
