"""
Model configuration management with pydantic validation.
"""
import os
import yaml
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelProvider(str, Enum):
    """Supported model providers."""
    DEEPSEEK = "deepseek"
    MOONSHOT = "moonshot"
    ALIBABA = "alibaba"
    OLLAMA = "ollama"
    OPENAI = "openai"


class ModelConfig(BaseModel):
    """Model configuration with validation."""
    provider: str
    config: Dict[str, Any] = Field(default_factory=dict)
    
    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration ready for ChatCompletionClient.load_component()."""
        # Replace environment variables in config
        config_copy = self.config.copy()
        for key, value in config_copy.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                default_value = None
                if ":-" in env_var:
                    env_var, default_value = env_var.split(":-")
                config_copy[key] = os.getenv(env_var, default_value)
        
        return {
            "provider": self.provider,
            "config": config_copy
        }


class AgentConfig(BaseModel):
    """Agent configuration with system prompt and parameters."""
    system_prompt: str
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2000, ge=1, le=8000)


class CodeGenerationRequest(BaseModel):
    """Request for code generation."""
    requirements: str = Field(..., min_length=10)
    language: str = Field("python", pattern="^(python|javascript|java|go|rust|typescript|cpp|c|php|ruby)$")
    context: Optional[str] = None
    max_iterations: int = Field(3, ge=1, le=10)


class AgentResponse(BaseModel):
    """Response from an agent."""
    agent_name: str
    message: str
    timestamp: str
    message_type: str = Field("message", pattern="^(message|tool_use|error|termination)$")


class ConfigLoader:
    """Configuration loader for models and agents."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize with configuration directory."""
        self.config_dir = config_dir
        self._models_config = None
        self._agents_config = None
    
    def load_models_config(self) -> Dict[str, ModelConfig]:
        """Load model configurations from YAML file."""
        if self._models_config is None:
            config_path = os.path.join(self.config_dir, "models.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            self._models_config = {}
            for name, config in data["models"].items():
                self._models_config[name] = ModelConfig(**config)
        
        return self._models_config
    
    def load_agents_config(self) -> Dict[str, AgentConfig]:
        """Load agent configurations from YAML file."""
        if self._agents_config is None:
            config_path = os.path.join(self.config_dir, "agents.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            self._agents_config = {}
            for name, config in data["agents"].items():
                self._agents_config[name] = AgentConfig(**config)
        
        return self._agents_config
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get specific model configuration."""
        models = self.load_models_config()
        if model_name not in models:
            raise ValueError(f"Model {model_name} not found in configuration")
        return models[model_name]
    
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get specific agent configuration."""
        agents = self.load_agents_config()
        if agent_name not in agents:
            raise ValueError(f"Agent {agent_name} not found in configuration")
        return agents[agent_name]
    
    def reload_config(self):
        """Reload configurations from files."""
        self._models_config = None
        self._agents_config = None