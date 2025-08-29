"""
Tests for agent creation and behavior.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.code_generator import create_code_generator
from agents.quality_checker import create_quality_checker
from agents.code_optimizer import create_code_optimizer
from agents.user_proxy import create_user_proxy


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    client = AsyncMock()
    client.model = "test-model"
    return client


@pytest.fixture
def mock_config_loader():
    """Create a mock configuration loader."""
    loader = MagicMock()
    loader.get_agent_config.return_value = MagicMock(
        system_prompt="Test system prompt",
        temperature=0.7,
        max_tokens=2000
    )
    return loader


@pytest.mark.asyncio
async def test_code_generator_creation(mock_model_client, mock_config_loader):
    """Test code generator agent creation and configuration."""
    agent = await create_code_generator(mock_model_client, mock_config_loader)
    
    assert agent.name == "code_generator"
    assert agent._model_client == mock_model_client
    assert agent._model_client_stream is True
    assert len(agent._system_messages) > 0


@pytest.mark.asyncio
async def test_quality_checker_creation(mock_model_client, mock_config_loader):
    """Test quality checker agent creation and configuration."""
    agent = await create_quality_checker(mock_model_client, mock_config_loader)
    
    assert agent.name == "quality_checker"
    assert agent._model_client == mock_model_client
    assert agent._model_client_stream is True


@pytest.mark.asyncio
async def test_code_optimizer_creation(mock_model_client, mock_config_loader):
    """Test code optimizer agent creation and configuration."""
    agent = await create_code_optimizer(mock_model_client, mock_config_loader)
    
    assert agent.name == "code_optimizer"
    assert agent._model_client == mock_model_client
    assert agent._model_client_stream is True


@pytest.mark.asyncio
async def test_user_proxy_creation():
    """Test user proxy agent creation."""
    session_id = "test_session_123"
    agent = await create_user_proxy(session_id)
    
    assert agent.name == "user_proxy"
    assert agent.session_id == session_id
    assert agent.input_queue is not None


@pytest.mark.asyncio
async def test_user_proxy_input_handling():
    """Test user proxy input handling."""
    import asyncio
    
    session_id = "test_session_123"
    input_queue = asyncio.Queue()
    agent = await create_user_proxy(session_id, input_queue)
    
    # Test input handling
    prompt = "Please approve the code"
    
    # Simulate user input
    user_response = {
        "type": "user_input",
        "content": "APPROVE",
        "session_id": session_id
    }
    
    # Start input function
    input_task = asyncio.create_task(agent._web_input_func(prompt))
    
    # Simulate delay then provide input
    await asyncio.sleep(0.1)
    await input_queue.put(user_response)
    
    # Get result
    result = await input_task
    assert result == "APPROVE"


@pytest.mark.asyncio
async def test_user_proxy_timeout():
    """Test user proxy timeout handling."""
    import asyncio
    
    session_id = "test_session_123"
    agent = await create_user_proxy(session_id)
    
    # Mock the timeout behavior directly
    with patch.object(agent, '_web_input_func') as mock_func:
        mock_func.return_value = "User did not provide input within the time limit"
        result = await agent._web_input_func("test prompt")
        assert "time limit" in result


@pytest.mark.asyncio
async def test_agent_configuration_loading():
    """Test agent configuration loading from files."""
    with patch('models.config.ConfigLoader') as mock_loader_class:
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        
        # Mock configuration
        mock_config = MagicMock()
        mock_config.system_prompt = "Test prompt for code generation"
        mock_config.temperature = 0.8
        mock_config.max_tokens = 1500
        mock_loader.get_agent_config.return_value = mock_config
        
        mock_client = AsyncMock()
        
        # Test agent creation with configuration
        agent = await create_code_generator(mock_client, mock_loader)
        
        # Verify configuration was loaded
        mock_loader.get_agent_config.assert_called_once_with("code_generator")
        assert len(agent._system_messages) > 0


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test agent creation error handling."""
    with patch('models.config.ConfigLoader') as mock_loader_class:
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader
        mock_loader.get_agent_config.side_effect = Exception("Config error")
        
        mock_client = AsyncMock()
        
        # Test that error is propagated
        with pytest.raises(Exception) as exc_info:
            await create_code_generator(mock_client, mock_loader)
        
        assert "Config error" in str(exc_info.value)