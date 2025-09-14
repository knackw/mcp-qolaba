"""
Comprehensive health check service for Qolaba MCP Server.

This module implements a robust health checking system that monitors various
system components and provides detailed status information for container
orchestration, load balancers, and monitoring systems.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from pydantic import BaseModel, Field

from ..core.logging_config import get_module_logger, get_performance_logger
from ..config.settings import get_settings
from ..core.metrics import get_metrics_collector


logger = get_module_logger("health.health_check")
perf_logger = get_performance_logger("health.health_check")
metrics_collector = get_metrics_collector()


class HealthStatus(str, Enum):
    """Health status enumeration for system components."""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Service is running but not optimal
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth(BaseModel):
    """Health status for an individual system component."""
    
    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Component health status")
    message: Optional[str] = Field(None, description="Status message or error details")
    response_time_ms: Optional[float] = Field(None, description="Component response time in milliseconds")
    last_checked: str = Field(..., description="ISO timestamp of last health check")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional component-specific data")
    
    @classmethod
    def create_healthy(cls, name: str, response_time_ms: float = None, 
                      message: str = "Component is healthy", 
                      metadata: Dict[str, Any] = None) -> ComponentHealth:
        """Create a healthy component status."""
        return cls(
            name=name,
            status=HealthStatus.HEALTHY,
            message=message,
            response_time_ms=response_time_ms,
            last_checked=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        )
    
    @classmethod
    def create_unhealthy(cls, name: str, message: str, 
                        response_time_ms: float = None,
                        metadata: Dict[str, Any] = None) -> ComponentHealth:
        """Create an unhealthy component status."""
        return cls(
            name=name,
            status=HealthStatus.UNHEALTHY,
            message=message,
            response_time_ms=response_time_ms,
            last_checked=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        )
    
    @classmethod
    def create_degraded(cls, name: str, message: str,
                       response_time_ms: float = None,
                       metadata: Dict[str, Any] = None) -> ComponentHealth:
        """Create a degraded component status."""
        return cls(
            name=name,
            status=HealthStatus.DEGRADED,
            message=message,
            response_time_ms=response_time_ms,
            last_checked=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        )


class SystemHealth(BaseModel):
    """Overall system health status."""
    
    status: HealthStatus = Field(..., description="Overall system health status")
    timestamp: str = Field(..., description="ISO timestamp of health check")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    version: str = Field(..., description="Application version")
    components: List[ComponentHealth] = Field(..., description="Individual component health statuses")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Health check summary statistics")
    
    @property
    def is_healthy(self) -> bool:
        """Check if system is considered healthy."""
        return self.status == HealthStatus.HEALTHY
    
    @property
    def unhealthy_components(self) -> List[ComponentHealth]:
        """Get list of unhealthy components."""
        return [c for c in self.components if c.status == HealthStatus.UNHEALTHY]
    
    @property
    def degraded_components(self) -> List[ComponentHealth]:
        """Get list of degraded components."""
        return [c for c in self.components if c.status == HealthStatus.DEGRADED]


# Type alias for health check functions
HealthCheckFunction = Callable[[], Awaitable[ComponentHealth]]


class HealthCheckService:
    """
    Comprehensive health check service for system monitoring.
    
    This service provides detailed health status information about various
    system components including API connectivity, database status, and
    service dependencies.
    """
    
    def __init__(self):
        """Initialize the health check service."""
        self.settings = get_settings()
        self._start_time = time.time()
        self._version = "1.0.0"  # Should be dynamic in real implementation
        
        # Registry of health check functions
        self._health_checks: Dict[str, HealthCheckFunction] = {}
        
        # Initialize built-in health checks
        self._register_builtin_checks()
        
        logger.info("Health check service initialized", extra={
            "start_time": self._start_time,
            "version": self._version,
            "registered_checks": list(self._health_checks.keys())
        })
    
    def register_health_check(self, name: str, check_func: HealthCheckFunction) -> None:
        """
        Register a custom health check function.
        
        Args:
            name: Unique name for the health check
            check_func: Async function that returns ComponentHealth
        """
        if name in self._health_checks:
            logger.warning(f"Overriding existing health check: {name}")
        
        self._health_checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def _register_builtin_checks(self) -> None:
        """Register built-in health checks."""
        self._health_checks.update({
            "api_connectivity": self._check_api_connectivity,
            "configuration": self._check_configuration,
            "memory_usage": self._check_memory_usage,
            "disk_space": self._check_disk_space,
            "logging_system": self._check_logging_system
        })
    
    async def get_health_status(self, include_details: bool = True) -> SystemHealth:
        """
        Get comprehensive system health status.
        
        Args:
            include_details: Whether to include detailed component information
            
        Returns:
            SystemHealth object with current system status
        """
        start_time = time.time()
        
        logger.info("Starting system health check", extra={
            "include_details": include_details,
            "registered_checks": len(self._health_checks)
        })
        
        # Run all health checks concurrently
        check_tasks = []
        for name, check_func in self._health_checks.items():
            task = asyncio.create_task(self._run_single_check(name, check_func))
            check_tasks.append(task)
        
        # Wait for all checks to complete
        component_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        components = []
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        
        for result in component_results:
            if isinstance(result, ComponentHealth):
                components.append(result)
                if result.status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif result.status == HealthStatus.DEGRADED:
                    degraded_count += 1
                elif result.status == HealthStatus.UNHEALTHY:
                    unhealthy_count += 1
            else:
                # Handle exceptions from health checks
                logger.error(f"Health check failed with exception: {result}")
                unhealthy_count += 1
        
        # Determine overall system health
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Calculate uptime
        uptime_seconds = time.time() - self._start_time
        total_check_time = (time.time() - start_time) * 1000
        
        # Create summary
        summary = {
            "total_components": len(components),
            "healthy_components": healthy_count,
            "degraded_components": degraded_count,
            "unhealthy_components": unhealthy_count,
            "health_check_duration_ms": total_check_time
        }
        
        system_health = SystemHealth(
            status=overall_status,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=uptime_seconds,
            version=self._version,
            components=components if include_details else [],
            summary=summary
        )
        
        # Log performance metrics
        perf_logger.log_operation_timing(
            operation="system_health_check",
            duration_ms=total_check_time,
            success=overall_status != HealthStatus.UNHEALTHY,
            metadata={
                "component_count": len(components),
                "overall_status": overall_status.value,
                "healthy_count": healthy_count,
                "degraded_count": degraded_count,
                "unhealthy_count": unhealthy_count
            }
        )
        
        # Record metrics for monitoring dashboard
        metrics_collector.record_health_check(
            component="system_health_check",
            duration_seconds=total_check_time / 1000.0,
            healthy=overall_status != HealthStatus.UNHEALTHY
        )
        
        # Record individual component health status as gauge metrics
        for component in components:
            health_value = 1 if component.status == HealthStatus.HEALTHY else 0
            if component.status == HealthStatus.DEGRADED:
                health_value = 0.5  # Partially healthy
            
            metrics_collector.set_gauge(
                "qolaba_mcp_component_health_status",
                health_value,
                labels={"component": component.name}
            )
        
        logger.info("System health check completed", extra={
            "overall_status": overall_status.value,
            "duration_ms": total_check_time,
            "component_count": len(components),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count
        })
        
        return system_health
    
    async def _run_single_check(self, name: str, check_func: HealthCheckFunction) -> ComponentHealth:
        """
        Run a single health check with error handling.
        
        Args:
            name: Name of the health check
            check_func: Health check function
            
        Returns:
            ComponentHealth result
        """
        try:
            start_time = time.time()
            result = await check_func()
            duration_ms = (time.time() - start_time) * 1000
            
            # Update response time if not set
            if result.response_time_ms is None:
                result.response_time_ms = duration_ms
                
            logger.debug(f"Health check '{name}' completed", extra={
                "status": result.status.value,
                "duration_ms": duration_ms,
                "message": result.message
            })
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check '{name}' failed", extra={
                "error": str(e),
                "duration_ms": duration_ms,
                "exception_type": type(e).__name__
            })
            
            return ComponentHealth.create_unhealthy(
                name=name,
                message=f"Health check failed: {str(e)}",
                response_time_ms=duration_ms,
                metadata={"exception_type": type(e).__name__}
            )
    
    async def _check_api_connectivity(self) -> ComponentHealth:
        """Check Qolaba API connectivity."""
        try:
            from ..api.client import QolabaHTTPClient
            
            async with QolabaHTTPClient(self.settings) as client:
                start_time = time.time()
                
                # Try a simple GET request to check connectivity
                # Use a lightweight endpoint if available, otherwise use base URL
                try:
                    response = await client.get("health")  # Assuming API has health endpoint
                except Exception:
                    # If no health endpoint, try base API call
                    response = await client.get("")
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return ComponentHealth.create_healthy(
                        name="api_connectivity",
                        response_time_ms=response_time,
                        message="API is reachable",
                        metadata={
                            "api_base_url": str(self.settings.api_base_url),
                            "status_code": response.status_code
                        }
                    )
                else:
                    return ComponentHealth.create_degraded(
                        name="api_connectivity",
                        response_time_ms=response_time,
                        message=f"API responded with status {response.status_code}",
                        metadata={
                            "api_base_url": str(self.settings.api_base_url),
                            "status_code": response.status_code
                        }
                    )
                    
        except Exception as e:
            return ComponentHealth.create_unhealthy(
                name="api_connectivity",
                message=f"API connectivity check failed: {str(e)}",
                metadata={
                    "api_base_url": str(self.settings.api_base_url),
                    "error_type": type(e).__name__
                }
            )
    
    async def _check_configuration(self) -> ComponentHealth:
        """Check configuration validity."""
        try:
            issues = []
            
            # Check required configuration
            if not self.settings.api_key or self.settings.api_key.get_secret_value() == "":
                issues.append("API key is not configured")
            
            if not self.settings.api_base_url:
                issues.append("API base URL is not configured")
            
            if self.settings.request_timeout <= 0:
                issues.append("Invalid request timeout configuration")
            
            if issues:
                return ComponentHealth.create_unhealthy(
                    name="configuration",
                    message=f"Configuration issues: {'; '.join(issues)}",
                    metadata={"issues": issues, "issues_count": len(issues)}
                )
            else:
                return ComponentHealth.create_healthy(
                    name="configuration",
                    message="Configuration is valid",
                    metadata={
                        "auth_method": self.settings.auth_method,
                        "timeout": self.settings.request_timeout,
                        "ssl_verify": self.settings.verify_ssl
                    }
                )
                
        except Exception as e:
            return ComponentHealth.create_unhealthy(
                name="configuration",
                message=f"Configuration check failed: {str(e)}"
            )
    
    async def _check_memory_usage(self) -> ComponentHealth:
        """Check system memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_usage_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if memory_usage_percent > 90:
                return ComponentHealth.create_unhealthy(
                    name="memory_usage",
                    message=f"High memory usage: {memory_usage_percent:.1f}%",
                    metadata={
                        "usage_percent": memory_usage_percent,
                        "available_gb": round(available_gb, 2),
                        "total_gb": round(memory.total / (1024**3), 2)
                    }
                )
            elif memory_usage_percent > 75:
                return ComponentHealth.create_degraded(
                    name="memory_usage",
                    message=f"Elevated memory usage: {memory_usage_percent:.1f}%",
                    metadata={
                        "usage_percent": memory_usage_percent,
                        "available_gb": round(available_gb, 2),
                        "total_gb": round(memory.total / (1024**3), 2)
                    }
                )
            else:
                return ComponentHealth.create_healthy(
                    name="memory_usage",
                    message=f"Memory usage normal: {memory_usage_percent:.1f}%",
                    metadata={
                        "usage_percent": memory_usage_percent,
                        "available_gb": round(available_gb, 2),
                        "total_gb": round(memory.total / (1024**3), 2)
                    }
                )
                
        except ImportError:
            return ComponentHealth.create_degraded(
                name="memory_usage",
                message="psutil not available for memory monitoring"
            )
        except Exception as e:
            return ComponentHealth.create_unhealthy(
                name="memory_usage",
                message=f"Memory check failed: {str(e)}"
            )
    
    async def _check_disk_space(self) -> ComponentHealth:
        """Check available disk space."""
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            available_gb = disk.free / (1024**3)
            
            if usage_percent > 90:
                return ComponentHealth.create_unhealthy(
                    name="disk_space",
                    message=f"Low disk space: {usage_percent:.1f}% used",
                    metadata={
                        "usage_percent": round(usage_percent, 1),
                        "available_gb": round(available_gb, 2),
                        "total_gb": round(disk.total / (1024**3), 2)
                    }
                )
            elif usage_percent > 80:
                return ComponentHealth.create_degraded(
                    name="disk_space",
                    message=f"Disk space getting low: {usage_percent:.1f}% used",
                    metadata={
                        "usage_percent": round(usage_percent, 1),
                        "available_gb": round(available_gb, 2),
                        "total_gb": round(disk.total / (1024**3), 2)
                    }
                )
            else:
                return ComponentHealth.create_healthy(
                    name="disk_space",
                    message=f"Disk space sufficient: {usage_percent:.1f}% used",
                    metadata={
                        "usage_percent": round(usage_percent, 1),
                        "available_gb": round(available_gb, 2),
                        "total_gb": round(disk.total / (1024**3), 2)
                    }
                )
                
        except ImportError:
            return ComponentHealth.create_degraded(
                name="disk_space",
                message="psutil not available for disk monitoring"
            )
        except Exception as e:
            return ComponentHealth.create_unhealthy(
                name="disk_space",
                message=f"Disk space check failed: {str(e)}"
            )
    
    async def _check_logging_system(self) -> ComponentHealth:
        """Check logging system functionality."""
        try:
            # Test that we can create log entries
            test_logger = get_module_logger("health.test")
            test_logger.info("Health check logging test")
            
            return ComponentHealth.create_healthy(
                name="logging_system",
                message="Logging system operational",
                metadata={"test_completed": True}
            )
            
        except Exception as e:
            return ComponentHealth.create_unhealthy(
                name="logging_system",
                message=f"Logging system check failed: {str(e)}"
            )


# Singleton instance
_health_service: Optional[HealthCheckService] = None


def get_health_service() -> HealthCheckService:
    """
    Get the singleton health check service instance.
    
    Returns:
        HealthCheckService instance
    """
    global _health_service
    if _health_service is None:
        _health_service = HealthCheckService()
    return _health_service