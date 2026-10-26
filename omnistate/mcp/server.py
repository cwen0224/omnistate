# -*- coding: utf-8 -*-
"""
OMNISTATE MCP Server Entrypoint
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from omnistate.mcp.protocol import McpServer


def main() -> None:
    parser = argparse.ArgumentParser(description="OMNISTATE Model Context Protocol (MCP) Server")
    parser.add_argument("--workspace", default=".", help="Target workspace path (default: current directory)")
    args = parser.parse_args()

    workspace_path = Path(args.workspace).resolve()
    server = McpServer(workspace_path)
    server.run_stdio()


if __name__ == "__main__":
    main()
