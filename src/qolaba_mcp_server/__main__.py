from __future__ import annotations

from fastmcp import FastMCP

from .server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()


