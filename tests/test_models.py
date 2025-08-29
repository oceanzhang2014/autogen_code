"""
Tests for model provider configuration and management.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from models.config import ModelConfig, AgentConfig, CodeGenerationRequest, ConfigLoader
from models.providers import ModelProviderManager, get_model_manager
from pydantic import ValidationError


def test_model_config_validation():
    """Test model configuration validation."""
    # Valid configuration
    config = ModelConfig(
        provider="autogen_ext.models.openai.OpenAIChatCompletionClient",
        config={"model": "gpt-4", "api_key": "test-key"}
    )
    assert config.provider == "autogen_ext.models.openai.OpenAIChatCompletionClient"
    assert config.config["model"] == "gpt-4"


def test_model_config_environment_substitution():
    """Test environment variable substitution in model config."""
    config = ModelConfig(
        provider="test.provider",
        config={"api_key": "${TEST_API_KEY}", "base_url": "${TEST_URL:-http://default.com}"}
    )
    
    with patch.dict('os.environ', {'TEST_API_KEY': 'secret-key'}):
        client_config = config.get_client_config()
        assert client_config["config"]["api_key"] == "secret-key"
        assert client_config["config"]["base_url"] == "http://default.com"


def test_agent_config_validation():
    """Test agent configuration validation."""
    # Valid configuration
    config = AgentConfig(
        system_prompt="You are a helpful assistant",
        temperature=0.7,
        max_tokens=2000
    )
    assert config.temperature == 0.7
    assert config.max_tokens == 2000
    
    # Invalid temperature
    with pytest.raises(ValidationError):
        AgentConfig(system_prompt="Test", temperature=3.0)
    
    # Invalid max_tokens
    with pytest.raises(ValidationError):
        AgentConfig(system_prompt="Test", max_tokens=-1)


def test_code_generation_request_validation():
    """Test code generation request validation."""
    # Valid request
    request = CodeGenerationRequest(
        requirements="Create a function to sort a list",
        language="python"
    )
    assert request.language == "python"
    assert request.max_iterations == 3  # default
    
    # Invalid language
    with pytest.raises(ValidationError):
        CodeGenerationRequest(
            requirements="Test",
            language="invalid_language"
        )
    
    # Requirements too short
    with pytest.raises(ValidationError):
        CodeGenerationRequest(
            requirements="Short",
            language="python"
        )


def test_config_loader():
    """Test configuration loader functionality."""
    mock_models_data = {
        "models": {
            "test_model": {
                "provider": "test.provider",
                "config": {"model": "test", "api_key": "test-key"}
            }
        }
    }
    
    mock_agents_data = {
        "agents": {
            "test_agent": {
                "system_prompt": "Test prompt",
                "temperature": 0.5,
                "max_tokens": 1000
            }
        }
    }
    
    with patch('builtins.open'), \
         patch('yaml.safe_load', side_effect=[mock_models_data, mock_agents_data]):
        
        loader = ConfigLoader()
        
        # Test model loading
        models = loader.load_models_config()
        assert "test_model" in models
        assert isinstance(models["test_model"], ModelConfig)
        
        # Test agent loading
        agents = loader.load_agents_config()
        assert "test_agent" in agents
        assert isinstance(agents["test_agent"], AgentConfig)
        
        # Test specific config retrieval
        model_config = loader.get_model_config("test_model")
        assert model_config.provider == "test.provider"
        
        agent_config = loader.get_agent_config("test_agent")
        assert agent_config.system_prompt == "Test prompt"


def test_config_loader_error_handling():
    """Test configuration loader error handling."""
    loader = ConfigLoader()
    
    # Test missing model
    with patch.object(loader, 'load_models_config', return_value={}):
        with pytest.raises(ValueError, match="Model.*not found"):
            loader.get_model_config("nonexistent_model")
    
    # Test missing agent
    with patch.object(loader, 'load_agents_config', return_value={}):
        with pytest.raises(ValueError, match="Agent.*not found"):
            loader.get_agent_config("nonexistent_agent")


@pytest.mark.asyncio
async def test_model_provider_manager():
    """Test model provider manager functionality."""
    mock_config_loader = MagicMock()
    mock_model_config = MagicMock()
    mock_model_config.get_client_config.return_value = {
        "provider": "test.provider",
        "config": {"model": "test"}
    }
    mock_config_loader.get_model_config.return_value = mock_model_config
    
    with patch('autogen_core.models.ChatCompletionClient.load_component') as mock_load:
        mock_client = AsyncMock()
        mock_load.return_value = mock_client
        
        manager = ModelProviderManager(mock_config_loader)
        
        # Test client creation
        client = await manager.get_client("test_model")
        assert client == mock_client
        
        # Test client caching
        client2 = await manager.get_client("test_model")
        assert client2 == mock_client
        assert mock_load.call_count == 1  # Should be cached


@pytest.mark.asyncio
async def test_model_provider_manager_fallback():
    """Test model provider manager fallback functionality."""
    mock_config_loader = MagicMock()
    
    # Mock first model to fail, second to succeed
    def side_effect(model_name):
        if model_name == "failing_model":
            raise Exception("Model unavailable")
        else:
            mock_config = MagicMock()
            mock_config.get_client_config.return_value = {"provider": "test", "config": {}}
            return mock_config
    
    mock_config_loader.get_model_config.side_effect = side_effect
    
    with patch('autogen_core.models.ChatCompletionClient.load_component') as mock_load:
        mock_client = AsyncMock()
        mock_load.return_value = mock_client
        
        manager = ModelProviderManager(mock_config_loader)
        manager._fallback_order = ["failing_model", "deepseek", "openai"]
        
        # Test fallback
        client = await manager.get_client_with_fallback("failing_model")
        assert client == mock_client


@pytest.mark.asyncio
async def test_model_provider_manager_health_check():
    """Test model provider health check."""
    mock_config_loader = MagicMock()
    mock_config_loader.load_models_config.return_value = {"model1": MagicMock(), "model2": MagicMock()}
    
    manager = ModelProviderManager(mock_config_loader)
    
    # Mock get_client to succeed for model1, fail for model2
    async def mock_get_client(model_name):
        if model_name == "model1":
            return AsyncMock()
        else:
            raise Exception("Connection failed")
    
    manager.get_client = mock_get_client
    
    health = await manager.health_check()
    assert health["model1"] is True
    assert health["model2"] is False


def test_get_model_manager_singleton():
    """Test that get_model_manager returns a singleton."""
    manager1 = get_model_manager()
    manager2 = get_model_manager()
    assert manager1 is manager2