"""
Health check routes for the Qolaba MCP Server.

This module integrates health check endpoints into the main server application,
providing container orchestration-compatible health monitoring.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from ..health.endpoints import (
    health_check_endpoint,
    readiness_probe_endpoint,
    liveness_probe_endpoint,
    simple_health_check
)
from ..core.logging_config import get_module_logger

logger = get_module_logger("server.health_routes")

# Create router for health endpoints
health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get(
    "",
    summary="System Health Check",
    description="""
    Comprehensive system health check endpoint suitable for container orchestration,
    load balancers, and monitoring systems.
    
    **HTTP Status Codes:**
    - `200`: System is healthy and ready to receive traffic
    - `503`: System is degraded or unhealthy - should not receive traffic
    - `500`: Health check system failure
    
    **Query Parameters:**
    - `detailed`: Include detailed component information (default: true)
    - `format`: Response format - 'json' for full details, 'simple' for basic status
    
    **Usage Examples:**
    - Docker HEALTHCHECK: `curl -f http://localhost:8000/health`
    - Kubernetes livenessProbe: `GET /health?detailed=false`
    - Load balancer health check: `GET /health?format=simple`
    """,
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "healthy": True,
                        "timestamp": "2025-09-13T21:02:00Z",
                        "uptime_seconds": 1234.5,
                        "version": "1.0.0",
                        "summary": {
                            "total_components": 5,
                            "healthy_components": 5,
                            "degraded_components": 0,
                            "unhealthy_components": 0,
                            "health_check_duration_ms": 45.2
                        },
                        "components": [
                            {
                                "name": "api_connectivity",
                                "status": "healthy",
                                "healthy": True,
                                "message": "API is reachable",
                                "response_time_ms": 12.3,
                                "last_checked": "2025-09-13T21:02:00Z",
                                "metadata": {"api_base_url": "https://api.qolaba.ai/v1"}
                            }
                        ],
                        "request_id": "health_check_abc123",
                        "response_time_ms": 45.2
                    }
                }
            }
        },
        503: {
            "description": "System is degraded or unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "healthy": False,
                        "timestamp": "2025-09-13T21:02:00Z",
                        "unhealthy_components": [
                            {
                                "name": "api_connectivity",
                                "message": "API connectivity check failed",
                                "status": "unhealthy"
                            }
                        ],
                        "request_id": "health_check_def456",
                        "response_time_ms": 67.8
                    }
                }
            }
        }
    }
)
async def get_health_status(
    request: Request,
    detailed: bool = Query(True, description="Include detailed component information"),
    format: str = Query("json", regex="^(json|simple)$", description="Response format")
) -> JSONResponse:
    """Get comprehensive system health status."""
    logger.debug("Health check route accessed", extra={
        "detailed": detailed,
        "format": format,
        "client_ip": request.client.host if request.client else "unknown"
    })
    
    return await health_check_endpoint(request, detailed=detailed, format=format)


@health_router.get(
    "/ready",
    summary="Readiness Probe",
    description="""
    Kubernetes-style readiness probe endpoint.
    
    This endpoint indicates whether the service is ready to receive traffic.
    It returns HTTP 200 only if all critical components are healthy.
    
    **Use Cases:**
    - Kubernetes readinessProbe
    - Service mesh ready checks
    - Load balancer backend health
    """,
    responses={
        200: {
            "description": "Service is ready to receive traffic",
            "content": {
                "application/json": {
                    "example": {
                        "ready": True,
                        "status": "ready",
                        "timestamp": "2025-09-13T21:02:00Z",
                        "request_id": "readiness_abc123",
                        "response_time_ms": 15.4
                    }
                }
            }
        },
        503: {
            "description": "Service is not ready",
            "content": {
                "application/json": {
                    "example": {
                        "ready": False,
                        "status": "not_ready",
                        "reason": "System status: degraded",
                        "timestamp": "2025-09-13T21:02:00Z",
                        "request_id": "readiness_def456"
                    }
                }
            }
        }
    }
)
async def readiness_probe(request: Request) -> JSONResponse:
    """Kubernetes-style readiness probe."""
    return await readiness_probe_endpoint(request)


@health_router.get(
    "/live",
    summary="Liveness Probe",
    description="""
    Kubernetes-style liveness probe endpoint.
    
    This endpoint indicates whether the service is alive and should not be restarted.
    It returns HTTP 200 as long as the basic service functionality is working.
    
    **Use Cases:**
    - Kubernetes livenessProbe
    - Container restart decisions
    - Basic service monitoring
    """,
    responses={
        200: {
            "description": "Service is alive",
            "content": {
                "application/json": {
                    "example": {
                        "alive": True,
                        "status": "alive",
                        "uptime_seconds": 1234.5,
                        "timestamp": 1694637720.123,
                        "request_id": "liveness_abc123",
                        "response_time_ms": 2.1
                    }
                }
            }
        }
    }
)
async def liveness_probe(request: Request) -> JSONResponse:
    """Kubernetes-style liveness probe."""
    return await liveness_probe_endpoint(request)


@health_router.get(
    "/simple",
    summary="Simple Health Check",
    description="""
    Lightweight health check endpoint for basic monitoring.
    
    Returns minimal health information with low overhead.
    Suitable for frequent polling by monitoring systems.
    """,
    responses={
        200: {
            "description": "Basic health information",
            "content": {
                "application/json": {
                    "example": {
                        "healthy": True,
                        "status": "healthy",
                        "uptime_seconds": 1234.5,
                        "timestamp": "2025-09-13T21:02:00Z"
                    }
                }
            }
        }
    }
)
async def simple_health_status() -> dict:
    """Get simple health status with minimal overhead."""
    logger.debug("Simple health check accessed")
    return await simple_health_check()


# Alternative endpoint paths for compatibility
@health_router.get(
    "/check",
    summary="Health Check (Alias)",
    description="Alternative endpoint path for health checking (alias for /health)",
    include_in_schema=False
)
async def health_check_alias(request: Request) -> JSONResponse:
    """Alternative health check endpoint path."""
    return await health_check_endpoint(request, detailed=False, format="simple")


@health_router.get(
    "/status", 
    summary="Status Check (Alias)",
    description="Alternative endpoint path for status checking",
    include_in_schema=False
)
async def status_check_alias(request: Request) -> JSONResponse:
    """Alternative status check endpoint path."""
    return await health_check_endpoint(request, detailed=True, format="json")


def get_health_router() -> APIRouter:
    """
    Get the configured health check router.
    
    Returns:
        APIRouter configured with health check endpoints
    """
    return health_router


# Middleware for request ID injection (if not already handled)
@health_router.middleware("http")
async def add_health_request_id(request: Request, call_next):
    """Add request ID to health check requests if not present."""
    if not hasattr(request.state, 'request_id'):
        import uuid
        request.state.request_id = f"health_{uuid.uuid4().hex[:8]}"
    
    response = await call_next(request)
    return response