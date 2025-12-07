"""
Unit tests for tool functions.

These are pure functions that don't require mocking.
"""


# -----------------------------------------------------------------------------
# Math Tools Tests
# -----------------------------------------------------------------------------


class TestMathTools:
    """Tests for math_tools.py functions."""

    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        from tools.math_tools import add

        result = add(2, 3)
        assert result == 5

    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        from tools.math_tools import add

        result = add(-2, -3)
        assert result == -5

    def test_add_mixed_numbers(self):
        """Test adding positive and negative numbers."""
        from tools.math_tools import add

        result = add(5, -3)
        assert result == 2

    def test_add_floats(self):
        """Test adding floating point numbers."""
        from tools.math_tools import add

        result = add(2.5, 3.5)
        assert result == 6.0

    def test_add_zero(self):
        """Test adding with zero."""
        from tools.math_tools import add

        assert add(5, 0) == 5
        assert add(0, 5) == 5
        assert add(0, 0) == 0

    def test_multiply_positive_numbers(self):
        """Test multiplying two positive numbers."""
        from tools.math_tools import multiply

        result = multiply(4, 5)
        assert result == 20

    def test_multiply_negative_numbers(self):
        """Test multiplying negative numbers."""
        from tools.math_tools import multiply

        result = multiply(-4, -5)
        assert result == 20

    def test_multiply_mixed_numbers(self):
        """Test multiplying positive and negative numbers."""
        from tools.math_tools import multiply

        result = multiply(4, -5)
        assert result == -20

    def test_multiply_floats(self):
        """Test multiplying floating point numbers."""
        from tools.math_tools import multiply

        result = multiply(2.5, 4.0)
        assert result == 10.0

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        from tools.math_tools import multiply

        assert multiply(5, 0) == 0
        assert multiply(0, 5) == 0

    def test_multiply_by_one(self):
        """Test multiplying by one (identity)."""
        from tools.math_tools import multiply

        assert multiply(7, 1) == 7
        assert multiply(1, 7) == 7


# -----------------------------------------------------------------------------
# Market Tools Tests
# -----------------------------------------------------------------------------


class TestMarketTools:
    """Tests for market_tools.py functions."""

    def test_get_index_returns_dict(self):
        """Test that get_index returns a dictionary."""
        from tools.market_tools import get_index

        result = get_index("NIFTY")
        assert isinstance(result, dict)
        assert "value" in result
        assert "change" in result
        assert "volume" in result

    def test_get_index_nifty(self):
        """Test getting NIFTY index."""
        from tools.market_tools import get_index

        result = get_index("NIFTY")
        assert isinstance(result["value"], float)
        assert result["value"] == 24680.50

    def test_get_index_sensex(self):
        """Test getting SENSEX index."""
        from tools.market_tools import get_index

        result = get_index("SENSEX")
        assert isinstance(result["value"], float)
        assert result["value"] == 81205.75

    def test_get_index_unknown(self):
        """Test getting unknown index returns error."""
        from tools.market_tools import get_index

        result = get_index("UNKNOWN_INDEX")
        assert "error" in result
        # Should return error message for unknown index


# -----------------------------------------------------------------------------
# Research Tools Tests (require mocking)
# -----------------------------------------------------------------------------


class TestResearchTools:
    """Tests for research_tools.py functions."""

    def test_web_search_returns_string(self, mock_perplexity_client):
        """Test that web_search returns a string response."""
        from tools.research_tools import web_search

        result = web_search("test query")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_web_search_calls_api(self, mock_perplexity_client):
        """Test that web_search calls the Perplexity API."""
        from tools.research_tools import web_search

        web_search("test query")

        # Verify API was called
        mock_perplexity_client.chat.completions.create.assert_called_once()

    def test_web_search_with_empty_query(self, mock_perplexity_client):
        """Test web_search with empty query."""
        from tools.research_tools import web_search

        result = web_search("")
        assert isinstance(result, str)
