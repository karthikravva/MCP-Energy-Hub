"""
MCP Tools Definition
Defines the tools available to AI assistants via MCP protocol
"""

from typing import Any, Dict, List


def get_mcp_tools() -> List[Dict[str, Any]]:
    """
    Returns the list of tools available via MCP protocol
    """
    return [
        {
            "name": "get_grid_realtime",
            "description": "Get real-time grid metrics for a specific region including load, generation, carbon intensity, and renewable fraction",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "region_id": {
                        "type": "string",
                        "description": "Grid region ID (e.g., ERCOT, CAISO, PJM, NYISO, MISO, SPP, ISONE)",
                        "enum": ["ERCOT", "CAISO", "PJM", "NYISO", "MISO", "SPP", "ISONE"]
                    }
                },
                "required": ["region_id"]
            }
        },
        {
            "name": "get_grid_carbon",
            "description": "Get current carbon intensity for a grid region. Useful for carbon-aware compute scheduling.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "region_id": {
                        "type": "string",
                        "description": "Grid region ID",
                        "enum": ["ERCOT", "CAISO", "PJM", "NYISO", "MISO", "SPP", "ISONE"]
                    }
                },
                "required": ["region_id"]
            }
        },
        {
            "name": "get_grid_forecast",
            "description": "Get load and carbon intensity forecast for a region",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "region_id": {
                        "type": "string",
                        "description": "Grid region ID",
                        "enum": ["ERCOT", "CAISO", "PJM", "NYISO", "MISO", "SPP", "ISONE"]
                    },
                    "horizon_hours": {
                        "type": "integer",
                        "description": "Forecast horizon in hours (1-168)",
                        "default": 48,
                        "minimum": 1,
                        "maximum": 168
                    }
                },
                "required": ["region_id"]
            }
        },
        {
            "name": "list_grid_regions",
            "description": "List all available grid regions with their metadata",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_data_centers",
            "description": "List data centers, optionally filtered by region or operator",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "region_id": {
                        "type": "string",
                        "description": "Filter by grid region ID"
                    },
                    "operator": {
                        "type": "string",
                        "description": "Filter by operator name (e.g., AWS, Google, Microsoft)"
                    },
                    "ai_only": {
                        "type": "boolean",
                        "description": "Only return AI-focused data centers",
                        "default": False
                    }
                }
            }
        },
        {
            "name": "get_data_center_energy",
            "description": "Get energy consumption estimates for a specific data center",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dc_id": {
                        "type": "string",
                        "description": "Data center ID"
                    }
                },
                "required": ["dc_id"]
            }
        },
        {
            "name": "get_ai_impact",
            "description": "Get AI compute impact KPIs for a region including AI share of load, renewable coverage, and grid stress",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "region_id": {
                        "type": "string",
                        "description": "Grid region ID",
                        "enum": ["ERCOT", "CAISO", "PJM", "NYISO", "MISO", "SPP", "ISONE"]
                    }
                },
                "required": ["region_id"]
            }
        },
        {
            "name": "get_best_region_for_compute",
            "description": "Find the best region for running compute workloads based on carbon intensity and grid conditions",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "optimize_for": {
                        "type": "string",
                        "description": "What to optimize for",
                        "enum": ["carbon", "cost", "reliability"],
                        "default": "carbon"
                    }
                }
            }
        }
    ]
