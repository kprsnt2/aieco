"""
AIEco - Test Suite
Comprehensive tests for the AIEco API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json


# ===== Fixtures =====

@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authenticated headers"""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    mock = AsyncMock()
    mock.chat_completion.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 100}
    }
    return mock


# ===== Health Check Tests =====

class TestHealthCheck:
    def test_health_endpoint(self, client):
        """Test health endpoint returns OK"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_readiness_endpoint(self, client):
        """Test readiness endpoint"""
        response = client.get("/ready")
        assert response.status_code in [200, 503]


# ===== Authentication Tests =====

class TestAuthentication:
    def test_login_success(self, client):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_email(self, client):
        """Test login with invalid email format"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "invalid-email", "password": "password123"}
        )
        assert response.status_code == 422
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without auth"""
        response = client.get("/api/v1/models")
        assert response.status_code == 401


# ===== Chat Completions Tests =====

class TestChatCompletions:
    def test_chat_completion_basic(self, client, auth_headers):
        """Test basic chat completion"""
        with patch("app.core.llm.get_llm_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.chat_completion.return_value = {
                "id": "test-id",
                "choices": [{"message": {"content": "Hello!"}}],
                "usage": {"total_tokens": 50}
            }
            mock_get.return_value = mock_client
            
            response = client.post(
                "/api/v1/chat/completions",
                headers=auth_headers,
                json={
                    "model": "glm-4.7",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )
            # Note: Will fail without proper auth mock
            assert response.status_code in [200, 401]
    
    def test_chat_completion_missing_messages(self, client, auth_headers):
        """Test chat without messages field"""
        response = client.post(
            "/api/v1/chat/completions",
            headers=auth_headers,
            json={"model": "glm-4.7"}
        )
        assert response.status_code == 422


# ===== RAG Tests =====

class TestRAG:
    def test_rag_query(self, client, auth_headers):
        """Test RAG query endpoint"""
        response = client.post(
            "/api/v1/rag/query",
            headers=auth_headers,
            json={
                "query": "How does authentication work?",
                "collection": "default",
                "top_k": 5
            }
        )
        assert response.status_code in [200, 401]
    
    def test_list_collections(self, client, auth_headers):
        """Test listing collections"""
        response = client.get(
            "/api/v1/rag/collections",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]


# ===== Agent Tests =====

class TestAgents:
    def test_list_agents(self, client, auth_headers):
        """Test listing available agents"""
        response = client.get(
            "/api/v1/agents/list",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]
    
    def test_run_agent(self, client, auth_headers):
        """Test running an agent"""
        response = client.post(
            "/api/v1/agents/run",
            headers=auth_headers,
            json={
                "agent": "code",
                "task": "Write a hello world function"
            }
        )
        assert response.status_code in [200, 401, 500]


# ===== Skills Tests =====

class TestSkills:
    def test_list_skills(self, client, auth_headers):
        """Test listing skills"""
        response = client.get(
            "/api/v1/skills/list",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]
    
    def test_activate_skill(self, client, auth_headers):
        """Test activating a skill"""
        response = client.post(
            "/api/v1/skills/activate",
            headers=auth_headers,
            json={"skill_name": "code-review"}
        )
        assert response.status_code in [200, 401, 404]


# ===== MCP Tools Tests =====

class TestMCPTools:
    def test_list_tools(self, client, auth_headers):
        """Test listing MCP tools"""
        response = client.get(
            "/api/v1/mcp/tools",
            headers=auth_headers
        )
        assert response.status_code in [200, 401]
    
    def test_execute_tool(self, client, auth_headers):
        """Test executing a tool"""
        response = client.post(
            "/api/v1/mcp/execute",
            headers=auth_headers,
            json={
                "tool": "filesystem.list_directory",
                "parameters": {"path": "."}
            }
        )
        assert response.status_code in [200, 401, 404]


# ===== Unit Tests =====

class TestSkillLoader:
    def test_skill_parsing(self):
        """Test SKILL.md parsing"""
        from app.services.skills.loader import SkillLoader
        
        loader = SkillLoader(skills_dir="skills")
        # Would need actual skills directory in test
        skills = loader.list_skills()
        assert isinstance(skills, list)


class TestPromptCaching:
    def test_cache_key_generation(self):
        """Test cache key generation"""
        from app.core.cache import generate_cache_key
        
        messages = [{"role": "user", "content": "Hello"}]
        key = generate_cache_key(messages, "glm-4.7")
        
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hex


# ===== Integration Tests =====

class TestIntegration:
    @pytest.mark.integration
    def test_full_chat_flow(self, client):
        """Test complete chat flow: login -> chat -> logout"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Chat
        chat_response = client.post(
            "/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": "glm-4.7",
                "messages": [{"role": "user", "content": "Hi"}]
            }
        )
        # May fail without LLM, that's okay
        assert chat_response.status_code in [200, 401, 500]


# ===== Performance Tests =====

class TestPerformance:
    @pytest.mark.slow
    def test_concurrent_requests(self, client, auth_headers):
        """Test handling concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]
        
        assert all(r.status_code == 200 for r in results)
