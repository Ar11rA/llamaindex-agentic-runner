import logging

import openai

from config import get_settings

logger = logging.getLogger(__name__)


def _get_perplexity_client() -> openai.OpenAI:
    """Get the Perplexity client instance."""
    settings = get_settings()
    return openai.OpenAI(
        api_key=settings.perplexity_api_key,
        base_url=settings.perplexity_api_base_url,
    )


def web_search(query: str) -> str:
    """Search the web for information using Perplexity AI."""
    logger.info("web_search query: %s", query)

    settings = get_settings()
    client = _get_perplexity_client()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "do web search and return response to user."
            ),
        },
        {
            "role": "user",
            "content": query,
        },
    ]

    response = client.chat.completions.create(
        model=settings.perplexity_model,
        messages=messages,
    )

    result = response.choices[0].message.content.strip()
    logger.info(
        "web_search result: %s", result[:200] + "..." if len(result) > 200 else result
    )

    return result
