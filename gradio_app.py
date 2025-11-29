"""
MCP Energy Hub - Gradio Interface
Clean, minimal UI for MCP's 1st Birthday Hackathon
"""

import gradio as gr
import httpx
import os

# API base URL - auto-detect for HuggingFace Spaces


def get_api_base():
    # When running on HF Spaces, use localhost since we're in same container
    space_id = os.environ.get("SPACE_ID")
    if space_id:
        return "http://localhost:7860"
    return "http://127.0.0.1:8000"


API_BASE = get_api_base()


async def call_mcp_tool(tool_name: str, arguments: dict):
    """Call an MCP tool via the HTTP API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"{API_BASE}/mcp/tools/call"
            response = await client.post(
                url,
                json={"name": tool_name, "arguments": arguments}
            )
            data = response.json()
            if data.get("success"):
                return data.get("result", {})
            return {"error": data.get("error", "Unknown error")}
        except httpx.ConnectError:
            return {"error": "Cannot connect to API. Make sure the server is running."}
        except Exception as e:
            return {"error": str(e)}


async def get_carbon_intensity(region: str):
    """Get carbon intensity for a region"""
    if not region:
        return "Please select a region", "", ""

    result = await call_mcp_tool("get_grid_carbon", {"region_id": region})

    if "error" in result:
        return f"Error: {result['error']}", "—", "—"

    carbon = result.get("carbon_intensity_kg_per_mwh", 0)
    renewable = result.get("renewable_fraction_pct", 0)
    recommendation = result.get("recommendation", "")
    timestamp = result.get("timestamp", "")[:16].replace("T", " ")

    # Simple status indicator
    if carbon < 200:
        status = "🟢 Excellent"
    elif carbon < 350:
        status = "🟡 Good"
    elif carbon < 500:
        status = "🟠 Fair"
    else:
        status = "🔴 High"

    summary = f"""### {region} Grid Status: {status}

**Carbon Intensity:** {carbon:.0f} kg CO₂/MWh

**Renewable Energy:** {renewable:.1f}%

**Recommendation:** {recommendation}

*Updated: {timestamp} UTC*
"""
    return summary, f"{carbon:.0f}", f"{renewable:.1f}%"


async def find_best_region(optimize_for: str):
    """Find the best region for compute"""
    result = await call_mcp_tool("get_best_region_for_compute",
                                 {"optimize_for": optimize_for.lower()})

    if "error" in result:
        return f"Error: {result['error']}"

    recommendation = result.get("recommendation", "Unknown")
    reason = result.get("reason", "")
    rankings = result.get("rankings", [])

    # Build clean rankings table
    table = "| Rank | Region | Carbon | Renewable |\n|:----:|:------:|-------:|----------:|\n"
    for i, r in enumerate(rankings[:5], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f" {i}"
        table += f"| {medal} | {r.get('region_id', 'N/A')} | {r.get('carbon_intensity', 0):.0f} kg | {r.get('renewable_pct', 0):.1f}% |\n"

    return f"""### Recommended: {recommendation}

{reason}

---

#### Regional Rankings (by {optimize_for.lower()})

{table}
"""


async def get_realtime_data(region: str):
    """Get real-time grid data"""
    if not region:
        return "Please select a region"

    result = await call_mcp_tool("get_grid_realtime", {"region_id": region})

    if "error" in result:
        return f"Error: {result['error']}"

    gen = result.get("generation_by_fuel", {})
    timestamp = result.get("timestamp", "")[:16].replace("T", " ")

    return f"""### {region} Real-Time Data

| Metric | Value |
|:-------|------:|
| **Load** | {result.get('load_mw', 0):,.0f} MW |
| **Generation** | {result.get('total_generation_mw', 0):,.0f} MW |
| **Carbon Intensity** | {result.get('carbon_intensity_kg_per_mwh', 0):.0f} kg/MWh |
| **Renewable** | {result.get('renewable_fraction_pct', 0):.1f}% |

#### Generation Mix

| Source | MW |
|:-------|---:|
| Natural Gas | {gen.get('natural_gas_mw', 0):,.0f} |
| Nuclear | {gen.get('nuclear_mw', 0):,.0f} |
| Wind | {gen.get('wind_mw', 0):,.0f} |
| Solar | {gen.get('solar_mw', 0):,.0f} |
| Hydro | {gen.get('hydro_mw', 0):,.0f} |
| Coal | {gen.get('coal_mw', 0):,.0f} |
| Other | {gen.get('other_mw', 0):,.0f} |

*Updated: {timestamp} UTC*
"""


async def get_all_regions():
    """Get overview of all regions"""
    result = await call_mcp_tool("list_grid_regions", {})

    if "error" in result:
        return f"Error: {result['error']}"

    regions = result.get("regions", [])

    table = "| Region | Name | States |\n|:-------|:-----|:-------|\n"
    for r in regions:
        states = ", ".join(r.get("states", [])[:4])
        if len(r.get("states", [])) > 4:
            states += "..."
        table += f"| **{r.get('region_id')}** | {r.get('name')} | {states} |\n"

    return f"""### US Grid Regions

{table}

*Data from EIA (Energy Information Administration)*
"""


async def get_ai_impact(region: str):
    """Get AI impact KPIs for a region"""
    if not region:
        return "Please select a region"

    result = await call_mcp_tool("get_ai_impact", {"region_id": region})

    if "error" in result:
        return f"Error: {result['error']}"

    timestamp = result.get("timestamp", "")[:16].replace("T", " ")

    return f"""### AI Compute Impact for {region}

| Metric | Value |
|:-------|------:|
| **AI Data Centers** | {result.get('ai_data_centers_count', 0)} |
| **Total AI Capacity** | {result.get('total_ai_capacity_mw', 0):,.1f} MW |
| **Estimated AI Load** | {result.get('estimated_ai_load_mw', 0):,.1f} MW |
| **AI Share of Grid** | {result.get('ai_share_of_grid_pct', 0):.2f}% |
| **Grid Carbon Intensity** | {result.get('grid_carbon_intensity', 0):.0f} kg/MWh |
| **Grid Renewable %** | {result.get('grid_renewable_pct', 0):.1f}% |

*Updated: {timestamp} UTC*
"""


async def get_data_centers(region: str, operator: str):
    """Get data centers with optional filters and real-time grid data"""
    arguments = {}
    if region and region != "All":
        arguments["region_id"] = region
    if operator and operator != "All":
        arguments["operator"] = operator

    result = await call_mcp_tool("get_data_centers", arguments)

    if "error" in result:
        return f"Error: {result['error']}"

    dcs = result.get("data_centers", [])
    count = result.get("count", 0)

    if count == 0:
        return "No data centers found. Try different filters."

    # Get real-time grid data for each region
    region_carbon = {}
    for dc in dcs:
        r = dc.get("region_id")
        if r and r not in region_carbon:
            grid_data = await call_mcp_tool("get_grid_carbon", {"region_id": r})
            if "error" not in grid_data:
                region_carbon[r] = {
                    "carbon": grid_data.get("carbon_intensity_kg_per_mwh", 0),
                    "renewable": grid_data.get("renewable_fraction_pct", 0)
                }

    table = "| Name | Operator | Region | Capacity | PUE | Grid Carbon | AI |\n|:-----|:---------|:-------|--------:|----:|------------:|:--:|\n"
    for dc in dcs[:20]:
        ai_badge = "✅" if dc.get("is_ai_focused") else "—"
        r = dc.get("region_id", "")
        carbon = region_carbon.get(r, {}).get("carbon", 0)
        table += f"| {dc.get('name', 'N/A')} | {dc.get('operator', 'N/A')} | {r} | {dc.get('max_capacity_mw', 0):.0f} MW | {dc.get('avg_pue', 0):.2f} | {carbon:.0f} kg | {ai_badge} |\n"

    # Summary stats
    total_capacity = sum(dc.get("max_capacity_mw", 0) for dc in dcs)
    ai_count = sum(1 for dc in dcs if dc.get("is_ai_focused"))

    return f"""### Data Centers ({count} found)

**Total Capacity:** {total_capacity:,.0f} MW | **AI-Focused:** {ai_count} facilities

{table}

*Grid Carbon = Real-time carbon intensity (kg CO₂/MWh)*
"""


async def get_dc_energy(dc_id: str):
    """Get energy estimates for a data center"""
    if not dc_id:
        return "Please enter a data center ID"

    result = await call_mcp_tool("get_data_center_energy", {"dc_id": dc_id})

    if "error" in result:
        return f"Error: {result['error']}"

    return f"""### Energy Estimates for {result.get('name', dc_id)}

| Metric | Value |
|:-------|------:|
| **Estimated Load** | {result.get('estimated_load_mw', 0):,.1f} MW |
| **IT Load** | {result.get('estimated_it_load_mw', 0):,.1f} MW |
| **Cooling Load** | {result.get('estimated_cooling_load_mw', 0):,.1f} MW |
| **PUE** | {result.get('pue', 0):.2f} |
| **Carbon Intensity** | {result.get('carbon_intensity_kg_per_mwh', 0):.0f} kg/MWh |
| **Hourly Emissions** | {result.get('estimated_hourly_emissions_kg', 0):,.0f} kg CO₂ |
"""


# Clean, minimal theme
theme = gr.themes.Base(
    primary_hue="emerald",
    secondary_hue="gray",
    neutral_hue="gray",
    font=gr.themes.GoogleFont("Inter"),
).set(
    body_background_fill="#fafafa",
    block_background_fill="white",
    block_border_width="1px",
    block_border_color="#e5e7eb",
    block_radius="8px",
    button_primary_background_fill="#059669",
    button_primary_background_fill_hover="#047857",
)

# Build the Gradio interface
with gr.Blocks(theme=theme, title="MCP Energy Hub") as demo:

    # Simple header
    gr.Markdown("""
# ⚡ MCP Energy Hub

Real-time energy grid intelligence for carbon-aware AI compute.

*MCP's 1st Birthday Hackathon — Track 1: Building MCP (Enterprise)*

---
""")

    with gr.Tabs():
        # Tab 1: Carbon Check
        with gr.TabItem("Carbon Intensity"):
            gr.Markdown(
                "Check the current carbon intensity of any US grid region.")

            with gr.Row():
                with gr.Column(scale=2):
                    region_select = gr.Dropdown(
                        choices=["ERCOT", "CAISO", "PJM",
                                 "NYISO", "MISO", "SPP", "ISONE"],
                        value="CAISO",
                        label="Grid Region"
                    )
                with gr.Column(scale=1):
                    carbon_value = gr.Textbox(
                        label="Carbon (kg/MWh)", interactive=False)
                with gr.Column(scale=1):
                    renewable_value = gr.Textbox(
                        label="Renewable %", interactive=False)

            check_btn = gr.Button("Check Carbon Intensity", variant="primary")
            carbon_output = gr.Markdown()

            check_btn.click(
                fn=get_carbon_intensity,
                inputs=[region_select],
                outputs=[carbon_output, carbon_value, renewable_value]
            )

            # Auto-load on region change
            region_select.change(
                fn=get_carbon_intensity,
                inputs=[region_select],
                outputs=[carbon_output, carbon_value, renewable_value]
            )

        # Tab 2: Find Best Region
        with gr.TabItem("Find Best Region"):
            gr.Markdown("Find the optimal region for your compute workload.")

            optimize_select = gr.Dropdown(
                choices=["Carbon", "Cost", "Reliability"],
                value="Carbon",
                label="Optimize For"
            )
            find_btn = gr.Button("Find Best Region", variant="primary")
            best_output = gr.Markdown()

            find_btn.click(
                fn=find_best_region,
                inputs=[optimize_select],
                outputs=[best_output]
            )

        # Tab 3: Real-Time Data
        with gr.TabItem("Real-Time Data"):
            gr.Markdown("View detailed real-time grid metrics.")

            realtime_region = gr.Dropdown(
                choices=["ERCOT", "CAISO", "PJM",
                         "NYISO", "MISO", "SPP", "ISONE"],
                value="ERCOT",
                label="Grid Region"
            )
            realtime_btn = gr.Button("Get Real-Time Data", variant="primary")
            realtime_output = gr.Markdown()

            realtime_btn.click(
                fn=get_realtime_data,
                inputs=[realtime_region],
                outputs=[realtime_output]
            )

        # Tab 4: AI Impact
        with gr.TabItem("AI Impact"):
            gr.Markdown("Track AI compute's impact on the power grid.")

            ai_region = gr.Dropdown(
                choices=["ERCOT", "CAISO", "PJM",
                         "NYISO", "MISO", "SPP", "ISONE"],
                value="ERCOT",
                label="Grid Region"
            )
            ai_btn = gr.Button("Get AI Impact", variant="primary")
            ai_output = gr.Markdown()

            ai_btn.click(
                fn=get_ai_impact,
                inputs=[ai_region],
                outputs=[ai_output]
            )

        # Tab 5: Data Centers
        with gr.TabItem("Data Centers"):
            gr.Markdown("Browse data centers and their energy consumption.")

            with gr.Row():
                dc_region = gr.Dropdown(
                    choices=["All", "ERCOT", "CAISO", "PJM",
                             "NYISO", "MISO", "SPP", "ISONE"],
                    value="All",
                    label="Filter by Region"
                )
                dc_operator = gr.Dropdown(
                    choices=["All", "AWS", "Google",
                             "Microsoft", "Meta", "Oracle"],
                    value="All",
                    label="Filter by Operator"
                )

            dc_btn = gr.Button("Search Data Centers", variant="primary")
            dc_output = gr.Markdown()

            dc_btn.click(
                fn=get_data_centers,
                inputs=[dc_region, dc_operator],
                outputs=[dc_output]
            )

            gr.Markdown("---")
            gr.Markdown("#### Get Energy Estimates for a Data Center")

            with gr.Row():
                dc_id_input = gr.Textbox(
                    label="Data Center ID",
                    placeholder="e.g., aws-us-east-1"
                )
                dc_energy_btn = gr.Button(
                    "Get Energy Estimates", variant="secondary")

            dc_energy_output = gr.Markdown()

            dc_energy_btn.click(
                fn=get_dc_energy,
                inputs=[dc_id_input],
                outputs=[dc_energy_output]
            )

        # Tab 6: All Regions
        with gr.TabItem("All Regions"):
            gr.Markdown("Overview of all available US grid regions.")

            regions_btn = gr.Button("Load Regions", variant="primary")
            regions_output = gr.Markdown()

            regions_btn.click(
                fn=get_all_regions,
                inputs=[],
                outputs=[regions_output]
            )

        # Tab 7: API Reference
        with gr.TabItem("API & MCP"):
            gr.Markdown("""
### MCP Tools

This server provides **8 MCP tools** for energy grid intelligence:

| Tool | Description |
|:-----|:------------|
| `get_grid_realtime` | Real-time grid metrics |
| `get_grid_carbon` | Carbon intensity with recommendation |
| `get_grid_forecast` | Load and carbon forecast |
| `list_grid_regions` | List available regions |
| `get_data_centers` | Data center information |
| `get_data_center_energy` | Energy consumption estimates |
| `get_ai_impact` | AI compute impact KPIs |
| `get_best_region_for_compute` | Find optimal region |

---

### HTTP API

**Endpoint:** `POST /mcp/tools/call`

**Example:**
```bash
curl -X POST https://your-space.hf.space/mcp/tools/call \\
  -H "Content-Type: application/json" \\
  -d '{"name": "get_grid_carbon", "arguments": {"region_id": "ERCOT"}}'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "region_id": "ERCOT",
    "carbon_intensity_kg_per_mwh": 380.2,
    "renewable_fraction_pct": 15.8,
    "recommendation": "Fair - Consider scheduling non-urgent workloads for later"
  }
}
```

---

### MCP Client Config

Add to your MCP settings:

```json
{
  "mcpServers": {
    "energy-hub": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```

---

### API Documentation

Full API docs available at [/docs](/docs)
""")

    # Footer
    gr.Markdown("""
---

Built for [MCP's 1st Birthday Hackathon](https://huggingface.co/MCP-1st-Birthday) | 
Data: [EIA Open Data](https://www.eia.gov/opendata/) | 
[API Docs](/docs)
""")


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
