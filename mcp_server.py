#!/usr/bin/env python3
"""
MCP Energy Hub - Standalone MCP Server
Run this to start the MCP server for AI assistant integration

Usage:
    python mcp_server.py

Or add to your MCP client configuration:
    {
        "mcpServers": {
            "energy-hub": {
                "command": "python",
                "args": ["path/to/mcp_server.py"]
            }
        }
    }
"""

from app.db.session import init_db
from app.mcp.server import mcp_server
import asyncio
import json
import logging
import sys
from typing import Any, Dict

# Setup logging to stderr (stdout is for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-energy-hub")

# Import after logging setup


class MCPProtocolHandler:
    """
    Handles MCP protocol communication over stdio
    """

    def __init__(self):
        self.server = mcp_server
        self.request_id = 0

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming MCP message and return response"""
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")

        logger.debug(f"Received: {method}")

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "initialized":
                result = None  # Notification, no response needed
            elif method == "tools/list":
                result = self._handle_tools_list()
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "resources/list":
                result = {"resources": []}
            elif method == "prompts/list":
                result = {"prompts": []}
            else:
                logger.warning(f"Unknown method: {method}")
                return self._error_response(msg_id, -32601, f"Method not found: {method}")

            if result is None:
                return None  # No response for notifications

            return self._success_response(msg_id, result)

        except Exception as e:
            logger.error(f"Error handling {method}: {e}")
            return self._error_response(msg_id, -32603, str(e))

    def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
            },
            "serverInfo": {
                "name": "mcp-energy-hub",
                "version": "1.0.0",
            }
        }

    def _handle_tools_list(self) -> Dict:
        """Handle tools/list request"""
        return {"tools": self.server.list_tools()}

    async def _handle_tools_call(self, params: Dict) -> Dict:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        logger.info(f"Calling tool: {tool_name}")
        result = await self.server.call_tool(tool_name, arguments)

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, default=str)
                }
            ]
        }

    def _success_response(self, msg_id: Any, result: Any) -> Dict:
        """Create a success response"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }

    def _error_response(self, msg_id: Any, code: int, message: str) -> Dict:
        """Create an error response"""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": code,
                "message": message
            }
        }


async def read_message() -> Dict[str, Any]:
    """Read a JSON-RPC message from stdin"""
    # Read headers
    headers = {}
    while True:
        line = await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline
        )
        line = line.strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    # Read content
    content_length = int(headers.get("content-length", 0))
    if content_length > 0:
        content = await asyncio.get_event_loop().run_in_executor(
            None, lambda: sys.stdin.read(content_length)
        )
        return json.loads(content)

    return {}


def write_message(message: Dict[str, Any]):
    """Write a JSON-RPC message to stdout"""
    if message is None:
        return

    content = json.dumps(message)
    sys.stdout.write(f"Content-Length: {len(content)}\r\n\r\n{content}")
    sys.stdout.flush()


async def main():
    """Main entry point for MCP server"""
    logger.info("Starting MCP Energy Hub server...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    handler = MCPProtocolHandler()

    logger.info("MCP server ready, waiting for messages...")

    while True:
        try:
            message = await read_message()
            if not message:
                continue

            response = await handler.handle_message(message)
            write_message(response)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
