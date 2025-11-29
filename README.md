---
title: MCP Energy Hub
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
tags:
  - mcp
  - building-mcp-track-enterprise
  - energy
  - carbon-aware
  - sustainability
  - ai-agents
  - climate-tech
app_port: 7860
---

<div align="center">

# ⚡ MCP Energy Hub

### Real-Time Energy Grid Intelligence for Carbon-Aware AI

[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-blue?style=for-the-badge&logo=anthropic)](https://modelcontextprotocol.io)
[![Hugging Face](https://img.shields.io/badge/🤗-Hugging%20Face-yellow?style=for-the-badge)](https://huggingface.co)
[![EIA Data](https://img.shields.io/badge/EIA-Real%20Time%20Data-green?style=for-the-badge)](https://www.eia.gov/opendata/)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

**🏆 MCP's 1st Birthday Hackathon Submission - Track 1: Building MCP (Enterprise)**

[🎬 Demo Video](#-demo-video) • [🚀 Try It Live](https://huggingface.co/spaces/MCP-1st-Birthday/mcp-energy-hub) • [📖 Documentation](#-mcp-tools) • [🐦 Share on X](https://twitter.com/intent/tweet?text=Check%20out%20MCP%20Energy%20Hub%20-%20Real-time%20energy%20grid%20intelligence%20for%20carbon-aware%20AI!%20%E2%9A%A1&url=https://huggingface.co/spaces/MCP-1st-Birthday/mcp-energy-hub)

</div>

---

## 🎯 The Problem

**AI compute is exploding, but the grid isn't always green.**

- Data centers consume **1-2% of global electricity** and growing rapidly
- AI training runs can emit as much CO2 as **5 cars over their lifetime**
- Most AI workloads run **without awareness of grid carbon intensity**
- Enterprises lack tools to **schedule compute when renewables are high**

## 💡 The Solution

**MCP Energy Hub** is an enterprise-grade MCP server that gives AI agents real-time visibility into the US power grid, enabling **carbon-aware compute scheduling**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    🤖 AI Agent (Claude, etc.)                    │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   MCP Protocol    │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│              ┌───────────────▼───────────────┐                  │
│              │      ⚡ MCP Energy Hub         │                  │
│              │  ┌─────────────────────────┐  │                  │
│              │  │ 8 MCP Tools for Energy  │  │                  │
│              │  │ Grid Intelligence       │  │                  │
│              │  └─────────────────────────┘  │                  │
│              └───────────────┬───────────────┘                  │
│                              │                                   │
│    ┌─────────────┬───────────┼───────────┬─────────────┐       │
│    ▼             ▼           ▼           ▼             ▼       │
│ ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐       │
│ │ERCOT│     │CAISO│     │ PJM │     │NYISO│     │MISO │       │
│ │Texas│     │Calif│     │ Mid │     │ NY  │     │Midwest      │
│ └─────┘     └─────┘     └─────┘     └─────┘     └─────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎬 Demo Video

> **📹 [Watch the 3-minute demo →](YOUR_VIDEO_LINK_HERE)**

*Shows: Real-time carbon queries, finding greenest region, AI impact analytics*

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🌍 **7 Grid Regions** | ERCOT, CAISO, PJM, NYISO, MISO, SPP, ISONE |
| ⚡ **Real-Time Data** | Live from EIA (US Energy Information Administration) |
| 🌱 **Carbon Intensity** | kg CO2/MWh for each region, updated hourly |
| 🔋 **Generation Mix** | Natural gas, coal, nuclear, wind, solar, hydro |
| 🏢 **Data Center Tracking** | Energy estimates, PUE, AI workload impact |
| 🎯 **Smart Scheduling** | Find the greenest region for your compute |
| 📊 **AI Impact KPIs** | Track AI's share of grid load |
| 🔌 **MCP Native** | Full Model Context Protocol support |

---

## 🛠️ MCP Tools

### 8 Tools for Energy Intelligence

| Tool | Description | Use Case |
|------|-------------|----------|
| `get_grid_realtime` | Real-time grid metrics | Monitor current load & generation |
| `get_grid_carbon` | Carbon intensity + recommendation | Carbon-aware scheduling |
| `get_grid_forecast` | Load & carbon forecast | Plan future workloads |
| `list_grid_regions` | Available grid regions | Discover coverage |
| `get_data_centers` | Data center info | Track facilities |
| `get_data_center_energy` | Energy consumption estimates | Audit energy use |
| `get_ai_impact` | AI compute KPIs | Measure AI's grid footprint |
| `get_best_region_for_compute` | **Find greenest region** | Optimize for carbon/cost |

### Example: Carbon-Aware Scheduling

```python
# AI Agent asks: "Where should I run this training job?"

result = mcp.call_tool("get_best_region_for_compute", {
    "optimize_for": "carbon"
})

# Response:
{
    "recommendation": "CAISO",
    "reason": "Lowest carbon intensity at 180 kg CO2/MWh",
    "rankings": [
        {"region": "CAISO", "carbon": 180, "renewable_pct": 45},
        {"region": "ERCOT", "carbon": 320, "renewable_pct": 28},
        {"region": "PJM", "carbon": 420, "renewable_pct": 12}
    ]
}
```

---

## 🚀 Quick Start

### Try the API

```bash
# Get carbon intensity for Texas grid
curl -X POST https://mcp-1st-birthday-mcp-energy-hub.hf.space/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_grid_carbon", "arguments": {"region_id": "ERCOT"}}'
```

### Response

```json
{
  "success": true,
  "result": {
    "region_id": "ERCOT",
    "timestamp": "2024-11-28T22:00:00Z",
    "carbon_intensity_kg_per_mwh": 320.5,
    "renewable_fraction_pct": 28.3,
    "recommendation": "Good - Moderate carbon intensity"
  }
}
```

### Connect to Claude Desktop

Add to your MCP settings:

```json
{
  "mcpServers": {
    "energy-hub": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/docs` | GET | Interactive Swagger UI |
| `/mcp/info` | GET | MCP server information |
| `/mcp/tools` | GET | List all MCP tools |
| `/mcp/tools/call` | POST | Execute an MCP tool |
| `/grid/regions` | GET | List grid regions |
| `/grid/{region}/realtime` | GET | Real-time metrics |
| `/grid/{region}/carbon` | GET | Carbon intensity |
| `/health` | GET | Health check |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     MCP Energy Hub                          │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   FastAPI    │  │  MCP Server  │  │  Data Ingestion  │ │
│  │   REST API   │  │  (8 Tools)   │  │  (EIA Collector) │ │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
│         │                 │                    │           │
│         └─────────────────┼────────────────────┘           │
│                           │                                │
│                    ┌──────▼──────┐                        │
│                    │  SQLite DB  │                        │
│                    │ Grid Metrics│                        │
│                    └─────────────┘                        │
├────────────────────────────────────────────────────────────┤
│                    External Data Sources                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │   EIA   │  │  ERCOT  │  │  CAISO  │  │   PJM   │      │
│  │   API   │  │   API   │  │   API   │  │   API   │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└────────────────────────────────────────────────────────────┘
```

---

## 🌍 Real-World Impact

### For Enterprises
- **Reduce carbon footprint** by scheduling AI workloads during high-renewable periods
- **Cost optimization** by running compute when energy prices are low
- **ESG reporting** with accurate AI energy consumption data

### For AI Developers
- **Carbon-aware training** - Train models when the grid is green
- **Transparent impact** - Know your model's carbon footprint
- **Automated scheduling** - Let AI agents make green decisions

### Potential Impact
- If 10% of AI workloads shifted to low-carbon periods: **~500,000 tons CO2/year saved**
- Real-time visibility enables **30-50% carbon reduction** for flexible workloads

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Python 3.11 |
| **Database** | SQLite (HF) / PostgreSQL (Production) |
| **MCP Protocol** | Native implementation |
| **Data Source** | EIA Open Data API |
| **Deployment** | Docker, Hugging Face Spaces |

---

## 📁 Project Structure

```
mcp-energy-hub/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── api/routes/          # REST endpoints
│   ├── mcp/                  # MCP server implementation
│   │   ├── server.py        # MCP protocol handler
│   │   ├── tools.py         # Tool definitions
│   │   └── routes.py        # HTTP MCP endpoints
│   ├── ingestion/           # Data collectors
│   │   └── eia_collector.py # EIA API integration
│   └── models/              # Database models
├── mcp_server.py            # Standalone MCP server (stdio)
├── Dockerfile               # HuggingFace deployment
└── README.md                # This file
```

---

## 🙏 Acknowledgments

- **[Anthropic](https://anthropic.com)** - For creating the MCP protocol
- **[Hugging Face](https://huggingface.co)** - For hosting this hackathon
- **[EIA](https://www.eia.gov)** - For open energy data
- **MCP's 1st Birthday Hackathon** - For the opportunity to build this

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **🐦 Twitter/X Post**: [Share your thoughts!](https://twitter.com/intent/tweet?text=Check%20out%20MCP%20Energy%20Hub%20-%20Real-time%20energy%20grid%20intelligence%20for%20carbon-aware%20AI!%20%E2%9A%A1&url=https://huggingface.co/spaces/MCP-1st-Birthday/mcp-energy-hub)
- **💬 HF Discussions**: [Ask questions here](https://huggingface.co/spaces/MCP-1st-Birthday/mcp-energy-hub/discussions)
- **🌐 Live Demo**: [Try it now!](https://huggingface.co/spaces/MCP-1st-Birthday/mcp-energy-hub)

---

<div align="center">

**Built with ❤️ for MCP's 1st Birthday Hackathon**

*Making AI compute sustainable, one query at a time* ⚡🌱

</div>
