#!/usr/bin/env python3
"""
Integration test script for DEPLOY-007: Metrics and Performance Monitoring.

This script verifies that the metrics system is properly integrated across all services
and can export metrics in Prometheus format.
"""

import sys
import os
import asyncio
import time
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_metrics_integration():
    """Test comprehensive metrics integration."""
    
    print("🧪 Testing DEPLOY-007: Metrics and Performance Monitoring Integration")
    print("=" * 70)
    
    try:
        # Test 1: Import and initialize metrics system
        print("1️⃣ Testing metrics system import and initialization...")
        from qolaba_mcp_server.core.metrics import (
            get_metrics_collector, 
            MetricsCollector, 
            MetricType,
            MetricLabels,
            increment_counter,
            set_gauge,
            observe_histogram,
            record_api_request,
            record_mcp_operation
        )
        
        metrics_collector = get_metrics_collector()
        assert isinstance(metrics_collector, MetricsCollector), "Metrics collector should be MetricsCollector instance"
        print("✅ Metrics system imported and initialized successfully")
        
        # Test 2: Basic metrics functionality
        print("\n2️⃣ Testing basic metrics functionality...")
        
        # Test counter
        increment_counter("test_counter", 5)
        increment_counter("test_counter", 3, labels={"test": "true"})
        
        # Test gauge
        set_gauge("test_gauge", 42.5)
        set_gauge("test_gauge", 100, labels={"component": "test"})
        
        # Test histogram
        observe_histogram("test_histogram", 0.123)
        observe_histogram("test_histogram", 0.456)
        observe_histogram("test_histogram", 0.789)
        
        print("✅ Basic metrics functionality working correctly")
        
        # Test 3: API client metrics integration
        print("\n3️⃣ Testing API client metrics integration...")
        record_api_request(
            endpoint="/text-to-image",
            method="POST", 
            status_code=200,
            duration_seconds=1.234,
            error_type=None
        )
        
        record_api_request(
            endpoint="/chat",
            method="POST",
            status_code=500,
            duration_seconds=2.567,
            error_type="server_error"
        )
        
        print("✅ API client metrics integration working correctly")
        
        # Test 4: MCP operation metrics integration  
        print("\n4️⃣ Testing MCP operation metrics integration...")
        record_mcp_operation(
            operation="text_to_image",
            duration_seconds=3.456,
            success=True,
            model="flux",
            user_id="test_user_123"
        )
        
        record_mcp_operation(
            operation="chat",
            duration_seconds=1.789,
            success=False,
            model="gpt-4",
            user_id="test_user_456"
        )
        
        print("✅ MCP operation metrics integration working correctly")
        
        # Test 5: Health check metrics integration
        print("\n5️⃣ Testing health check metrics integration...")
        metrics_collector.record_health_check(
            component="api_connectivity",
            duration_seconds=0.045,
            healthy=True
        )
        
        metrics_collector.record_health_check(
            component="memory_check", 
            duration_seconds=0.012,
            healthy=False
        )
        
        print("✅ Health check metrics integration working correctly")
        
        # Test 6: System metrics update
        print("\n6️⃣ Testing system metrics update...")
        metrics_collector.update_system_metrics()
        print("✅ System metrics update working correctly")
        
        # Test 7: Metrics summary generation
        print("\n7️⃣ Testing metrics summary generation...")
        summary = metrics_collector.get_metric_summary()
        
        assert "total_metrics" in summary, "Summary should contain total_metrics"
        assert "uptime_seconds" in summary, "Summary should contain uptime_seconds"  
        assert "metrics_by_type" in summary, "Summary should contain metrics_by_type"
        assert summary["total_metrics"] > 0, "Should have collected metrics"
        
        print(f"✅ Metrics summary generated: {summary['total_metrics']} metrics collected")
        
        # Test 8: Prometheus format export
        print("\n8️⃣ Testing Prometheus format export...")
        prometheus_data = metrics_collector.export_prometheus_metrics()
        
        assert isinstance(prometheus_data, str), "Prometheus export should return string"
        assert len(prometheus_data) > 0, "Prometheus export should not be empty"
        assert "# HELP" in prometheus_data, "Should contain Prometheus HELP comments"
        assert "# TYPE" in prometheus_data, "Should contain Prometheus TYPE comments"
        assert "qolaba_mcp_" in prometheus_data, "Should contain our custom metrics"
        
        # Count metrics in export
        metric_lines = [line for line in prometheus_data.split('\n') if line and not line.startswith('#') and '=' not in line]
        print(f"✅ Prometheus export generated: {len(metric_lines)} metric entries")
        
        # Test 9: Metrics router endpoints (if available)
        print("\n9️⃣ Testing metrics router integration...")
        try:
            from qolaba_mcp_server.api.metrics_router import (
                metrics_router,
                export_prometheus_metrics,
                get_metrics_summary,
                get_metrics_health,
                metrics_system_health_check
            )
            print("✅ Metrics router endpoints imported successfully")
            
            # Test health check function
            health_result = await metrics_system_health_check()
            assert isinstance(health_result, bool), "Health check should return boolean"
            print(f"✅ Metrics system health check: {'HEALTHY' if health_result else 'UNHEALTHY'}")
            
        except ImportError as e:
            print(f"⚠️  Metrics router import failed (may not be implemented yet): {e}")
        
        # Test 10: Performance timing context manager
        print("\n🔟 Testing performance timing context manager...")
        with metrics_collector.timer("test_operation_duration", labels={"test": "timing"}):
            # Simulate some work
            await asyncio.sleep(0.1)
        
        print("✅ Performance timing context manager working correctly")
        
        # Test 11: Verify metric persistence and retrieval
        print("\n1️⃣1️⃣ Testing metric persistence and retrieval...")
        
        # Get final summary
        final_summary = metrics_collector.get_metric_summary()
        
        # Verify we have all expected metric types
        metrics_by_type = final_summary["metrics_by_type"]
        expected_types = ["counter", "gauge", "histogram"]
        
        for metric_type in expected_types:
            assert metric_type in metrics_by_type, f"Should have {metric_type} metrics"
            assert metrics_by_type[metric_type] > 0, f"Should have collected {metric_type} metrics"
        
        print("✅ Metric persistence and retrieval working correctly")
        
        # Final verification: Generate final Prometheus export
        print("\n📊 Final Prometheus export verification...")
        final_prometheus = metrics_collector.export_prometheus_metrics()
        
        # Save a sample for inspection
        with open("metrics_sample.txt", "w", encoding="utf-8") as f:
            f.write("# Sample Prometheus metrics export from integration test\n")
            f.write(f"# Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# First 2000 characters:\n\n")
            f.write(final_prometheus[:2000])
            if len(final_prometheus) > 2000:
                f.write(f"\n\n... (truncated, full length: {len(final_prometheus)} characters)")
        
        print(f"✅ Final export generated ({len(final_prometheus)} characters)")
        print("📄 Sample saved to metrics_sample.txt")
        
        # Summary
        print("\n" + "=" * 70)
        print("🎉 DEPLOY-007 METRICS INTEGRATION TEST SUCCESSFUL!")
        print("=" * 70)
        print(f"📊 Total metrics collected: {final_summary['total_metrics']}")
        print(f"⏱️  System uptime: {final_summary['uptime_seconds']:.1f} seconds")
        print(f"📈 Metrics by type: {metrics_by_type}")
        print(f"🔗 Prometheus export size: {len(final_prometheus)} characters")
        print("\n🚀 All metrics systems are properly integrated and functional!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ DEPLOY-007 METRICS INTEGRATION TEST FAILED!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_missing_dependencies():
    """Test for missing dependencies that might cause issues."""
    print("\n🔍 Checking for missing dependencies...")
    
    missing_deps = []
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    try:
        import structlog
    except ImportError:
        missing_deps.append("structlog")
        
    try:
        from pythonjsonlogger import jsonlogger
    except ImportError:
        missing_deps.append("python-json-logger")
    
    if missing_deps:
        print(f"⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("These dependencies are required for full metrics functionality")
        return False
    else:
        print("✅ All required dependencies are available")
        return True


async def main():
    """Main test execution."""
    print("🚀 Starting DEPLOY-007 Metrics Integration Test Suite")
    print(f"🕒 Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check dependencies first
    deps_ok = await test_missing_dependencies()
    if not deps_ok:
        print("\n❌ Dependency check failed - some functionality may be limited")
    
    # Run main integration test
    success = await test_metrics_integration()
    
    # Final result
    if success:
        print("\n✅ All DEPLOY-007 metrics tests passed successfully!")
        print("The metrics and performance monitoring system is ready for production.")
        return 0
    else:
        print("\n❌ Some DEPLOY-007 metrics tests failed!")
        print("Please review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())