"""
HTTP endpoints for health checking functionality.

This module provides HTTP endpoints that can be used by container orchestration
systems, load balancers, and monitoring tools to check system health.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from ..core.logging_config import get_module_logger, get_performance_logger
from .health_check import get_health_service, HealthStatus


logger = get_module_logger("health.endpoints")
perf_logger = get_performance_logger("health.endpoints")


async def health_check_endpoint(
    request: Request,
    detailed: bool = True,
    format: str = "json"
) -> JSONResponse:
    """
    Main health check endpoint for container orchestration.
    
    This endpoint returns HTTP 200 for healthy systems and HTTP 503 for
    unhealthy systems, making it suitable for container health checks,
    load balancer health monitoring, and service discovery.
    
    Args:
        request: FastAPI request object
        detailed: Whether to include detailed component information
        format: Response format ('json' or 'simple')
        
    Returns:
        JSONResponse with health status
        
    HTTP Status Codes:
        - 200: System is healthy
        - 503: System is unhealthy or degraded
        - 500: Health check system failure
    """
    start_time = time.time()
    request_id = getattr(request.state, 'request_id', 'health_check')
    
    logger.info("Health check endpoint accessed", extra={
        "request_id": request_id,
        "detailed": detailed,
        "format": format,
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    })
    
    try:
        # Get health status from service
        health_service = get_health_service()
        system_health = await health_service.get_health_status(include_details=detailed)
        
        # Determine HTTP status code
        if system_health.status == HealthStatus.HEALTHY:
            http_status = 200
        else:
            # Return 503 (Service Unavailable) for degraded or unhealthy systems
            # This signals to load balancers and orchestrators that the service
            # should not receive traffic
            http_status = 503
        
        # Prepare response based on format
        if format == "simple":
            response_data = {
                "status": system_health.status.value,
                "healthy": system_health.is_healthy,
                "timestamp": system_health.timestamp,
                "uptime_seconds": system_health.uptime_seconds
            }
        else:
            # Full JSON response with all details
            response_data = {
                "status": system_health.status.value,
                "healthy": system_health.is_healthy,
                "timestamp": system_health.timestamp,
                "uptime_seconds": system_health.uptime_seconds,
                "version": system_health.version,
                "summary": system_health.summary
            }
            
            if detailed:
                response_data["components"] = [
                    {
                        "name": comp.name,
                        "status": comp.status.value,
                        "healthy": comp.status == HealthStatus.HEALTHY,
                        "message": comp.message,
                        "response_time_ms": comp.response_time_ms,
                        "last_checked": comp.last_checked,
                        "metadata": comp.metadata
                    }
                    for comp in system_health.components
                ]
                
                # Add problem summaries for quick diagnosis
                if system_health.unhealthy_components:
                    response_data["unhealthy_components"] = [
                        {
                            "name": comp.name,
                            "message": comp.message,
                            "status": comp.status.value
                        }
                        for comp in system_health.unhealthy_components
                    ]
                
                if system_health.degraded_components:
                    response_data["degraded_components"] = [
                        {
                            "name": comp.name,
                            "message": comp.message,
                            "status": comp.status.value
                        }
                        for comp in system_health.degraded_components
                    ]
        
        # Add request metadata
        response_data["request_id"] = request_id
        response_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        # Log performance metrics
        perf_logger.log_api_call(
            endpoint="/health",
            method="GET",
            status_code=http_status,
            response_time_ms=response_data["response_time_ms"],
            request_size=0,
            response_size=len(str(response_data)),
            error=None if http_status == 200 else f"System status: {system_health.status.value}"
        )
        
        logger.info("Health check endpoint completed", extra={
            "request_id": request_id,
            "http_status": http_status,
            "system_status": system_health.status.value,
            "response_time_ms": response_data["response_time_ms"],
            "component_count": len(system_health.components),
            "healthy_components": system_health.summary.get("healthy_components", 0),
            "unhealthy_components": system_health.summary.get("unhealthy_components", 0)
        })
        
        return JSONResponse(
            content=response_data,
            status_code=http_status,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Health-Status": system_health.status.value,
                "X-Request-ID": request_id
            }
        )
        
    except Exception as e:
        # Health check system failure - return 500
        error_response_time = round((time.time() - start_time) * 1000, 2)
        
        logger.error("Health check endpoint failed", extra={
            "request_id": request_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "response_time_ms": error_response_time
        })
        
        # Log performance metrics for failure
        perf_logger.log_api_call(
            endpoint="/health",
            method="GET",
            status_code=500,
            response_time_ms=error_response_time,
            request_size=0,
            response_size=0,
            error=f"{type(e).__name__}: {str(e)}"
        )
        
        error_response = {
            "status": "error",
            "healthy": False,
            "message": "Health check system failure",
            "error": str(e),
            "timestamp": system_health.timestamp if 'system_health' in locals() else time.time(),
            "request_id": request_id,
            "response_time_ms": error_response_time
        }
        
        return JSONResponse(
            content=error_response,
            status_code=500,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "X-Health-Status": "error",
                "X-Request-ID": request_id
            }
        )


async def readiness_probe_endpoint(request: Request) -> JSONResponse:
    """
    Kubernetes-style readiness probe endpoint.
    
    This endpoint checks if the service is ready to receive traffic.
    Returns 200 only if all critical components are healthy.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSONResponse with readiness status
    """
    start_time = time.time()
    request_id = getattr(request.state, 'request_id', 'readiness_check')
    
    try:
        health_service = get_health_service()
        system_health = await health_service.get_health_status(include_details=False)
        
        # Readiness is stricter - only healthy systems are ready
        if system_health.status == HealthStatus.HEALTHY:
            response_data = {
                "ready": True,
                "status": "ready",
                "timestamp": system_health.timestamp,
                "request_id": request_id
            }
            http_status = 200
        else:
            response_data = {
                "ready": False,
                "status": "not_ready",
                "reason": f"System status: {system_health.status.value}",
                "timestamp": system_health.timestamp,
                "request_id": request_id
            }
            http_status = 503
        
        response_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        logger.debug("Readiness probe completed", extra={
            "request_id": request_id,
            "ready": response_data["ready"],
            "system_status": system_health.status.value,
            "response_time_ms": response_data["response_time_ms"]
        })
        
        return JSONResponse(
            content=response_data,
            status_code=http_status,
            headers={
                "Cache-Control": "no-cache",
                "X-Request-ID": request_id
            }
        )
        
    except Exception as e:
        error_response_time = round((time.time() - start_time) * 1000, 2)
        
        logger.error("Readiness probe failed", extra={
            "request_id": request_id,
            "error": str(e),
            "response_time_ms": error_response_time
        })
        
        return JSONResponse(
            content={
                "ready": False,
                "status": "error",
                "error": str(e),
                "request_id": request_id,
                "response_time_ms": error_response_time
            },
            status_code=500
        )


async def liveness_probe_endpoint(request: Request) -> JSONResponse:
    """
    Kubernetes-style liveness probe endpoint.
    
    This endpoint checks if the service is alive and should not be restarted.
    Returns 200 as long as the basic service is running.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSONResponse with liveness status
    """
    start_time = time.time()
    request_id = getattr(request.state, 'request_id', 'liveness_check')
    
    try:
        # Simple liveness check - just verify basic functionality
        health_service = get_health_service()
        
        # Basic checks - if we can create the service and get uptime, we're alive
        uptime = time.time() - health_service._start_time
        
        response_data = {
            "alive": True,
            "status": "alive",
            "uptime_seconds": uptime,
            "timestamp": time.time(),
            "request_id": request_id,
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }
        
        logger.debug("Liveness probe completed", extra={
            "request_id": request_id,
            "alive": True,
            "uptime_seconds": uptime,
            "response_time_ms": response_data["response_time_ms"]
        })
        
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers={
                "Cache-Control": "no-cache",
                "X-Request-ID": request_id
            }
        )
        
    except Exception as e:
        # Even if health service fails, as long as we can respond, we're "alive"
        error_response_time = round((time.time() - start_time) * 1000, 2)
        
        logger.warning("Liveness probe had issues but service is alive", extra={
            "request_id": request_id,
            "error": str(e),
            "response_time_ms": error_response_time
        })
        
        return JSONResponse(
            content={
                "alive": True,
                "status": "alive_with_issues",
                "issues": str(e),
                "request_id": request_id,
                "response_time_ms": error_response_time
            },
            status_code=200
        )


# Convenience functions for integration
async def simple_health_check() -> Dict[str, Any]:
    """
    Simple health check function that returns basic status.
    
    Returns:
        Dictionary with basic health information
    """
    try:
        health_service = get_health_service()
        system_health = await health_service.get_health_status(include_details=False)
        
        return {
            "healthy": system_health.is_healthy,
            "status": system_health.status.value,
            "uptime_seconds": system_health.uptime_seconds,
            "timestamp": system_health.timestamp
        }
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        return {
            "healthy": False,
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }