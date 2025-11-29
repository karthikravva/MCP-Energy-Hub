"""
MCP (Model Context Protocol) Server Implementation
Enables AI assistants to query energy grid data
"""

from app.mcp.server import MCPServer
from app.mcp.tools import get_mcp_tools

__all__ = ["MCPServer", "get_mcp_tools"]
