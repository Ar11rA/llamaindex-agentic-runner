import logging
from typing import Any

from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent

logger = logging.getLogger(__name__)


def get_index(index_name: str) -> dict[str, Any]:
    """Get the current value of a market index."""
    logger.info("get_index called for: %s", index_name)

    # Mock implementation
    mock_data = {
        "SP500": {"value": 5234.18, "change": "+0.45%", "volume": "3.2B"},
        "NASDAQ": {"value": 16742.39, "change": "+0.67%", "volume": "4.1B"},
        "DOW": {"value": 39872.99, "change": "+0.23%", "volume": "2.8B"},
        "NIFTY": {"value": 24680.50, "change": "+0.32%", "volume": "1.8B"},
        "SENSEX": {"value": 81205.75, "change": "+0.28%", "volume": "1.5B"},
    }

    # Normalize the index name
    normalized = index_name.upper().replace(" ", "").replace("&", "").replace("50", "")
    if "NIFTY" in normalized:
        normalized = "NIFTY"
    elif "S&P" in index_name.upper() or "SP" in normalized:
        normalized = "SP500"

    result = mock_data.get(normalized, {"error": f"Index '{index_name}' not found"})

    logger.info("get_index result: %s", result)
    return result


async def push_index(ctx: Context, index_name: str, value: float) -> str:
    """
    Push/update a market index value.

    ⚠️ DANGEROUS OPERATION - Requires human confirmation before execution.

    Args:
        ctx: Workflow context (automatically injected)
        index_name: Name of the index to update
        value: New value to set

    Returns:
        Success or abort message
    """
    logger.info("push_index called for: %s with value: %s", index_name, value)

    # Request human confirmation using HITL pattern
    question = f"⚠️ CONFIRM: Update '{index_name}' to {value}? (yes/no) "

    response = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id=question,
        waiter_event=InputRequiredEvent(
            prefix=question,
            user_name="operator",
        ),
        requirements={"user_name": "operator"},
    )

    # Act on the human response
    human_answer = response.response.strip().lower()
    if human_answer in ("yes", "y", "confirm", "approved"):
        result = f"✅ SUCCESS: Index '{index_name}' updated to {value}"
        logger.info("push_index confirmed: %s", result)
        return result
    else:
        result = f"❌ ABORTED: Update to '{index_name}' was cancelled by operator (response: '{response.response}')"
        logger.info("push_index aborted: %s", result)
        return result
