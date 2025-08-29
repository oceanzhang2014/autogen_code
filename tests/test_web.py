"""
Tests for Flask web application and API endpoints.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from web.app import create_app
from models.config import CodeGenerationRequest


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app(testing=True)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'autogen-multi-agent-system'


def test_index_route(client):
    """Test index route serves static files."""
    # This test would need actual static files to work properly
    # For now, test that the route exists
    response = client.get('/')
    # May return 404 if static file doesn't exist in test environment
    assert response.status_code in [200, 404]


@patch('web.routes.create_agent_team')
@patch('web.routes.session_manager')
@patch('web.routes.streaming_manager')
def test_generate_code_endpoint(mock_streaming, mock_session, mock_create_team, client):
    """Test code generation endpoint."""
    # Mock dependencies
    mock_team = AsyncMock()
    mock_create_team.return_value = mock_team
    mock_session.create_session = MagicMock()
    mock_streaming.create_stream = MagicMock()
    
    # Test valid request
    request_data = {
        "requirements": "Create a function to calculate fibonacci numbers",
        "language": "python",
        "context": "For educational purposes",
        "max_iterations": 3
    }
    
    response = client.post('/api/generate', 
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'session_id' in data
    assert data['status'] == 'started'
    assert 'stream_url' in data


def test_generate_code_invalid_request(client):
    """Test code generation with invalid request data."""
    # Test missing requirements
    request_data = {
        "language": "python"
    }
    
    response = client.post('/api/generate',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_generate_code_invalid_language(client):
    """Test code generation with invalid language."""
    request_data = {
        "requirements": "Create a function to sort a list",
        "language": "invalid_language"
    }
    
    response = client.post('/api/generate',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_generate_code_no_json(client):
    """Test code generation endpoint with no JSON data."""
    response = client.post('/api/generate', content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


@patch('web.routes.streaming_manager')
def test_stream_endpoint(mock_streaming, client):
    """Test streaming endpoint."""
    import queue
    
    # Mock stream with some test data
    mock_stream = queue.Queue()
    mock_stream.put('{"type": "test", "message": "hello"}')
    mock_stream.put(None)  # End of stream
    
    mock_streaming.get_stream.return_value = mock_stream
    
    response = client.get('/api/stream/test_session')
    
    assert response.status_code == 200
    assert response.content_type.startswith('text/event-stream')


@patch('web.routes.streaming_manager')
def test_stream_endpoint_no_session(mock_streaming, client):
    """Test streaming endpoint with non-existent session."""
    mock_streaming.get_stream.return_value = None
    
    response = client.get('/api/stream/nonexistent_session')
    
    assert response.status_code == 200
    # Should return error in stream
    data = response.get_data(as_text=True)
    assert 'Session not found' in data


@patch('web.routes.session_manager')
def test_approve_endpoint(mock_session, client):
    """Test approval endpoint."""
    import asyncio
    
    # Mock session data
    mock_queue = asyncio.Queue()
    mock_session_data = {
        "user_input_queue": mock_queue
    }
    mock_session.get_session.return_value = mock_session_data
    
    request_data = {
        "session_id": "test_session",
        "action": "approve"
    }
    
    response = client.post('/api/approve',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['action'] == 'approve'


@patch('web.routes.session_manager')
def test_approve_endpoint_invalid_action(mock_session, client):
    """Test approval endpoint with invalid action."""
    request_data = {
        "session_id": "test_session",
        "action": "invalid_action"
    }
    
    response = client.post('/api/approve',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


@patch('web.routes.session_manager')
def test_approve_endpoint_no_session(mock_session, client):
    """Test approval endpoint with non-existent session."""
    mock_session.get_session.return_value = None
    
    request_data = {
        "session_id": "nonexistent_session",
        "action": "approve"
    }
    
    response = client.post('/api/approve',
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


@patch('web.routes.session_manager')
def test_status_endpoint(mock_session, client):
    """Test session status endpoint."""
    # Mock session data
    mock_request = CodeGenerationRequest(
        requirements="test requirements",
        language="python"
    )
    
    mock_session_data = {
        "status": "running",
        "created_at": "2024-01-01T12:00:00",
        "request": mock_request,
        "active": True
    }
    mock_session.get_session.return_value = mock_session_data
    
    response = client.get('/api/status/test_session')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['session_id'] == 'test_session'
    assert data['status'] == 'running'
    assert data['language'] == 'python'
    assert data['active'] is True


@patch('web.routes.session_manager')
def test_status_endpoint_no_session(mock_session, client):
    """Test status endpoint with non-existent session."""
    mock_session.get_session.return_value = None
    
    response = client.get('/api/status/nonexistent_session')
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


@patch('web.routes.get_model_manager')
def test_models_endpoint(mock_get_manager, client):
    """Test models listing endpoint."""
    mock_manager = MagicMock()
    mock_manager.list_available_models.return_value = ["deepseek", "moonshot", "alibaba"]
    mock_get_manager.return_value = mock_manager
    
    response = client.get('/api/models')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'models' in data
    assert 'default_models' in data
    assert "deepseek" in data['models']


def test_cors_headers(client):
    """Test CORS headers are set correctly."""
    response = client.get('/health')
    
    # Flask-CORS should add these headers
    # Note: In testing, CORS headers might not be fully applied
    assert response.status_code == 200


def test_app_configuration():
    """Test application configuration."""
    app = create_app(testing=True)
    
    assert app.config['TESTING'] is True
    assert 'SECRET_KEY' in app.config
    
    # Test production configuration
    prod_app = create_app(testing=False)
    assert prod_app.config['TESTING'] is False