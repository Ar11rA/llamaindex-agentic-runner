import logging

logger = logging.getLogger(__name__)


def multiply(a: float, b: float) -> float:
    """Multiply two numbers and returns the product"""
    result = a * b
    logger.info("multiply(%s, %s) = %s", a, b, result)
    return result


def add(a: float, b: float) -> float:
    """Add two numbers and returns the sum"""
    result = a + b
    logger.info("add(%s, %s) = %s", a, b, result)
    return result
