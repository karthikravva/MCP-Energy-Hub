"""
MCP HTTP Endpoints
Provides HTTP interface for MCP tools (alternative to stdio)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.mcp.server import mcp_server

router = APIRouter(prefix="/mcp", tags=["MCP"])


class ToolCallRequest(BaseModel):
    """Request body for tool calls"""
    name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    """Response from tool calls"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/info")
async def get_server_info():
    """Get MCP server information"""
    return mcp_server.get_server_info()


@router.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    return {"tools": mcp_server.list_tools()}


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """
    Call an MCP tool

    Example:
    ```json
    {
        "name": "get_grid_realtime",
        "arguments": {"region_id": "ERCOT"}
    }
    ```
    """
    result = await mcp_server.call_tool(request.name, request.arguments)

    if "error" in result:
        return ToolCallResponse(success=False, error=result["error"])

    return ToolCallResponse(success=True, result=result)


@router.get("/tools/{tool_name}/schema")
async def get_tool_schema(tool_name: str):
    """Get the schema for a specific tool"""
    for tool in mcp_server.list_tools():
        if tool["name"] == tool_name:
            return tool

    raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
