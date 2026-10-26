# -*- coding: utf-8 -*-
"""
OMNISTATE Model Context Protocol (MCP) JSON-RPC 2.0 Stdio Handler
Zero external dependencies, standards-compliant MCP server protocol engine.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from omnistate.constants import PROTOCOL_VERSION, VERSION
from omnistate.mcp.tools import McpToolRegistry


class McpServer:
    """Zero-dependency stdio JSON-RPC server adhering to the Model Context Protocol."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.registry = McpToolRegistry(self.workspace_root)
        self.is_initialized = False

    def send_response(self, response: Dict[str, Any]) -> None:
        payload = json.dumps(response, ensure_ascii=False)
        sys.stdout.write(f"{payload}\n")
        sys.stdout.flush()

    def send_error(self, req_id: Any, code: int, message: str) -> None:
        self.send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        })

    def handle_request(self, message: Dict[str, Any]) -> None:
        req_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        # Handle notifications (requests without id)
        if req_id is None:
            if method == "notifications/initialized":
                self.is_initialized = True
            return

        # 1. initialize
        if method == "initialize":
            self.is_initialized = True
            self.send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {
                            "listChanged": False,
                        }
                    },
                    "serverInfo": {
                        "name": "omnistate",
                        "version": VERSION,
                    },
                },
            })

        # 2. ping
        elif method == "ping":
            self.send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            })

        # 3. tools/list
        elif method == "tools/list":
            tools = self.registry.get_tool_definitions()
            self.send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": tools,
                },
            })

        # 4. tools/call
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            success, output = self.registry.call_tool(tool_name, tool_args)
            self.send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": output,
                        }
                    ],
                    "isError": not success,
                },
            })

        else:
            self.send_error(req_id, -32601, f"Method '{method}' not found")

    def run_stdio(self) -> None:
        """Main stdio loop reading messages from standard input."""
        # Ensure utf-8 stdio
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            # Support Content-Length prefix if present
            if line.lower().startswith("content-length:"):
                try:
                    length = int(line.split(":", 1)[1].strip())
                    # Consume next empty line
                    sys.stdin.readline()
                    body = sys.stdin.read(length)
                    message = json.loads(body)
                except Exception as e:
                    sys.stderr.write(f"Failed to read framed message: {e}\n")
                    continue
            else:
                try:
                    message = json.loads(line)
                except Exception as e:
                    sys.stderr.write(f"Malformed JSON: {e}\n")
                    continue

            if isinstance(message, dict):
                self.handle_request(message)
