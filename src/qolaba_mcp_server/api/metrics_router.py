"""
FastAPI router for metrics endpoints.

This module provides HTTP endpoints for metrics export in Prometheus format,
metric summaries, and monitoring dashboard integration.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from fastapi import APIRouter, Response, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse, JSONResponse

from ..core.metrics import get_metrics_collector, MetricsCollector
from ..core.logging_config import get_module_logger, RequestContext
from ..health.health_check import get_health_service

logger = get_module_logger("api.metrics_router")

# Create metrics router
metrics_router = APIRouter(
    prefix="/metrics",
    tags=["monitoring", "metrics"],
    responses={
        500: {"description": "Internal server error"},
        503: {"description": "Service temporarily unavailable"}
    }
)


async def get_metrics_service() -> MetricsCollector:
    """Dependency to get metrics collector service."""
    return get_metrics_collector()


@metrics_router.get(
    "",
    response_class=PlainTextResponse,
    summary="Export Prometheus metrics",
    description="Export all collected metrics in Prometheus format for scraping",
    responses={
        200: {
            "description": "Metrics exported successfully",
            "content": {"text/plain": {"example": "# HELP qolaba_mcp_http_requests_total Total HTTP requests\n# TYPE qolaba_mcp_http_requests_total counter\nqolaba_mcp_http_requests_total 42"}}
        }
    }
)
async def export_prometheus_metrics(
    metrics_service: MetricsCollector = Depends(get_metrics_service),
    format: str = Query("prometheus", description="Export format (prometheus only supported currently)")
) -> Response:
    """
    Export metrics in Prometheus format.
    
    This endpoint is designed to be scraped by Prometheus server.
    Returns metrics in the standard Prometheus exposition format.
    """
    request_id = f"metrics_export_{hash(id(metrics_service))}"
    
    with RequestContext(request_id=request_id, operation="metrics_export") as ctx:
        logger.info("Exporting Prometheus metrics", extra={
            "request_id": ctx.request_id,
            "format": format
        })
        
        try:
            if format != "prometheus":
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported format: {format}. Only 'prometheus' is supported."
                )
            
            # Export metrics in Prometheus format
            prometheus_data = metrics_service.export_prometheus_metrics()
            
            # Record the metrics export operation
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics", "method": "GET", "status_code": "200"}
            )
            
            logger.info("Metrics exported successfully", extra={
                "request_id": ctx.request_id,
                "data_length": len(prometheus_data),
                "format": format
            })
            
            return PlainTextResponse(
                content=prometheus_data,
                headers={
                    "Content-Type": "text/plain; version=0.0.4; charset=utf-8",
                    "X-Request-ID": ctx.request_id,
                    "Cache-Control": "no-cache, no-store, must-revalidate"
                }
            )
            
        except Exception as e:
            logger.error("Failed to export metrics", extra={
                "request_id": ctx.request_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Record error metric
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics", "method": "GET", "status_code": "500"}
            )
            
            raise HTTPException(
                status_code=500,
                detail="Failed to export metrics. Please try again later."
            )


@metrics_router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Get metrics summary",
    description="Get detailed summary of all collected metrics for debugging and monitoring",
    responses={
        200: {
            "description": "Metrics summary retrieved successfully",
            "content": {"application/json": {
                "example": {
                    "total_metrics": 15,
                    "uptime_seconds": 3600.5,
                    "metrics_by_type": {"counter": 8, "gauge": 4, "histogram": 3},
                    "last_updated": "2025-09-13T22:00:00Z"
                }
            }}
        }
    }
)
async def get_metrics_summary(
    metrics_service: MetricsCollector = Depends(get_metrics_service),
    detailed: bool = Query(False, description="Include detailed metric information")
) -> Dict[str, Any]:
    """
    Get comprehensive metrics summary.
    
    Provides overview of all collected metrics including counts by type,
    uptime information, and optionally detailed metric values.
    """
    request_id = f"metrics_summary_{hash(id(metrics_service))}"
    
    with RequestContext(request_id=request_id, operation="metrics_summary") as ctx:
        logger.info("Generating metrics summary", extra={
            "request_id": ctx.request_id,
            "detailed": detailed
        })
        
        try:
            summary = metrics_service.get_metric_summary()
            
            # Filter detailed information if not requested
            if not detailed:
                summary.pop("metrics", None)
            
            # Add additional context
            summary["request_id"] = ctx.request_id
            summary["detailed"] = detailed
            
            # Record the summary request
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics/summary", "method": "GET", "status_code": "200"}
            )
            
            logger.info("Metrics summary generated", extra={
                "request_id": ctx.request_id,
                "metric_count": summary["total_metrics"],
                "detailed": detailed
            })
            
            return summary
            
        except Exception as e:
            logger.error("Failed to generate metrics summary", extra={
                "request_id": ctx.request_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics/summary", "method": "GET", "status_code": "500"}
            )
            
            raise HTTPException(
                status_code=500,
                detail="Failed to generate metrics summary. Please try again later."
            )


@metrics_router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Get metrics system health",
    description="Check the health and status of the metrics collection system",
    responses={
        200: {"description": "Metrics system is healthy"},
        503: {"description": "Metrics system is experiencing issues"}
    }
)
async def get_metrics_health(
    metrics_service: MetricsCollector = Depends(get_metrics_service)
) -> Dict[str, Any]:
    """
    Check metrics system health.
    
    Verifies that the metrics collection system is functioning properly
    and can collect and export metrics.
    """
    request_id = f"metrics_health_{hash(id(metrics_service))}"
    
    with RequestContext(request_id=request_id, operation="metrics_health") as ctx:
        logger.info("Checking metrics system health", extra={
            "request_id": ctx.request_id
        })
        
        try:
            # Test basic metrics functionality
            test_counter = "test_health_check_counter"
            metrics_service.increment_counter(test_counter, 1)
            
            # Get summary to verify system is responsive
            summary = metrics_service.get_metric_summary()
            
            health_status = {
                "status": "healthy",
                "request_id": ctx.request_id,
                "metrics_collector": {
                    "total_metrics": summary["total_metrics"],
                    "uptime_seconds": summary["uptime_seconds"],
                    "last_updated": summary["last_updated"]
                },
                "functionality_test": {
                    "counter_test": "passed",
                    "summary_test": "passed"
                },
                "timestamp": summary["last_updated"]
            }
            
            # Record successful health check
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics/health", "method": "GET", "status_code": "200"}
            )
            
            logger.info("Metrics system health check passed", extra={
                "request_id": ctx.request_id,
                "total_metrics": summary["total_metrics"]
            })
            
            return health_status
            
        except Exception as e:
            logger.error("Metrics system health check failed", extra={
                "request_id": ctx.request_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            try:
                metrics_service.increment_counter(
                    "qolaba_mcp_http_requests_total",
                    labels={"endpoint": "/metrics/health", "method": "GET", "status_code": "503"}
                )
            except:
                pass  # Don't fail if we can't even record the error
            
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "error": str(e),
                    "request_id": ctx.request_id,
                    "message": "Metrics system is experiencing issues"
                }
            )


@metrics_router.post(
    "/reset",
    response_model=Dict[str, Any],
    summary="Reset all metrics (development only)",
    description="Reset all collected metrics to zero. This should only be used in development environments.",
    responses={
        200: {"description": "Metrics reset successfully"},
        403: {"description": "Reset not allowed in production"}
    }
)
async def reset_metrics(
    metrics_service: MetricsCollector = Depends(get_metrics_service),
    confirm: bool = Query(False, description="Confirmation flag required to perform reset")
) -> Dict[str, Any]:
    """
    Reset all metrics to zero values.
    
    This endpoint is primarily for development and testing purposes.
    Production environments should typically not allow metric resets.
    """
    import os
    
    request_id = f"metrics_reset_{hash(id(metrics_service))}"
    
    with RequestContext(request_id=request_id, operation="metrics_reset") as ctx:
        logger.warning("Metrics reset requested", extra={
            "request_id": ctx.request_id,
            "confirm": confirm
        })
        
        # Check if we're in production environment
        is_production = os.getenv("FASTMCP_TEST_MODE") != "1"
        
        if is_production:
            logger.error("Metrics reset attempted in production", extra={
                "request_id": ctx.request_id
            })
            
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics/reset", "method": "POST", "status_code": "403"}
            )
            
            raise HTTPException(
                status_code=403,
                detail="Metric reset is not allowed in production environments"
            )
        
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Reset confirmation required. Set 'confirm=true' query parameter."
            )
        
        try:
            # Get metrics count before reset
            summary_before = metrics_service.get_metric_summary()
            
            # Perform reset
            metrics_service.reset_metrics()
            
            # Verify reset
            summary_after = metrics_service.get_metric_summary()
            
            result = {
                "status": "reset_successful",
                "request_id": ctx.request_id,
                "metrics_before_reset": summary_before["total_metrics"],
                "metrics_after_reset": summary_after["total_metrics"],
                "timestamp": summary_after["last_updated"]
            }
            
            # Record the reset operation (this will be the first metric after reset)
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics/reset", "method": "POST", "status_code": "200"}
            )
            
            logger.info("Metrics reset completed", extra={
                "request_id": ctx.request_id,
                "metrics_reset": summary_before["total_metrics"]
            })
            
            return result
            
        except Exception as e:
            logger.error("Failed to reset metrics", extra={
                "request_id": ctx.request_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            metrics_service.increment_counter(
                "qolaba_mcp_http_requests_total",
                labels={"endpoint": "/metrics/reset", "method": "POST", "status_code": "500"}
            )
            
            raise HTTPException(
                status_code=500,
                detail="Failed to reset metrics. Please try again later."
            )


# Add middleware to record HTTP requests to metrics endpoints
@metrics_router.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware to track metrics for metrics endpoints themselves."""
    import time
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record HTTP request metrics
        metrics_service = get_metrics_collector()
        metrics_service.record_http_request(
            endpoint=str(request.url.path),
            method=request.method,
            status_code=response.status_code,
            duration_seconds=duration
        )
        
        # Add response headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        # Record error
        metrics_service = get_metrics_collector()
        metrics_service.record_http_request(
            endpoint=str(request.url.path),
            method=request.method,
            status_code=500,
            duration_seconds=duration
        )
        
        raise e


# Health integration for metrics system
async def metrics_system_health_check() -> bool:
    """
    Health check function for metrics system integration.
    
    Returns:
        True if metrics system is healthy, False otherwise
    """
    try:
        metrics_service = get_metrics_collector()
        
        # Test basic functionality
        test_start = time.time()
        metrics_service.increment_counter("health_check_test", 1)
        summary = metrics_service.get_metric_summary()
        test_duration = time.time() - test_start
        
        # Record health check timing
        metrics_service.record_health_check(
            component="metrics_system",
            duration_seconds=test_duration,
            healthy=True
        )
        
        return True
        
    except Exception as e:
        logger.error("Metrics system health check failed", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        try:
            metrics_service = get_metrics_collector()
            metrics_service.record_health_check(
                component="metrics_system",
                duration_seconds=0.0,
                healthy=False
            )
        except:
            pass  # Don't fail if we can't record the failure
        
        return False