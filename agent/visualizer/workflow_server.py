"""
Debug server for LlamaIndex Workflows.

Based on: https://developers.llamaindex.ai/python/llamaagents/workflows/deployment/

This server provides a REST API for interacting with workflows including:
- POST /workflows/{name}/run - Run a workflow synchronously
- POST /workflows/{name}/run-nowait - Run a workflow asynchronously
- GET /events/{handler_id} - Stream events from an async workflow
- POST /events/{handler_id} - Send events (for HITL)
- GET /results/{handler_id} - Get result of an async workflow
- POST /handlers/{handler_id}/cancel - Cancel a running workflow

Usage:
    python -m obs.workflow_server

Or import and run programmatically:
    from obs.workflow_server import serve
    import asyncio
    asyncio.run(serve())
"""

import asyncio
import logging

from workflows.server import WorkflowServer

from flows.story_flow import StoryFlow
from flows.story_critic_flow import StoryCriticFlow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_server() -> WorkflowServer:
    """Create and configure the WorkflowServer with all flows."""
    server = WorkflowServer()

    # Register StoryFlow
    story_flow = StoryFlow(timeout=600.0, verbose=True)
    server.add_workflow("story_flow", story_flow)
    logger.info("Registered workflow: story_flow")

    # Register StoryCriticFlow (with branching/looping)
    story_critic_flow = StoryCriticFlow(timeout=900.0, verbose=True)
    server.add_workflow("story_critic_flow", story_critic_flow)
    logger.info("Registered workflow: story_critic_flow")

    return server


async def serve(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the workflow debug server.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 8081)

    The server provides these endpoints:
        GET  /workflows              - List available workflows
        POST /workflows/{name}/run   - Run workflow synchronously
        POST /workflows/{name}/run-nowait - Run workflow async
        GET  /events/{handler_id}    - Stream events (SSE)
        POST /events/{handler_id}    - Send events (HITL)
        GET  /results/{handler_id}   - Get workflow result
        POST /handlers/{handler_id}/cancel - Cancel workflow
    """
    server = create_server()

    logger.info("=" * 50)
    logger.info("Starting Workflow Debug Server")
    logger.info("=" * 50)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"API Docs: http://{host}:{port}/docs")
    logger.info("=" * 50)
    logger.info("Available workflows:")
    logger.info("  - story_flow: Research a topic and write an article")
    logger.info(
        "  - story_critic_flow: Research, write, critique & iterate (max 3 attempts)"
    )
    logger.info("=" * 50)

    await server.serve(host, port)


if __name__ == "__main__":
    asyncio.run(serve())
