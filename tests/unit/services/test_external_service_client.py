"""Comprehensive tests for ExternalServiceClient."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import httpx
import openai

from src.services.external_service_client import ExternalServiceClient
from src.utils.circuit_breaker import CircuitBreakerError


class TestExternalServiceClient:
    """Test ExternalServiceClient functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.openai.api_key = "test-api-key"
        return settings

    @pytest.fixture
    def client(self, mock_settings):
        """Create ExternalServiceClient instance."""
        with patch('src.services.external_service_client.openai.Client'):
            with patch('src.services.external_service_client.httpx.AsyncClient'):
                return ExternalServiceClient(mock_settings)

    def test_initialization(self, mock_settings):
        """Test client initialization."""
        with patch('src.services.external_service_client.openai.Client') as mock_openai:
            with patch('src.services.external_service_client.httpx.AsyncClient') as mock_httpx:
                client = ExternalServiceClient(mock_settings)
                
                assert client.settings == mock_settings
                mock_openai.assert_called_once_with(api_key="test-api-key")
                mock_httpx.assert_called_once_with(timeout=30.0)

    @patch('src.services.external_service_client.protect_external_service')
    def test_generate_code_with_openai_success(self, mock_protect, client):
        """Test successful OpenAI code generation."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'openai_client') as mock_openai_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "def test_function():\n    return 'Hello World'"
            mock_openai_client.chat.completions.create.return_value = mock_response
            
            result = client.generate_code_with_openai("Write a test function")
            
            assert "def test_function()" in result
            mock_openai_client.chat.completions.create.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_generate_code_with_openai_failure(self, mock_protect, client):
        """Test OpenAI code generation failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'openai_client') as mock_openai_client:
            mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
            
            with pytest.raises(Exception, match="API Error"):
                client.generate_code_with_openai("Write a test function")

    @patch('src.services.external_service_client.protect_external_service_async')
    @pytest.mark.asyncio
    async def test_generate_code_with_openai_async_success(self, mock_protect, client):
        """Test successful async OpenAI code generation."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'openai_client') as mock_openai_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "async def test_function():\n    return 'Hello World'"
            mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            result = await client.generate_code_with_openai_async("Write an async test function")
            
            assert "async def test_function()" in result
            mock_openai_client.chat.completions.create.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service_async')
    @pytest.mark.asyncio
    async def test_generate_code_with_openai_async_failure(self, mock_protect, client):
        """Test async OpenAI code generation failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'openai_client') as mock_openai_client:
            mock_openai_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception, match="API Error"):
                await client.generate_code_with_openai_async("Write an async test function")

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_pr_success(self, mock_protect, client):
        """Test successful GitHub PR creation."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "html_url": "https://github.com/test/repo/pull/1",
                "number": 1,
                "title": "Test PR"
            }
            mock_http.post.return_value = mock_response
            
            result = client.create_github_pr(
                title="Test PR",
                body="Test description",
                head="feature-branch",
                base="main",
                repo="test/repo"
            )
            
            assert result["html_url"] == "https://github.com/test/repo/pull/1"
            assert result["number"] == 1
            mock_http.post.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_pr_failure(self, mock_protect, client):
        """Test GitHub PR creation failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Bad Request"}
            mock_http.post.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to create PR"):
                client.create_github_pr(
                    title="Test PR",
                    body="Test description",
                    head="feature-branch",
                    base="main",
                    repo="test/repo"
                )

    @patch('src.services.external_service_client.protect_external_service')
    def test_list_github_repositories_success(self, mock_protect, client):
        """Test successful GitHub repository listing."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"name": "repo1", "full_name": "test/repo1"},
                {"name": "repo2", "full_name": "test/repo2"}
            ]
            mock_http.get.return_value = mock_response
            
            result = client.list_github_repositories("testuser")
            
            assert len(result) == 2
            assert result[0]["name"] == "repo1"
            assert result[1]["name"] == "repo2"
            mock_http.get.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_list_github_repositories_failure(self, mock_protect, client):
        """Test GitHub repository listing failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to list repositories"):
                client.list_github_repositories("testuser")

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_repository_success(self, mock_protect, client):
        """Test successful GitHub repository retrieval."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "test-repo",
                "full_name": "test/test-repo",
                "description": "Test repository",
                "private": False
            }
            mock_http.get.return_value = mock_response
            
            result = client.get_github_repository("test/test-repo")
            
            assert result["name"] == "test-repo"
            assert result["full_name"] == "test/test-repo"
            assert result["private"] is False
            mock_http.get.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_repository_failure(self, mock_protect, client):
        """Test GitHub repository retrieval failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to get repository"):
                client.get_github_repository("test/nonexistent-repo")

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_issue_success(self, mock_protect, client):
        """Test successful GitHub issue creation."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "html_url": "https://github.com/test/repo/issues/1",
                "number": 1,
                "title": "Test Issue"
            }
            mock_http.post.return_value = mock_response
            
            result = client.create_github_issue(
                title="Test Issue",
                body="Test issue description",
                repo="test/repo"
            )
            
            assert result["html_url"] == "https://github.com/test/repo/issues/1"
            assert result["number"] == 1
            mock_http.post.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_issue_failure(self, mock_protect, client):
        """Test GitHub issue creation failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"message": "Bad Request"}
            mock_http.post.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to create issue"):
                client.create_github_issue(
                    title="Test Issue",
                    body="Test issue description",
                    repo="test/repo"
                )

    @patch('src.services.external_service_client.protect_external_service')
    def test_search_github_repositories_success(self, mock_protect, client):
        """Test successful GitHub repository search."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "total_count": 2,
                "items": [
                    {"name": "repo1", "full_name": "test/repo1"},
                    {"name": "repo2", "full_name": "test/repo2"}
                ]
            }
            mock_http.get.return_value = mock_response
            
            result = client.search_github_repositories("test query")
            
            assert result["total_count"] == 2
            assert len(result["items"]) == 2
            assert result["items"][0]["name"] == "repo1"
            mock_http.get.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_search_github_repositories_failure(self, mock_protect, client):
        """Test GitHub repository search failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.json.return_value = {"message": "Validation Failed"}
            mock_http.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to search repositories"):
                client.search_github_repositories("invalid query")

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_user_success(self, mock_protect, client):
        """Test successful GitHub user retrieval."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "login": "testuser",
                "name": "Test User",
                "email": "test@example.com",
                "public_repos": 10
            }
            mock_http.get.return_value = mock_response
            
            result = client.get_github_user("testuser")
            
            assert result["login"] == "testuser"
            assert result["name"] == "Test User"
            assert result["public_repos"] == 10
            mock_http.get.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_user_failure(self, mock_protect, client):
        """Test GitHub user retrieval failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to get user"):
                client.get_github_user("nonexistentuser")

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_commit_success(self, mock_protect, client):
        """Test successful GitHub commit retrieval."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "sha": "abc123",
                "commit": {
                    "message": "Test commit",
                    "author": {"name": "Test Author"}
                }
            }
            mock_http.get.return_value = mock_response
            
            result = client.get_github_commit("test/repo", "abc123")
            
            assert result["sha"] == "abc123"
            assert result["commit"]["message"] == "Test commit"
            mock_http.get.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_commit_failure(self, mock_protect, client):
        """Test GitHub commit retrieval failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to get commit"):
                client.get_github_commit("test/repo", "invalid-sha")

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_branch_success(self, mock_protect, client):
        """Test successful GitHub branch retrieval."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "main",
                "commit": {"sha": "abc123"},
                "protected": True
            }
            mock_http.get.return_value = mock_response
            
            result = client.get_github_branch("test/repo", "main")
            
            assert result["name"] == "main"
            assert result["commit"]["sha"] == "abc123"
            assert result["protected"] is True
            mock_http.get.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_branch_failure(self, mock_protect, client):
        """Test GitHub branch retrieval failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to get branch"):
                client.get_github_branch("test/repo", "nonexistent-branch")

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_branch_success(self, mock_protect, client):
        """Test successful GitHub branch creation."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "ref": "refs/heads/feature-branch",
                "object": {"sha": "abc123"}
            }
            mock_http.post.return_value = mock_response
            
            result = client.create_github_branch("test/repo", "feature-branch", "abc123")
            
            assert result["ref"] == "refs/heads/feature-branch"
            assert result["object"]["sha"] == "abc123"
            mock_http.post.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_branch_failure(self, mock_protect, client):
        """Test GitHub branch creation failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.json.return_value = {"message": "Validation Failed"}
            mock_http.post.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to create branch"):
                client.create_github_branch("test/repo", "feature-branch", "invalid-sha")

    @patch('src.services.external_service_client.protect_external_service')
    def test_delete_github_branch_success(self, mock_protect, client):
        """Test successful GitHub branch deletion."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 204
            mock_http.delete.return_value = mock_response
            
            result = client.delete_github_branch("test/repo", "feature-branch")
            
            assert result is True
            mock_http.delete.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_delete_github_branch_failure(self, mock_protect, client):
        """Test GitHub branch deletion failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.delete.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to delete branch"):
                client.delete_github_branch("test/repo", "nonexistent-branch")

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_file_success(self, mock_protect, client):
        """Test successful GitHub file retrieval."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "README.md",
                "path": "README.md",
                "content": "SGVsbG8gV29ybGQ=",  # Base64 encoded "Hello World"
                "encoding": "base64"
            }
            mock_http.get.return_value = mock_response
            
            result = client.get_github_file("test/repo", "README.md")
            
            assert result["name"] == "README.md"
            assert result["path"] == "README.md"
            assert result["encoding"] == "base64"
            mock_http.get.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_get_github_file_failure(self, mock_protect, client):
        """Test GitHub file retrieval failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.get.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to get file"):
                client.get_github_file("test/repo", "nonexistent-file.txt")

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_file_success(self, mock_protect, client):
        """Test successful GitHub file creation."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "content": {"name": "new-file.txt"},
                "commit": {"sha": "abc123"}
            }
            mock_http.put.return_value = mock_response
            
            result = client.create_github_file(
                "test/repo",
                "new-file.txt",
                "Hello World",
                "Add new file"
            )
            
            assert result["content"]["name"] == "new-file.txt"
            assert result["commit"]["sha"] == "abc123"
            mock_http.put.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_create_github_file_failure(self, mock_protect, client):
        """Test GitHub file creation failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 409
            mock_response.json.return_value = {"message": "Conflict"}
            mock_http.put.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to create file"):
                client.create_github_file(
                    "test/repo",
                    "existing-file.txt",
                    "Hello World",
                    "Add new file"
                )

    @patch('src.services.external_service_client.protect_external_service')
    def test_update_github_file_success(self, mock_protect, client):
        """Test successful GitHub file update."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": {"name": "updated-file.txt"},
                "commit": {"sha": "def456"}
            }
            mock_http.put.return_value = mock_response
            
            result = client.update_github_file(
                "test/repo",
                "updated-file.txt",
                "Updated content",
                "Update file",
                "abc123"
            )
            
            assert result["content"]["name"] == "updated-file.txt"
            assert result["commit"]["sha"] == "def456"
            mock_http.put.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_update_github_file_failure(self, mock_protect, client):
        """Test GitHub file update failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 412
            mock_response.json.return_value = {"message": "Precondition Failed"}
            mock_http.put.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to update file"):
                client.update_github_file(
                    "test/repo",
                    "file.txt",
                    "Updated content",
                    "Update file",
                    "invalid-sha"
                )

    @patch('src.services.external_service_client.protect_external_service')
    def test_delete_github_file_success(self, mock_protect, client):
        """Test successful GitHub file deletion."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": None,
                "commit": {"sha": "def456"}
            }
            mock_http.delete.return_value = mock_response
            
            result = client.delete_github_file(
                "test/repo",
                "file-to-delete.txt",
                "Delete file",
                "abc123"
            )
            
            assert result["content"] is None
            assert result["commit"]["sha"] == "def456"
            mock_http.delete.assert_called_once()

    @patch('src.services.external_service_client.protect_external_service')
    def test_delete_github_file_failure(self, mock_protect, client):
        """Test GitHub file deletion failure."""
        mock_protect.return_value = lambda func: func
        
        with patch.object(client, 'http_client') as mock_http:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not Found"}
            mock_http.delete.return_value = mock_response
            
            with pytest.raises(Exception, match="Failed to delete file"):
                client.delete_github_file(
                    "test/repo",
                    "nonexistent-file.txt",
                    "Delete file",
                    "abc123"
                )

    def test_close(self, client):
        """Test client cleanup."""
        with patch.object(client, 'http_client') as mock_http:
            client.close()
            mock_http.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_aclose(self, client):
        """Test async client cleanup."""
        with patch.object(client, 'http_client') as mock_http:
            mock_http.aclose = AsyncMock()
            await client.aclose()
            mock_http.aclose.assert_called_once()

    def test_context_manager(self, mock_settings):
        """Test client as context manager."""
        with patch('src.services.external_service_client.openai.Client'):
            with patch('src.services.external_service_client.httpx.AsyncClient') as mock_httpx:
                with ExternalServiceClient(mock_settings) as client:
                    assert isinstance(client, ExternalServiceClient)
                mock_httpx.return_value.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_settings):
        """Test client as async context manager."""
        with patch('src.services.external_service_client.openai.Client'):
            with patch('src.services.external_service_client.httpx.AsyncClient') as mock_httpx:
                mock_httpx.return_value.aclose = AsyncMock()
                async with ExternalServiceClient(mock_settings) as client:
                    assert isinstance(client, ExternalServiceClient)
                mock_httpx.return_value.aclose.assert_called_once()
