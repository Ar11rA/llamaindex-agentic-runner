"""
Observability configuration using Arize Phoenix.

Traces all LlamaIndex operations (agents, teams, flows) automatically.
Based on: https://developers.llamaindex.ai/python/llamaagents/workflows/observability/
"""

import logging
import os

from config.settings import get_settings

logger = logging.getLogger(__name__)


def setup_observability():
    """
    Initialize Arize Phoenix tracing for LlamaIndex.

    Call this once at application startup (before any LlamaIndex operations).
    Automatically traces all agents, teams, and flows.

    Returns:
        The tracer provider if successful, None otherwise.
    """
    settings = get_settings()

    if not settings.phoenix_enabled:
        logger.info(
            "Phoenix observability disabled (set PHOENIX_ENABLED=true to enable)"
        )
        return None

    try:
        from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

        # Set Phoenix collector endpoint via environment variable
        if settings.phoenix_endpoint:
            os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = settings.phoenix_endpoint
            logger.info(f"Phoenix collector endpoint: {settings.phoenix_endpoint}")

        # Choose processor based on setting
        if settings.phoenix_batch_processor:
            tracer_provider = _create_batch_tracer(settings)
        else:
            tracer_provider = _create_simple_tracer(settings)

        # Instrument LlamaIndex - captures ALL LlamaIndex operations:
        # - Agents (FunctionAgent, tool calls, LLM calls)
        # - Teams (AgentWorkflow, agent handoffs)
        # - Flows (@step functions, event routing)
        LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)

        logger.info("LlamaIndex instrumentation complete")
        return tracer_provider

    except ImportError as e:
        logger.warning(f"Phoenix dependencies not installed: {e}")
        logger.warning(
            "Run: uv pip install arize-phoenix openinference-instrumentation-llama_index"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix observability: {e}")
        return None


def _create_simple_tracer(settings):
    """
    Development mode: SimpleSpanProcessor via phoenix.otel.register().

    Spans are exported immediately and synchronously.
    Good for debugging - see traces instantly.
    """
    from phoenix.otel import register

    tracer_provider = register(project_name=settings.phoenix_project_name)
    logger.info("Using SimpleSpanProcessor (development mode)")
    return tracer_provider


def _create_batch_tracer(settings):
    """
    Production mode: BatchSpanProcessor with HTTP transport.

    Spans are batched and exported asynchronously for better performance.
    Uses the same HTTP endpoint as Phoenix web UI (port 6006).
    """
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # HTTP endpoint - same port as Phoenix web UI
    http_endpoint = settings.phoenix_endpoint or "http://localhost:6006"
    if not http_endpoint.endswith("/v1/traces"):
        http_endpoint = f"{http_endpoint}/v1/traces"

    logger.info(f"BatchSpanProcessor endpoint: {http_endpoint}")

    # Create resource with project name (shows in Phoenix UI)
    resource = Resource.create(
        {
            "service.name": settings.phoenix_project_name,
            "project.name": settings.phoenix_project_name,
        }
    )

    # Create TracerProvider
    tracer_provider = TracerProvider(resource=resource)

    # Create HTTP exporter to Phoenix
    exporter = OTLPSpanExporter(endpoint=http_endpoint)

    # Create BatchSpanProcessor with production settings
    batch_processor = BatchSpanProcessor(
        exporter,
        max_queue_size=2048,  # Max spans to queue before dropping
        max_export_batch_size=512,  # Spans per export batch
        schedule_delay_millis=5000,  # Export every 5 seconds
    )

    # Add processor and set as global
    tracer_provider.add_span_processor(batch_processor)
    trace.set_tracer_provider(tracer_provider)

    logger.info("Using BatchSpanProcessor (production mode)")
    return tracer_provider
