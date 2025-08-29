"""
Code optimization and performance specialist agent.
"""
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from models.config import ConfigLoader


async def create_code_optimizer(model_client: ChatCompletionClient, config_loader: ConfigLoader = None) -> AssistantAgent:
    """
    Create specialized code optimization agent.
    
    Args:
        model_client: Model client for the agent
        config_loader: Configuration loader for agent settings
    
    Returns:
        AssistantAgent: Configured code optimization agent
    """
    config_loader = config_loader or ConfigLoader()
    agent_config = config_loader.get_agent_config("code_optimizer")
    
    return AssistantAgent(
        name="code_optimizer",
        model_client=model_client,
        system_message=agent_config.system_prompt,
        model_client_stream=True,  # Enable streaming for real-time output
    )