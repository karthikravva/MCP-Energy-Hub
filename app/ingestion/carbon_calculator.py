"""
Carbon Intensity Calculator
Calculates CO2 emissions intensity from generation fuel mix
"""

from typing import Dict


# Emission factors in kg CO2 per MWh
# Source: EPA eGRID, IPCC
EMISSION_FACTORS = {
    "natural_gas_mw": 410,      # Combined cycle gas turbine
    "coal_mw": 820,             # Average coal plant
    "nuclear_mw": 12,           # Lifecycle emissions
    "wind_mw": 11,              # Lifecycle emissions
    "solar_mw": 45,             # Lifecycle emissions (PV)
    "hydro_mw": 24,             # Lifecycle emissions
    "other_mw": 500,            # Conservative estimate for unknown
}


class CarbonIntensityCalculator:
    """
    Calculates grid carbon intensity from generation mix
    """

    def __init__(self, emission_factors: Dict[str, float] = None):
        self.emission_factors = emission_factors or EMISSION_FACTORS

    def calculate(self, generation_by_fuel: Dict[str, float], total_generation_mw: float) -> float:
        """
        Calculate carbon intensity in kg CO2 per MWh

        Args:
            generation_by_fuel: Dict with fuel type keys and MW values
            total_generation_mw: Total generation in MW

        Returns:
            Carbon intensity in kg CO2 / MWh
        """
        if total_generation_mw <= 0:
            return 0.0

        total_emissions = 0.0

        for fuel_type, generation_mw in generation_by_fuel.items():
            emission_factor = self.emission_factors.get(fuel_type, 500)
            total_emissions += generation_mw * emission_factor

        # Weighted average intensity
        carbon_intensity = total_emissions / total_generation_mw

        return round(carbon_intensity, 2)

    def calculate_renewable_fraction(self, generation_by_fuel: Dict[str, float], total_generation_mw: float) -> float:
        """
        Calculate percentage of generation from renewable sources
        """
        if total_generation_mw <= 0:
            return 0.0

        renewable_sources = ["wind_mw", "solar_mw", "hydro_mw"]
        renewable_mw = sum(
            generation_by_fuel.get(source, 0)
            for source in renewable_sources
        )

        return round((renewable_mw / total_generation_mw) * 100, 2)

    def estimate_emissions(self, load_mw: float, carbon_intensity: float, hours: float = 1.0) -> float:
        """
        Estimate total CO2 emissions for a given load

        Args:
            load_mw: Load in MW
            carbon_intensity: Carbon intensity in kg CO2 / MWh
            hours: Duration in hours

        Returns:
            Total emissions in kg CO2
        """
        energy_mwh = load_mw * hours
        return round(energy_mwh * carbon_intensity, 2)
