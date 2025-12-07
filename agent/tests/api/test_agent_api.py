"""
API tests for agent controller endpoints.

Tests HTTP endpoints with mocked agent execution.
"""

from unittest.mock import patch


# -----------------------------------------------------------------------------
# List Agents Endpoint Tests
# -----------------------------------------------------------------------------


class TestListAgentsEndpoint:
    """Tests for GET /api/v1/agents endpoint."""

    def test_list_agents_returns_200(self, test_client):
        """Test list agents returns 200 status."""
        response = test_client.get("/api/v1/agents")
        assert response.status_code == 200

    def test_list_agents_returns_list(self, test_client):
        """Test list agents returns a list of agents."""
        response = test_client.get("/api/v1/agents")
        data = response.json()

        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_list_agents_contains_math(self, test_client):
        """Test list agents contains math agent."""
        response = test_client.get("/api/v1/agents")
        data = response.json()

        agent_ids = [a["id"] for a in data["agents"]]
        assert "math" in agent_ids

    def test_list_agents_has_required_fields(self, test_client):
        """Test each agent has required fields."""
        response = test_client.get("/api/v1/agents")
        data = response.json()

        for agent in data["agents"]:
            assert "id" in agent
            assert "name" in agent
            assert "description" in agent


# -----------------------------------------------------------------------------
# Chat Endpoint Tests
# -----------------------------------------------------------------------------


class TestChatEndpoint:
    """Tests for POST /api/v1/agents/{id}/chat endpoint."""

    def test_chat_with_unknown_agent_returns_404(self, test_client):
        """Test chatting with unknown agent returns 404."""
        response = test_client.post(
            "/api/v1/agents/unknown_agent/chat",
            json={"message": "Hello", "session_id": "test-session"},
        )
        assert response.status_code == 404

    def test_chat_requires_message(self, test_client):
        """Test chat requires message field."""
        response = test_client.post(
            "/api/v1/agents/math/chat",
            json={"session_id": "test-session"},
        )
        assert response.status_code == 422  # Validation error

    def test_chat_with_math_agent_returns_200(self, test_client, mock_db_manager):
        """Test chat with math agent returns 200."""
        # Mock the agent's run_with_hitl method
        with patch("agents.base.BaseAgent.run_with_hitl") as mock_run:
            from agents.base import CompletedResult

            mock_run.return_value = CompletedResult(response="The result is 8")

            response = test_client.post(
                "/api/v1/agents/math/chat",
                json={"message": "What is 5 + 3?", "session_id": "test-session"},
            )

        assert response.status_code == 200

    def test_chat_response_has_required_fields(self, test_client, mock_db_manager):
        """Test chat response has required fields."""
        with patch("agents.base.BaseAgent.run_with_hitl") as mock_run:
            from agents.base import CompletedResult

            mock_run.return_value = CompletedResult(response="Test response")

            response = test_client.post(
                "/api/v1/agents/math/chat",
                json={"message": "Hello", "session_id": "test-session"},
            )

        data = response.json()
        assert "response" in data or "status" in data


# -----------------------------------------------------------------------------
# Stream Endpoint Tests
# -----------------------------------------------------------------------------


class TestStreamEndpoint:
    """Tests for POST /api/v1/agents/{id}/chat/stream endpoint."""

    def test_stream_with_unknown_agent_returns_404(self, test_client):
        """Test streaming with unknown agent returns 404."""
        response = test_client.post(
            "/api/v1/agents/unknown_agent/chat/stream",
            json={"message": "Hello", "session_id": "test-session"},
        )
        assert response.status_code == 404

    def test_stream_requires_message(self, test_client):
        """Test stream requires message field."""
        response = test_client.post(
            "/api/v1/agents/math/chat/stream",
            json={"session_id": "test-session"},
        )
        assert response.status_code == 422


# -----------------------------------------------------------------------------
# Session Management Tests
# -----------------------------------------------------------------------------


class TestSessionManagement:
    """Tests for session management endpoints."""

    def test_clear_session_with_unknown_agent_returns_404(self, test_client):
        """Test clearing session for unknown agent returns 404."""
        response = test_client.delete("/api/v1/agents/unknown_agent/session/test-123")
        assert response.status_code == 404

    def test_clear_session_returns_200(self, test_client, mock_db_manager):
        """Test clearing session returns 200."""
        response = test_client.delete("/api/v1/agents/math/session/test-123")
        assert response.status_code == 200

    def test_clear_session_response_has_fields(self, test_client, mock_db_manager):
        """Test clear session response has required fields."""
        response = test_client.delete("/api/v1/agents/math/session/test-123")
        data = response.json()

        assert "cleared" in data
        assert "session_id" in data


# -----------------------------------------------------------------------------
# HITL Respond Endpoint Tests
# -----------------------------------------------------------------------------


class TestHITLRespondEndpoint:
    """Tests for POST /api/v1/agents/{id}/chat/respond endpoint."""

    def test_respond_with_unknown_agent_returns_404(self, test_client):
        """Test responding to unknown agent returns 404."""
        response = test_client.post(
            "/api/v1/agents/unknown_agent/chat/respond",
            json={"workflow_id": "test-workflow", "response": "yes"},
        )
        assert response.status_code == 404

    def test_respond_requires_workflow_id(self, test_client):
        """Test respond requires workflow_id field."""
        response = test_client.post(
            "/api/v1/agents/math/chat/respond",
            json={"response": "yes"},
        )
        assert response.status_code == 422

    def test_respond_requires_response(self, test_client):
        """Test respond requires response field."""
        response = test_client.post(
            "/api/v1/agents/math/chat/respond",
            json={"workflow_id": "test-workflow"},
        )
        assert response.status_code == 422

    def test_respond_with_missing_workflow_returns_404(
        self, test_client, mock_db_manager
    ):
        """Test responding to non-existent workflow returns 404."""
        # mock_db_manager.get_workflow_state returns None by default
        response = test_client.post(
            "/api/v1/agents/math/chat/respond",
            json={"workflow_id": "non-existent", "response": "yes"},
        )
        assert response.status_code == 404


# -----------------------------------------------------------------------------
# Health Check Tests
# -----------------------------------------------------------------------------


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, test_client):
        """Test health check returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy(self, test_client):
        """Test health check returns healthy status."""
        response = test_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
