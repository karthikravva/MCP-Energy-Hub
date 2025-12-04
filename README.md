<div align="center">

# ⚡ MCP Energy Hub

### Real-Time Energy Grid Intelligence for Carbon-Aware AI

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-blue?style=for-the-badge&logo=anthropic)](https://modelcontextprotocol.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

[![GitHub Stars](https://img.shields.io/github/stars/karthikravva/MCP-Energy-Hub?style=social)](https://github.com/karthikravva/MCP-Energy-Hub)
[![GitHub Forks](https://img.shields.io/github/forks/karthikravva/MCP-Energy-Hub?style=social)](https://github.com/karthikravva/MCP-Energy-Hub/fork)

**Enterprise-grade MCP server providing real-time US power grid intelligence for carbon-aware AI compute scheduling**

[📖 Documentation](#-mcp-tools) • [🚀 Quick Start](#-quick-start) • [🤝 Contributing](CONTRIBUTING.md) • [📜 License](LICENSE)

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

### Prerequisites

- Python 3.11+
- [EIA API Key](https://www.eia.gov/opendata/register.php) (free)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-energy-hub.git
cd mcp-energy-hub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your EIA_API_KEY
```

### Run the Server

```bash
# Start the FastAPI server
python -m uvicorn app.main:app --reload --port 8000

# Or run the standalone MCP server (for Claude Desktop)
python mcp_server.py
```

### Try the API

```bash
# Get carbon intensity for Texas grid
curl -X POST http://localhost:8000/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_grid_carbon", "arguments": {"region_id": "ERCOT"}}'
```

### Example Response

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

Add to your Claude Desktop MCP settings (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "energy-hub": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-energy-hub/mcp_server.py"],
      "env": {
        "EIA_API_KEY": "your-api-key-here"
      }
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

## � Docker Deployment

```bash
# Build the Docker image
docker build -t mcp-energy-hub .

# Run the container
docker run -p 8000:8000 -e EIA_API_KEY=your-key mcp-energy-hub
```

---

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

---

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🙏 Acknowledgments

- **[Anthropic](https://anthropic.com)** - For creating the MCP protocol
- **[EIA](https://www.eia.gov)** - For open energy data APIs
- **[FastAPI](https://fastapi.tiangolo.com)** - For the excellent web framework

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **� MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **⚡ EIA Open Data**: [eia.gov/opendata](https://www.eia.gov/opendata/)
- **🐛 Report Issues**: [GitHub Issues](https://github.com/karthikravva/MCP-Energy-Hub/issues)

---

<div align="center">

**Made with ❤️ for sustainable AI**

*Helping AI compute become carbon-aware, one query at a time* ⚡🌱

⭐ Star this repo if you find it useful!

</div>
