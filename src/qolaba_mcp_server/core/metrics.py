"""
Comprehensive metrics and performance monitoring system for Qolaba MCP Server.

This module provides Prometheus-compatible metrics collection, custom business metrics,
performance tracking, and monitoring dashboard preparation for production environments.
Features:
- Prometheus metrics integration with counter, gauge, histogram, and summary types
- Custom metrics for Qolaba API operations and business logic
- Performance tracking with response time analysis
- Resource utilization monitoring (CPU, memory, disk)
- Request rate and error rate tracking
- Dashboard-ready metric export formats
"""

from __future__ import annotations

import os
try:
    import psutil  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency in some environments
    psutil = None  # type: ignore[assignment]
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional, Union, Callable, ContextManager
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging_config import get_module_logger, get_performance_logger

logger = get_module_logger("core.metrics")
perf_logger = get_performance_logger("core.metrics")


class MetricType(str, Enum):
    """Supported metric types for monitoring system."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricLabels:
    """Standard labels for metrics categorization."""
    
    operation: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[str] = None
    error_type: Optional[str] = None
    model: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Convert labels to dictionary, filtering None values."""
        return {k: str(v) for k, v in self.__dict__.items() if v is not None}


@dataclass
class Metric:
    """Individual metric with metadata and tracking capabilities."""
    
    name: str
    metric_type: MetricType
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: Union[int, float] = 0
    samples: List[float] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_value(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None) -> None:
        """Update metric value and timestamp."""
        if labels:
            self.labels.update(labels)
        
        if self.metric_type == MetricType.COUNTER:
            self.value += value
        elif self.metric_type == MetricType.GAUGE:
            self.value = value
        elif self.metric_type in [MetricType.HISTOGRAM, MetricType.SUMMARY]:
            self.samples.append(float(value))
            self.value = sum(self.samples) / len(self.samples) if self.samples else 0
        
        self.updated_at = datetime.now(timezone.utc)
    
    def get_prometheus_format(self) -> str:
        """Export metric in Prometheus format."""
        label_str = ""
        if self.labels:
            label_pairs = [f'{k}="{v}"' for k, v in self.labels.items()]
            label_str = "{" + ",".join(label_pairs) + "}"
        
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} {self.metric_type.value}",
            f"{self.name}{label_str} {self.value}"
        ]
        
        # Add additional data for histograms and summaries
        if self.metric_type == MetricType.HISTOGRAM and self.samples:
            # Add histogram buckets
            buckets = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
            for bucket in buckets:
                count = sum(1 for s in self.samples if s <= bucket)
                lines.append(f"{self.name}_bucket{{le=\"{bucket}\"{label_str[1:-1] and ',' + label_str[1:-1] or ''}}} {count}")
            
            lines.append(f"{self.name}_sum{label_str} {sum(self.samples)}")
            lines.append(f"{self.name}_count{label_str} {len(self.samples)}")
        
        elif self.metric_type == MetricType.SUMMARY and self.samples:
            # Add summary quantiles
            sorted_samples = sorted(self.samples)
            quantiles = [0.5, 0.9, 0.95, 0.99]
            for quantile in quantiles:
                index = int(len(sorted_samples) * quantile)
                if index < len(sorted_samples):
                    value = sorted_samples[index]
                    lines.append(f"{self.name}{{quantile=\"{quantile}\"{label_str[1:-1] and ',' + label_str[1:-1] or ''}}} {value}")
            
            lines.append(f"{self.name}_sum{label_str} {sum(self.samples)}")
            lines.append(f"{self.name}_count{label_str} {len(self.samples)}")
        
        return "\n".join(lines)


class MetricsCollector:
    """
    Central metrics collection service for Qolaba MCP Server.
    
    Provides thread-safe metric collection, Prometheus export capabilities,
    and comprehensive monitoring for all system components.
    """
    
    _instance: Optional['MetricsCollector'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'MetricsCollector':
        """Singleton pattern for global metrics collector."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._metrics: Dict[str, Metric] = {}
            self._metric_lock = Lock()
            self._start_time = time.time()
            self._request_count = 0
            self._error_count = 0
            
            # Initialize standard metrics
            self._initialize_standard_metrics()
            self._initialized = True
    
    def _initialize_standard_metrics(self):
        """Initialize standard system and application metrics."""
        
        # HTTP request metrics
        self.register_metric(
            "qolaba_mcp_http_requests_total",
            MetricType.COUNTER,
            "Total number of HTTP requests processed"
        )
        
        self.register_metric(
            "qolaba_mcp_http_request_duration_seconds",
            MetricType.HISTOGRAM,
            "HTTP request duration in seconds"
        )
        
        # API client metrics
        self.register_metric(
            "qolaba_api_requests_total",
            MetricType.COUNTER,
            "Total number of requests to Qolaba API"
        )
        
        self.register_metric(
            "qolaba_api_request_duration_seconds",
            MetricType.HISTOGRAM,
            "Duration of Qolaba API requests in seconds"
        )
        
        self.register_metric(
            "qolaba_api_errors_total",
            MetricType.COUNTER,
            "Total number of Qolaba API errors"
        )
        
        # Business logic metrics
        self.register_metric(
            "qolaba_mcp_operations_total",
            MetricType.COUNTER,
            "Total number of MCP operations processed"
        )
        
        self.register_metric(
            "qolaba_mcp_operation_duration_seconds",
            MetricType.HISTOGRAM,
            "Duration of MCP operations in seconds"
        )
        
        # System resource metrics
        self.register_metric(
            "qolaba_mcp_memory_usage_bytes",
            MetricType.GAUGE,
            "Current memory usage in bytes"
        )
        
        self.register_metric(
            "qolaba_mcp_cpu_usage_percent",
            MetricType.GAUGE,
            "Current CPU usage percentage"
        )
        
        # Health check metrics
        self.register_metric(
            "qolaba_mcp_health_check_duration_seconds",
            MetricType.HISTOGRAM,
            "Duration of health check operations"
        )
        
        self.register_metric(
            "qolaba_mcp_component_health_status",
            MetricType.GAUGE,
            "Health status of system components (1=healthy, 0=unhealthy)"
        )
        
        logger.info("Standard metrics initialized", extra={
            "metric_count": len(self._metrics),
            "metric_names": list(self._metrics.keys())
        })
    
    def register_metric(self, 
                       name: str, 
                       metric_type: MetricType, 
                       description: str,
                       labels: Optional[Dict[str, str]] = None) -> Metric:
        """
        Register a new metric for collection.
        
        Args:
            name: Unique metric name (should follow Prometheus naming conventions)
            metric_type: Type of metric (counter, gauge, histogram, summary)
            description: Human-readable description
            labels: Optional default labels
            
        Returns:
            Created metric instance
        """
        with self._metric_lock:
            if name in self._metrics:
                logger.warning(f"Metric {name} already registered, returning existing")
                return self._metrics[name]
            
            metric = Metric(
                name=name,
                metric_type=metric_type,
                description=description,
                labels=labels or {}
            )
            
            self._metrics[name] = metric
            
            logger.debug(f"Registered metric: {name}", extra={
                "metric_type": metric_type.value,
                "description": description,
                "labels": labels
            })
            
            return metric
    
    def increment_counter(self, 
                         name: str, 
                         value: Union[int, float] = 1,
                         labels: Optional[Union[Dict[str, str], MetricLabels]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by (default: 1)
            labels: Optional labels for this measurement
        """
        with self._metric_lock:
            if name not in self._metrics:
                logger.warning(f"Counter metric {name} not found, creating automatically")
                self.register_metric(name, MetricType.COUNTER, f"Auto-created counter: {name}")
            
            metric = self._metrics[name]
            if metric.metric_type != MetricType.COUNTER:
                raise ValueError(f"Metric {name} is not a counter")
            
            label_dict = labels.to_dict() if isinstance(labels, MetricLabels) else (labels or {})
            metric.update_value(value, label_dict)
    
    def set_gauge(self, 
                  name: str, 
                  value: Union[int, float],
                  labels: Optional[Union[Dict[str, str], MetricLabels]] = None) -> None:
        """
        Set gauge metric value.
        
        Args:
            name: Metric name
            value: Current value
            labels: Optional labels for this measurement
        """
        with self._metric_lock:
            if name not in self._metrics:
                logger.warning(f"Gauge metric {name} not found, creating automatically")
                self.register_metric(name, MetricType.GAUGE, f"Auto-created gauge: {name}")
            
            metric = self._metrics[name]
            if metric.metric_type != MetricType.GAUGE:
                raise ValueError(f"Metric {name} is not a gauge")
            
            label_dict = labels.to_dict() if isinstance(labels, MetricLabels) else (labels or {})
            metric.update_value(value, label_dict)
    
    def observe_histogram(self, 
                         name: str, 
                         value: float,
                         labels: Optional[Union[Dict[str, str], MetricLabels]] = None) -> None:
        """
        Record observation for histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels for this measurement
        """
        with self._metric_lock:
            if name not in self._metrics:
                logger.warning(f"Histogram metric {name} not found, creating automatically")
                self.register_metric(name, MetricType.HISTOGRAM, f"Auto-created histogram: {name}")
            
            metric = self._metrics[name]
            if metric.metric_type != MetricType.HISTOGRAM:
                raise ValueError(f"Metric {name} is not a histogram")
            
            label_dict = labels.to_dict() if isinstance(labels, MetricLabels) else (labels or {})
            metric.update_value(value, label_dict)
    
    def record_api_request(self, 
                          endpoint: str,
                          method: str,
                          status_code: int,
                          duration_seconds: float,
                          error_type: Optional[str] = None) -> None:
        """
        Record Qolaba API request metrics.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            duration_seconds: Request duration
            error_type: Optional error type if request failed
        """
        labels = MetricLabels(
            endpoint=endpoint,
            method=method,
            status_code=str(status_code),
            error_type=error_type
        )
        
        # Increment total requests
        self.increment_counter("qolaba_api_requests_total", labels=labels)
        
        # Record duration
        self.observe_histogram("qolaba_api_request_duration_seconds", duration_seconds, labels=labels)
        
        # Count errors
        if status_code >= 400 or error_type:
            self.increment_counter("qolaba_api_errors_total", labels=labels)
        
        perf_logger.log_api_call(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=duration_seconds * 1000,
            error=error_type
        )
    
    def record_mcp_operation(self,
                           operation: str,
                           duration_seconds: float,
                           success: bool = True,
                           model: Optional[str] = None,
                           user_id: Optional[str] = None) -> None:
        """
        Record MCP operation metrics.
        
        Args:
            operation: Operation name (e.g., 'text_to_image', 'chat')
            duration_seconds: Operation duration
            success: Whether operation succeeded
            model: Optional model used
            user_id: Optional user identifier
        """
        labels = MetricLabels(
            operation=operation,
            model=model,
            user_id=user_id,
            status_code="200" if success else "500"
        )
        
        # Increment total operations
        self.increment_counter("qolaba_mcp_operations_total", labels=labels)
        
        # Record duration
        self.observe_histogram("qolaba_mcp_operation_duration_seconds", duration_seconds, labels=labels)
        
        perf_logger.log_operation_timing(
            operation=operation,
            duration_ms=duration_seconds * 1000,
            success=success,
            metadata={"model": model, "user_id": user_id}
        )
    
    def record_http_request(self,
                          endpoint: str,
                          method: str,
                          status_code: int,
                          duration_seconds: float) -> None:
        """
        Record HTTP request metrics for MCP server.
        
        Args:
            endpoint: Request endpoint
            method: HTTP method
            status_code: Response status code
            duration_seconds: Request duration
        """
        labels = MetricLabels(
            endpoint=endpoint,
            method=method,
            status_code=str(status_code)
        )
        
        self.increment_counter("qolaba_mcp_http_requests_total", labels=labels)
        self.observe_histogram("qolaba_mcp_http_request_duration_seconds", duration_seconds, labels=labels)
    
    def update_system_metrics(self) -> None:
        """Update system resource metrics."""
        try:
            if psutil is None:
                logger.debug("psutil not available; skipping system metrics update")
                return

            # Memory usage
            memory_info = psutil.virtual_memory()
            self.set_gauge("qolaba_mcp_memory_usage_bytes", memory_info.used)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.set_gauge("qolaba_mcp_cpu_usage_percent", cpu_percent)

            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss
            process_cpu = process.cpu_percent()

            self.set_gauge("qolaba_mcp_process_memory_bytes", process_memory)
            self.set_gauge("qolaba_mcp_process_cpu_percent", process_cpu)

        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")
    
    def record_health_check(self, 
                           component: str, 
                           duration_seconds: float,
                           healthy: bool) -> None:
        """
        Record health check metrics.
        
        Args:
            component: Component name
            duration_seconds: Health check duration
            healthy: Whether component is healthy
        """
        labels = MetricLabels(operation=component)
        
        self.observe_histogram("qolaba_mcp_health_check_duration_seconds", duration_seconds, labels=labels)
        self.set_gauge("qolaba_mcp_component_health_status", 1 if healthy else 0, labels=labels)
    
    @contextmanager
    def timer(self, metric_name: str, labels: Optional[Union[Dict[str, str], MetricLabels]] = None) -> ContextManager[None]:
        """
        Context manager for timing operations.
        
        Args:
            metric_name: Name of histogram metric to record timing
            labels: Optional labels
            
        Usage:
            with metrics.timer("operation_duration_seconds"):
                # Operation to time
                pass
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.observe_histogram(metric_name, duration, labels)
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics for debugging and monitoring.
        
        Returns:
            Dictionary containing metric summary information
        """
        with self._metric_lock:
            summary = {
                "total_metrics": len(self._metrics),
                "uptime_seconds": time.time() - self._start_time,
                "metrics_by_type": {},
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "metrics": {}
            }
            
            # Group by type
            for metric in self._metrics.values():
                metric_type = metric.metric_type.value
                if metric_type not in summary["metrics_by_type"]:
                    summary["metrics_by_type"][metric_type] = 0
                summary["metrics_by_type"][metric_type] += 1
                
                # Add metric details
                summary["metrics"][metric.name] = {
                    "type": metric_type,
                    "value": metric.value,
                    "description": metric.description,
                    "labels": metric.labels,
                    "sample_count": len(metric.samples) if metric.samples else 0,
                    "updated_at": metric.updated_at.isoformat()
                }
            
            return summary
    
    def export_prometheus_metrics(self) -> str:
        """
        Export all metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        with self._metric_lock:
            # Update system metrics before export
            self.update_system_metrics()
            
            metric_lines = []
            
            # Add server info
            metric_lines.extend([
                f"# Qolaba MCP Server Metrics Export",
                f"# Generated at {datetime.now(timezone.utc).isoformat()}",
                f"# Total metrics: {len(self._metrics)}",
                ""
            ])
            
            # Export each metric
            for metric in sorted(self._metrics.values(), key=lambda m: m.name):
                metric_lines.append(metric.get_prometheus_format())
                metric_lines.append("")  # Empty line between metrics
            
            return "\n".join(metric_lines)
    
    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._metric_lock:
            for metric in self._metrics.values():
                metric.value = 0
                metric.samples.clear()
                metric.updated_at = datetime.now(timezone.utc)
        
        logger.info("All metrics reset")


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Convenience functions
def increment_counter(name: str, 
                     value: Union[int, float] = 1,
                     labels: Optional[Union[Dict[str, str], MetricLabels]] = None):
    """Increment counter metric via global collector."""
    metrics_collector.increment_counter(name, value, labels)


def set_gauge(name: str, 
              value: Union[int, float],
              labels: Optional[Union[Dict[str, str], MetricLabels]] = None):
    """Set gauge metric via global collector."""
    metrics_collector.set_gauge(name, value, labels)


def observe_histogram(name: str, 
                     value: float,
                     labels: Optional[Union[Dict[str, str], MetricLabels]] = None):
    """Record histogram observation via global collector."""
    metrics_collector.observe_histogram(name, value, labels)


def timer(metric_name: str, labels: Optional[Union[Dict[str, str], MetricLabels]] = None):
    """Timer context manager via global collector."""
    return metrics_collector.timer(metric_name, labels)


def record_api_request(endpoint: str, method: str, status_code: int, duration_seconds: float, error_type: Optional[str] = None):
    """Record API request metrics via global collector."""
    metrics_collector.record_api_request(endpoint, method, status_code, duration_seconds, error_type)


def record_mcp_operation(operation: str, duration_seconds: float, success: bool = True, model: Optional[str] = None, user_id: Optional[str] = None):
    """Record MCP operation metrics via global collector."""
    metrics_collector.record_mcp_operation(operation, duration_seconds, success, model, user_id)


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    return metrics_collector