"""
Metrics Server for Deep Research System
Provides Prometheus metrics endpoint and health checks
"""

import asyncio
import logging
from aiohttp import web
import os
import json
from monitoring import metrics, health_checker, alert_manager, PROMETHEUS_AVAILABLE, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

async def metrics_handler(request):
    """Handle /metrics endpoint for Prometheus"""
    metrics_data = metrics.get_metrics()
    return web.Response(
        body=metrics_data,
        content_type=CONTENT_TYPE_LATEST if PROMETHEUS_AVAILABLE else 'text/plain'
    )

async def health_handler(request):
    """Handle /health endpoint"""
    health_status = await health_checker.check_health()
    status_code = 200 if health_status["status"] == "healthy" else 503
    return web.json_response(health_status, status=status_code)

async def alerts_handler(request):
    """Handle /alerts endpoint"""
    last_n = int(request.query.get('last_n', 10))
    alerts = alert_manager.get_alerts(last_n)
    return web.json_response({
        "alerts": alerts,
        "total_alerts": len(alert_manager.alerts)
    })

async def shadow_metrics_handler(request):
    """Handle /api/performance/shadow endpoint"""
    # Read shadow mode comparison data
    perf_dir = os.getenv("PERFORMANCE_DATA_DIR", "./performance_data")
    shadow_file = os.path.join(perf_dir, "shadow_comparisons.json")
    
    if os.path.exists(shadow_file):
        try:
            with open(shadow_file, 'r') as f:
                data = json.load(f)
            return web.json_response(data)
        except Exception as e:
            return web.json_response({
                "error": f"Failed to read shadow data: {str(e)}"
            }, status=500)
    else:
        return web.json_response({
            "message": "No shadow mode data available yet"
        }, status=404)

def create_metrics_app():
    """Create aiohttp application for metrics"""
    app = web.Application()
    app.router.add_get('/metrics', metrics_handler)
    app.router.add_get('/health', health_handler)
    app.router.add_get('/alerts', alerts_handler)
    app.router.add_get('/api/performance/shadow', shadow_metrics_handler)
    return app

async def start_metrics_server(port: int = 9090):
    """Start the metrics server"""
    app = create_metrics_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Metrics server started on port {port}")
    logger.info(f"Available endpoints:")
    logger.info(f"  - http://localhost:{port}/metrics (Prometheus metrics)")
    logger.info(f"  - http://localhost:{port}/health (Health check)")
    logger.info(f"  - http://localhost:{port}/alerts (Active alerts)")
    logger.info(f"  - http://localhost:{port}/api/performance/shadow (Shadow mode data)")
    return runner

def run_metrics_server():
    """Run metrics server standalone"""
    port = int(os.getenv("METRICS_PORT", "9090"))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        runner = loop.run_until_complete(start_metrics_server(port))
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down metrics server...")
        loop.run_until_complete(runner.cleanup())
    finally:
        loop.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_metrics_server()