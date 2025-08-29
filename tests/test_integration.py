"""
End-to-end integration tests for the multi-agent system.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from web.app import create_app
from utils.session import SessionManager, create_agent_team
from utils.streaming import StreamingManager
from utils.security import CodeSafetyScanner, InputValidator
from models.config import CodeGenerationRequest


@pytest.fixture
def app():
    """Create a test Flask application."""
    return create_app(testing=True)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.mark.asyncio
async def test_session_manager_lifecycle():
    """Test complete session lifecycle."""
    session_manager = SessionManager()
    
    # Mock agent team
    mock_team = AsyncMock()
    
    # Create test request
    request = CodeGenerationRequest(
        requirements="Create a simple calculator function",
        language="python"
    )
    
    session_id = "test_session_123"
    
    # Test session creation
    session_manager.create_session(session_id, mock_team, request)
    
    # Test session retrieval
    session_data = session_manager.get_session(session_id)
    assert session_data is not None
    assert session_data["status"] == "created"
    assert session_data["active"] is True
    
    # Test status update
    session_manager.update_session_status(session_id, "running")
    session_data = session_manager.get_session(session_id)
    assert session_data["status"] == "running"
    
    # Test non-existent session
    assert session_manager.get_session("nonexistent") is None


@pytest.mark.asyncio 
async def test_streaming_manager_functionality():
    """Test streaming manager message handling."""
    streaming_manager = StreamingManager()
    
    session_id = "test_stream_session"
    
    # Create stream
    stream = streaming_manager.create_stream(session_id)
    assert stream is not None
    
    # Test message sending
    test_message = {
        "type": "agent_message",
        "agent": "code_generator",
        "message": "Starting code generation..."
    }
    
    success = streaming_manager.send_message(session_id, test_message)
    assert success is True
    
    # Test message retrieval
    retrieved_stream = streaming_manager.get_stream(session_id)
    assert retrieved_stream is not None
    
    # Test stream closure
    streaming_manager.close_stream(session_id)
    
    # Stream should no longer exist
    assert streaming_manager.get_stream(session_id) is None


def test_security_scanner_code_analysis():
    """Test security scanner with various code samples."""
    scanner = CodeSafetyScanner()
    
    # Test safe code
    safe_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    
print(fibonacci(10))
"""
    result = scanner.scan_code(safe_code, "python")
    assert result["safety_level"] == "SAFE"
    assert result["risk_score"] == 0
    
    # Test potentially dangerous code
    dangerous_code = """
import os
import subprocess

def delete_files():
    os.system("rm -rf /")
    subprocess.run(["rm", "-rf", "/home"])
"""
    result = scanner.scan_code(dangerous_code, "python")
    assert result["safety_level"] in ["DANGEROUS", "MODERATE_RISK"]
    assert result["risk_score"] > 0
    assert len(result["risks"]) > 0
    
    # Test network operations
    network_code = """
import requests
import socket

def fetch_data():
    response = requests.get("https://api.example.com/data")
    return response.json()
"""
    result = scanner.scan_code(network_code, "python")
    assert result["risk_score"] > 0
    
    # Test non-Python code
    js_code = """
function deleteFile(filename) {
    system('rm ' + filename);
    exec('del ' + filename);
}
"""
    result = scanner.scan_code(js_code, "javascript")
    assert result["language"] == "javascript"


def test_input_validator():
    """Test input validation functionality."""
    # Test valid requirements
    valid_req = "Create a function to sort a list of numbers in ascending order"
    result = InputValidator.validate_code_requirements(valid_req)
    assert result["is_valid"] is True
    assert len(result["issues"]) == 0
    
    # Test suspicious requirements
    suspicious_req = "Create a function to hack into a system and steal passwords"
    result = InputValidator.validate_code_requirements(suspicious_req)
    assert result["is_valid"] is False
    assert len(result["issues"]) > 0
    
    # Test too short requirements
    short_req = "Sort"
    result = InputValidator.validate_code_requirements(short_req)
    assert result["is_valid"] is False
    
    # Test input sanitization
    dirty_input = "<script>alert('xss')</script>Sort a list"
    clean_input = InputValidator.sanitize_input(dirty_input)
    assert "<script>" not in clean_input
    assert "Sort a list" in clean_input


@pytest.mark.asyncio
@patch('utils.session.get_model_manager')
@patch('utils.session.create_code_generator')
@patch('utils.session.create_quality_checker')
@patch('utils.session.create_code_optimizer')
@patch('utils.session.create_user_proxy')
async def test_agent_team_creation(mock_user_proxy, mock_optimizer, mock_checker, 
                                  mock_generator, mock_model_manager):
    """Test agent team creation with mocked dependencies."""
    # Mock model manager
    mock_manager = AsyncMock()
    mock_client = AsyncMock()
    mock_manager.get_client_with_fallback.return_value = mock_client
    mock_model_manager.return_value = mock_manager
    
    # Mock agent creation
    mock_generator.return_value = AsyncMock(name="code_generator")
    mock_checker.return_value = AsyncMock(name="quality_checker")
    mock_optimizer.return_value = AsyncMock(name="code_optimizer")
    mock_user_proxy.return_value = AsyncMock(name="user_proxy")
    
    # Mock RoundRobinGroupChat
    with patch('utils.session.RoundRobinGroupChat') as mock_team_class:
        mock_team = AsyncMock()
        mock_team_class.return_value = mock_team
        
        # Test team creation
        team = await create_agent_team("test_session", "python")
        
        # Verify team was created
        assert team == mock_team
        mock_team_class.assert_called_once()
        
        # Verify agents were created
        mock_generator.assert_called_once()
        mock_checker.assert_called_once()
        mock_optimizer.assert_called_once()
        mock_user_proxy.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling_in_workflow():
    """Test error handling throughout the workflow."""
    # Test model manager error handling
    with patch('models.providers.ModelProviderManager') as mock_manager_class:
        mock_manager = AsyncMock()
        mock_manager.get_client_with_fallback.side_effect = RuntimeError("All models failed")
        mock_manager_class.return_value = mock_manager
        
        # Test that error is handled gracefully
        with pytest.raises(RuntimeError):
            await create_agent_team("test_session", "python")


def test_configuration_loading_integration():
    """Test that configuration loading works end-to-end."""
    from models.config import ConfigLoader
    
    mock_models_data = {
        "models": {
            "test_model": {
                "provider": "test.provider",
                "config": {"model": "test", "api_key": "${TEST_API_KEY}"}
            }
        }
    }
    
    mock_agents_data = {
        "agents": {
            "test_agent": {
                "system_prompt": "You are a test agent",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }
    }
    
    with patch('builtins.open'), \
         patch('yaml.safe_load', side_effect=[mock_models_data, mock_agents_data]), \
         patch.dict('os.environ', {'TEST_API_KEY': 'secret-key'}):
        
        loader = ConfigLoader()
        
        # Test full configuration loading
        models = loader.load_models_config()
        agents = loader.load_agents_config()
        
        assert len(models) == 1
        assert len(agents) == 1
        
        # Test environment variable substitution
        model_config = loader.get_model_config("test_model")
        client_config = model_config.get_client_config()
        assert client_config["config"]["api_key"] == "secret-key"


@pytest.mark.asyncio
async def test_full_request_lifecycle(client):
    """Test a complete request from API to response."""
    with patch('web.routes.create_agent_team') as mock_create_team, \
         patch('web.routes.session_manager') as mock_session_manager, \
         patch('web.routes.streaming_manager') as mock_streaming_manager, \
         patch('web.routes._process_generation_request') as mock_process:
        
        # Setup mocks
        mock_team = AsyncMock()
        mock_create_team.return_value = mock_team
        mock_session_manager.create_session = MagicMock()
        mock_streaming_manager.create_stream = MagicMock()
        mock_process.return_value = None
        
        # Make request
        request_data = {
            "requirements": "Create a function to calculate prime numbers",
            "language": "python",
            "max_iterations": 3
        }
        
        response = client.post('/api/generate',
                              json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert 'session_id' in data
        assert data['status'] == 'started'
        
        # Verify mocks were called
        mock_create_team.assert_called_once()
        mock_session_manager.create_session.assert_called_once()
        mock_streaming_manager.create_stream.assert_called_once()


def test_concurrent_sessions():
    """Test handling of multiple concurrent sessions."""
    session_manager = SessionManager()
    streaming_manager = StreamingManager()
    
    # Create multiple sessions
    session_ids = ["session_1", "session_2", "session_3"]
    
    for session_id in session_ids:
        # Mock team and request
        mock_team = AsyncMock()
        request = CodeGenerationRequest(
            requirements=f"Test requirements for {session_id}",
            language="python"
        )
        
        # Create session and stream
        session_manager.create_session(session_id, mock_team, request)
        streaming_manager.create_stream(session_id)
    
    # Verify all sessions exist
    for session_id in session_ids:
        assert session_manager.get_session(session_id) is not None
        assert streaming_manager.get_stream(session_id) is not None
    
    # Test cleanup
    for session_id in session_ids:
        streaming_manager.close_stream(session_id)
        assert streaming_manager.get_stream(session_id) is None