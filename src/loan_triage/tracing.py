"""OpenTelemetry span helpers."""

from contextlib import contextmanager
from typing import Any, Dict, Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    
    # Configure tracer
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(ConsoleSpanExporter())
    )
    
    tracer = trace.get_tracer(__name__)
    
    @contextmanager
    def span(name: str, attributes: Dict[str, Any] = None):
        """Context manager for creating spans."""
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span
    
    def record_exception(span, exception: Exception) -> None:
        """Record an exception on a span."""
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
        span.record_exception(exception)
        
except ImportError:
    # Fallback if OpenTelemetry is not installed
    @contextmanager
    def span(name: str, attributes: Dict[str, Any] = None):
        """Context manager for creating spans (no-op fallback)."""
        yield None
    
    def record_exception(span, exception: Exception) -> None:
        """Record an exception (no-op fallback)."""
        pass
