#!/usr/bin/env python3
"""
Qolaba API MCP Server - Main Entry Point

This is the main entry point for the Qolaba API MCP Server.
Run this script to start the server in stdio mode for MCP communication.

Usage:
    python main.py

Environment Variables:
    See .env.example for required configuration variables.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from qolaba_mcp_server.server import mcp
from qolaba_mcp_server.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the Qolaba MCP Server."""
    try:
        # Load and validate settings
        settings = get_settings()

        logger.info("Starting Qolaba API MCP Server")
        logger.info(f"Environment: {settings.env}")
        logger.info(f"API Base URL: {settings.api_base_url}")
        logger.info(f"Auth Method: {settings.auth_method}")

        # Validate configuration before starting
        if settings.auth_method == "none" and settings.env in ["production", "staging"]:
            logger.error("No authentication configured for production/staging environment!")
            sys.exit(1)

        # Run the MCP server in stdio mode
        logger.info("Server starting in stdio mode...")
        await mcp.run(transport="stdio")

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)