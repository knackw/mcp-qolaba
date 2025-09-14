"""
Comprehensive unit tests for health check system.

This module tests all health check components including the service,
endpoints, routes, and integration functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import time

from qolaba_mcp_server.health.health_check import (
    HealthCheckService,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    get_health_service
)
from qolaba_mcp_server.health.endpoints import (
    health_check_endpoint,
    readiness_probe_endpoint,
    liveness_probe_endpoint,
    simple_health_check
)


class TestHealthStatus:
    """Test HealthStatus enumeration."""
    
    def test_health_status_values(self):
        """Test health status enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"
    
    def test_health_status_membership(self):
        """Test health status membership testing."""
        assert HealthStatus.HEALTHY in HealthStatus
        assert "invalid_status" not in [status.value for status in HealthStatus]


class TestComponentHealth:
    """Test ComponentHealth model and factory methods."""
    
    def test_component_health_creation(self):
        """Test creating ComponentHealth instances."""
        health = ComponentHealth(
            name="test_component",
            status=HealthStatus.HEALTHY,
            message="All good",
            response_time_ms=15.5,
            last_checked=datetime.now(timezone.utc).isoformat(),
            metadata={"version": "1.0"}
        )
        
        assert health.name == "test_component"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "All good"
        assert health.response_time_ms == 15.5
        assert health.metadata["version"] == "1.0"
    
    def test_create_healthy_factory(self):
        """Test create_healthy factory method."""
        health = ComponentHealth.create_healthy(
            name="api",
            response_time_ms=10.0,
            message="API is working",
            metadata={"url": "https://api.test"}
        )
        
        assert health.name == "api"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "API is working"
        assert health.response_time_ms == 10.0
        assert health.metadata["url"] == "https://api.test"
        assert health.last_checked is not None
    
    def test_create_unhealthy_factory(self):
        """Test create_unhealthy factory method."""
        health = ComponentHealth.create_unhealthy(
            name="database",
            message="Connection failed",
            response_time_ms=5000.0,
            metadata={"error": "timeout"}
        )
        
        assert health.name == "database"
        assert health.status == HealthStatus.UNHEALTHY
        assert health.message == "Connection failed"
        assert health.response_time_ms == 5000.0
        assert health.metadata["error"] == "timeout"
    
    def test_create_degraded_factory(self):
        """Test create_degraded factory method."""
        health = ComponentHealth.create_degraded(
            name="cache",
            message="High latency",
            response_time_ms=500.0
        )
        
        assert health.name == "cache"
        assert health.status == HealthStatus.DEGRADED
        assert health.message == "High latency"
        assert health.response_time_ms == 500.0


class TestSystemHealth:
    """Test SystemHealth model and properties."""
    
    def test_system_health_creation(self):
        """Test creating SystemHealth instances."""
        components = [
            ComponentHealth.create_healthy("api"),
            ComponentHealth.create_degraded("cache", "Slow response")
        ]
        
        system_health = SystemHealth(
            status=HealthStatus.DEGRADED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=3600.0,
            version="1.0.0",
            components=components,
            summary={"total": 2, "healthy": 1, "degraded": 1}
        )
        
        assert system_health.status == HealthStatus.DEGRADED
        assert system_health.uptime_seconds == 3600.0
        assert system_health.version == "1.0.0"
        assert len(system_health.components) == 2
    
    def test_is_healthy_property(self):
        """Test is_healthy property."""
        healthy_system = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=100.0,
            version="1.0.0",
            components=[]
        )
        
        unhealthy_system = SystemHealth(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=100.0,
            version="1.0.0",
            components=[]
        )
        
        assert healthy_system.is_healthy is True
        assert unhealthy_system.is_healthy is False
    
    def test_unhealthy_components_property(self):
        """Test unhealthy_components property."""
        components = [
            ComponentHealth.create_healthy("api"),
            ComponentHealth.create_unhealthy("db", "Connection failed"),
            ComponentHealth.create_degraded("cache", "Slow"),
            ComponentHealth.create_unhealthy("storage", "Disk full")
        ]
        
        system_health = SystemHealth(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=100.0,
            version="1.0.0",
            components=components
        )
        
        unhealthy = system_health.unhealthy_components
        assert len(unhealthy) == 2
        assert unhealthy[0].name == "db"
        assert unhealthy[1].name == "storage"
    
    def test_degraded_components_property(self):
        """Test degraded_components property."""
        components = [
            ComponentHealth.create_healthy("api"),
            ComponentHealth.create_degraded("cache", "Slow"),
            ComponentHealth.create_unhealthy("db", "Failed")
        ]
        
        system_health = SystemHealth(
            status=HealthStatus.DEGRADED,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=100.0,
            version="1.0.0",
            components=components
        )
        
        degraded = system_health.degraded_components
        assert len(degraded) == 1
        assert degraded[0].name == "cache"


class TestHealthCheckService:
    """Test HealthCheckService functionality."""
    
    @pytest.fixture
    def health_service(self):
        """Create health service for testing."""
        with patch('qolaba_mcp_server.health.health_check.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            mock_settings.return_value.api_key.get_secret_value.return_value = "test_key"
            mock_settings.return_value.api_base_url = "https://api.test"
            mock_settings.return_value.request_timeout = 30.0
            mock_settings.return_value.verify_ssl = True
            
            return HealthCheckService()
    
    def test_health_service_initialization(self, health_service):
        """Test health service initialization."""
        assert health_service is not None
        assert health_service._start_time is not None
        assert health_service._version == "1.0.0"
        assert len(health_service._health_checks) == 5  # Built-in checks
    
    def test_register_custom_health_check(self, health_service):
        """Test registering custom health checks."""
        async def custom_check():
            return ComponentHealth.create_healthy("custom", message="Custom check")
        
        health_service.register_health_check("custom", custom_check)
        assert "custom" in health_service._health_checks
        assert len(health_service._health_checks) == 6  # 5 built-in + 1 custom
    
    def test_register_duplicate_health_check(self, health_service):
        """Test registering duplicate health check overwrites existing."""
        async def first_check():
            return ComponentHealth.create_healthy("test")
        
        async def second_check():
            return ComponentHealth.create_degraded("test", "Updated")
        
        health_service.register_health_check("test_check", first_check)
        health_service.register_health_check("test_check", second_check)
        
        # Should still have the same total count (overwrite, not add)
        assert len(health_service._health_checks) == 6  # 5 built-in + 1 custom
        assert health_service._health_checks["test_check"] == second_check
    
    @pytest.mark.asyncio
    async def test_get_health_status_all_healthy(self, health_service):
        """Test get_health_status with all components healthy."""
        # Create mock health check functions
        async def mock_api():
            return ComponentHealth.create_healthy("api_connectivity")

        async def mock_config():
            return ComponentHealth.create_healthy("configuration")

        async def mock_memory():
            return ComponentHealth.create_healthy("memory_usage")

        async def mock_disk():
            return ComponentHealth.create_healthy("disk_space")

        async def mock_logging():
            return ComponentHealth.create_healthy("logging_system")

        # Replace the health checks dict
        health_service._health_checks = {
            "api_connectivity": mock_api,
            "configuration": mock_config,
            "memory_usage": mock_memory,
            "disk_space": mock_disk,
            "logging_system": mock_logging
        }

        system_health = await health_service.get_health_status()

        assert system_health.status == HealthStatus.HEALTHY
        assert system_health.is_healthy is True
        assert len(system_health.components) == 5
        assert system_health.summary["healthy_components"] == 5
        assert system_health.summary["unhealthy_components"] == 0
    
    @pytest.mark.asyncio
    async def test_get_health_status_with_unhealthy_component(self, health_service):
        """Test get_health_status with one unhealthy component."""
        # Create mock health check functions
        async def mock_api():
            return ComponentHealth.create_unhealthy("api_connectivity", "API down")

        async def mock_config():
            return ComponentHealth.create_healthy("configuration")

        async def mock_memory():
            return ComponentHealth.create_healthy("memory_usage")

        async def mock_disk():
            return ComponentHealth.create_healthy("disk_space")

        async def mock_logging():
            return ComponentHealth.create_healthy("logging_system")

        # Replace the health checks dict
        health_service._health_checks = {
            "api_connectivity": mock_api,
            "configuration": mock_config,
            "memory_usage": mock_memory,
            "disk_space": mock_disk,
            "logging_system": mock_logging
        }

        system_health = await health_service.get_health_status()

        assert system_health.status == HealthStatus.UNHEALTHY
        assert system_health.is_healthy is False
        assert len(system_health.components) == 5
        assert system_health.summary["healthy_components"] == 4
        assert system_health.summary["unhealthy_components"] == 1
    
    @pytest.mark.asyncio
    async def test_get_health_status_with_degraded_component(self, health_service):
        """Test get_health_status with degraded component."""
        # Create mock health check functions
        async def mock_api():
            return ComponentHealth.create_healthy("api_connectivity")

        async def mock_config():
            return ComponentHealth.create_healthy("configuration")

        async def mock_memory():
            return ComponentHealth.create_degraded("memory_usage", "High usage")

        async def mock_disk():
            return ComponentHealth.create_healthy("disk_space")

        async def mock_logging():
            return ComponentHealth.create_healthy("logging_system")

        # Replace the health checks dict
        health_service._health_checks = {
            "api_connectivity": mock_api,
            "configuration": mock_config,
            "memory_usage": mock_memory,
            "disk_space": mock_disk,
            "logging_system": mock_logging
        }

        system_health = await health_service.get_health_status()

        assert system_health.status == HealthStatus.DEGRADED
        assert system_health.is_healthy is False
        assert len(system_health.components) == 5
        assert system_health.summary["healthy_components"] == 4
        assert system_health.summary["degraded_components"] == 1
    
    @pytest.mark.asyncio
    async def test_get_health_status_without_details(self, health_service):
        """Test get_health_status without detailed component info."""
        with patch.object(health_service, '_run_single_check') as mock_check:
            mock_check.return_value = ComponentHealth.create_healthy("test")
            
            system_health = await health_service.get_health_status(include_details=False)
            
            assert len(system_health.components) == 0
            assert "total_components" in system_health.summary
    
    @pytest.mark.asyncio
    async def test_run_single_check_success(self, health_service):
        """Test _run_single_check with successful check."""
        async def successful_check():
            return ComponentHealth.create_healthy("test_component")
        
        result = await health_service._run_single_check("test", successful_check)
        
        assert result.name == "test_component"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_run_single_check_exception(self, health_service):
        """Test _run_single_check with exception."""
        async def failing_check():
            raise Exception("Test exception")
        
        result = await health_service._run_single_check("test", failing_check)
        
        assert result.name == "test"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Test exception" in result.message
        assert result.response_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_check_configuration_valid(self, health_service):
        """Test _check_configuration with valid configuration."""
        result = await health_service._check_configuration()
        
        assert result.name == "configuration"
        assert result.status == HealthStatus.HEALTHY
        assert "Configuration is valid" in result.message
    
    @pytest.mark.asyncio
    async def test_check_configuration_missing_api_key(self, health_service):
        """Test _check_configuration with missing API key."""
        health_service.settings.api_key.get_secret_value.return_value = ""
        
        result = await health_service._check_configuration()
        
        assert result.name == "configuration"
        assert result.status == HealthStatus.UNHEALTHY
        assert "API key is not configured" in result.message
    
    @pytest.mark.asyncio
    async def test_check_api_connectivity_success(self, health_service):
        """Test _check_api_connectivity with successful connection."""
        with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_instance.get.return_value = mock_response
            
            result = await health_service._check_api_connectivity()
            
            assert result.name == "api_connectivity"
            assert result.status == HealthStatus.HEALTHY
            assert "API is reachable" in result.message
    
    @pytest.mark.asyncio
    async def test_check_api_connectivity_failure(self, health_service):
        """Test _check_api_connectivity with connection failure."""
        with patch('qolaba_mcp_server.api.client.QolabaHTTPClient') as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            
            result = await health_service._check_api_connectivity()
            
            assert result.name == "api_connectivity"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection failed" in result.message
    
    @pytest.mark.asyncio
    async def test_check_memory_usage_normal(self, health_service):
        """Test _check_memory_usage with normal usage."""
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.percent = 60.0
            mock_memory.return_value.available = 8 * 1024**3  # 8GB
            mock_memory.return_value.total = 16 * 1024**3  # 16GB
            
            result = await health_service._check_memory_usage()
            
            assert result.name == "memory_usage"
            assert result.status == HealthStatus.HEALTHY
            assert "Memory usage normal" in result.message
    
    @pytest.mark.asyncio
    async def test_check_memory_usage_high(self, health_service):
        """Test _check_memory_usage with high usage."""
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = MagicMock()
            mock_memory.return_value.percent = 95.0
            mock_memory.return_value.available = 1 * 1024**3  # 1GB
            mock_memory.return_value.total = 16 * 1024**3  # 16GB
            
            result = await health_service._check_memory_usage()
            
            assert result.name == "memory_usage"
            assert result.status == HealthStatus.UNHEALTHY
            assert "High memory usage" in result.message
    
    @pytest.mark.asyncio
    async def test_check_logging_system_success(self, health_service):
        """Test _check_logging_system success."""
        result = await health_service._check_logging_system()
        
        assert result.name == "logging_system"
        assert result.status == HealthStatus.HEALTHY
        assert "Logging system operational" in result.message


class TestHealthCheckSingleton:
    """Test health check service singleton pattern."""
    
    def test_get_health_service_singleton(self):
        """Test that get_health_service returns singleton instance."""
        with patch('qolaba_mcp_server.health.health_check.get_settings'):
            # Clear singleton
            import qolaba_mcp_server.health.health_check as hc_module
            hc_module._health_service = None
            
            # Get first instance
            service1 = get_health_service()
            assert service1 is not None
            
            # Get second instance - should be same
            service2 = get_health_service()
            assert service1 is service2
            
            # Clear for other tests
            hc_module._health_service = None


class TestHealthCheckEndpoints:
    """Test health check HTTP endpoints."""
    
    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI request."""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers.get.return_value = "test-agent"
        request.state.request_id = "test_request_123"
        return request
    
    @pytest.fixture
    def mock_healthy_system(self):
        """Create mock healthy system health."""
        return SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=1234.0,
            version="1.0.0",
            components=[ComponentHealth.create_healthy("test_component")],
            summary={"total_components": 1, "healthy_components": 1}
        )
    
    @pytest.fixture
    def mock_unhealthy_system(self):
        """Create mock unhealthy system health."""
        return SystemHealth(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=1234.0,
            version="1.0.0",
            components=[ComponentHealth.create_unhealthy("test_component", "Failed")],
            summary={"total_components": 1, "unhealthy_components": 1}
        )
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint_healthy_system(self, mock_request, mock_healthy_system):
        """Test health check endpoint with healthy system."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_health_status.return_value = mock_healthy_system
            
            response = await health_check_endpoint(mock_request, detailed=True, format="json")
            
            assert response.status_code == 200
            content = response.body.decode()
            assert "healthy" in content.lower()
            assert "test_component" in content
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint_unhealthy_system(self, mock_request, mock_unhealthy_system):
        """Test health check endpoint with unhealthy system."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_health_status.return_value = mock_unhealthy_system
            
            response = await health_check_endpoint(mock_request, detailed=True, format="json")
            
            assert response.status_code == 503
            content = response.body.decode()
            assert "unhealthy" in content.lower()
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint_simple_format(self, mock_request, mock_healthy_system):
        """Test health check endpoint with simple format."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_health_status.return_value = mock_healthy_system
            
            response = await health_check_endpoint(mock_request, detailed=False, format="simple")
            
            assert response.status_code == 200
            content = response.body.decode()
            # Simple format should have fewer details
            assert "components" not in content
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint_exception(self, mock_request):
        """Test health check endpoint with exception."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_service.side_effect = Exception("Service failure")
            
            response = await health_check_endpoint(mock_request)
            
            assert response.status_code == 500
            content = response.body.decode()
            assert "error" in content.lower()
    
    @pytest.mark.asyncio
    async def test_readiness_probe_ready(self, mock_request, mock_healthy_system):
        """Test readiness probe with ready system."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_health_status.return_value = mock_healthy_system
            
            response = await readiness_probe_endpoint(mock_request)
            
            assert response.status_code == 200
            content = response.body.decode()
            assert '"ready":true' in content
    
    @pytest.mark.asyncio
    async def test_readiness_probe_not_ready(self, mock_request, mock_unhealthy_system):
        """Test readiness probe with not ready system."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_health_status.return_value = mock_unhealthy_system
            
            response = await readiness_probe_endpoint(mock_request)
            
            assert response.status_code == 503
            content = response.body.decode()
            assert '"ready":false' in content
    
    @pytest.mark.asyncio
    async def test_liveness_probe_alive(self, mock_request):
        """Test liveness probe with alive system."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_instance = MagicMock()
            mock_instance._start_time = time.time() - 1000  # 1000 seconds ago
            mock_service.return_value = mock_instance
            
            response = await liveness_probe_endpoint(mock_request)
            
            assert response.status_code == 200
            content = response.body.decode()
            assert '"alive":true' in content
    
    @pytest.mark.asyncio
    async def test_liveness_probe_with_issues(self, mock_request):
        """Test liveness probe with service issues."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_service.side_effect = Exception("Service issue")
            
            response = await liveness_probe_endpoint(mock_request)
            
            # Should still return 200 (alive) even with issues
            assert response.status_code == 200
            content = response.body.decode()
            assert '"alive":true' in content
            assert "alive_with_issues" in content
    
    @pytest.mark.asyncio
    async def test_simple_health_check_function(self):
        """Test simple health check function."""
        mock_system_health = SystemHealth(
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=100.0,
            version="1.0.0",
            components=[]
        )
        
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_health_status.return_value = mock_system_health
            
            result = await simple_health_check()
            
            assert result["healthy"] is True
            assert result["status"] == "healthy"
            assert result["uptime_seconds"] == 100.0
    
    @pytest.mark.asyncio
    async def test_simple_health_check_exception(self):
        """Test simple health check function with exception."""
        with patch('qolaba_mcp_server.health.endpoints.get_health_service') as mock_service:
            mock_service.side_effect = Exception("Test error")
            
            result = await simple_health_check()
            
            assert result["healthy"] is False
            assert result["status"] == "error"
            assert "Test error" in result["error"]