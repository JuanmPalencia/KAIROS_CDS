from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Métricas
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

incidents_created_total = Counter(
    'incidents_created_total',
    'Total incidents created'
)

incidents_resolved_total = Counter(
    'incidents_resolved_total',
    'Total incidents resolved'
)

available_vehicles_count = Gauge(
    'available_vehicles_count',
    'Number of available vehicles'
)

database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections'
)


def metrics_endpoint():
    """Generate Prometheus metrics"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
