"""
Code quality checking and security analysis agent.
"""
import re
from typing import Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from models.config import ConfigLoader


class QualityCheckerAgent(AssistantAgent):
    """Enhanced Quality Checker agent with scoring capabilities."""
    
    def __init__(self, model_client: ChatCompletionClient, system_message: str, **kwargs):
        """
        Initialize Quality Checker agent.
        
        Args:
            model_client: Model client for the agent
            system_message: System prompt for the agent
            **kwargs: Additional arguments for AssistantAgent
        """
        super().__init__(
            name="quality_checker",
            model_client=model_client,
            system_message=system_message,
            model_client_stream=True,
            **kwargs
        )
    
    def extract_quality_score(self, message_content: str) -> Optional[int]:
        """
        Extract quality score from agent response.
        
        Args:
            message_content: The agent's response message
            
        Returns:
            Optional[int]: Quality score (0-100) or None if not found
        """
        # Look for patterns like "质量评分: 85/100" or "质量评分：85/100"
        score_patterns = [
            r'质量评分[：:]\s*(\d+)/100',
            r'质量评分[：:]\s*(\d+)分',
            r'评分[：:]\s*(\d+)/100',
            r'评分[：:]\s*(\d+)分',
            r'Score[：:]\s*(\d+)/100',
            r'Quality Score[：:]\s*(\d+)/100'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, message_content, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                # Ensure score is within valid range
                if 0 <= score <= 100:
                    return score
        
        return None


async def create_quality_checker(model_client: ChatCompletionClient, config_loader: ConfigLoader = None) -> QualityCheckerAgent:
    """
    Create specialized quality checking agent.
    
    Args:
        model_client: Model client for the agent
        config_loader: Configuration loader for agent settings
    
    Returns:
        QualityCheckerAgent: Configured quality checking agent with scoring
    """
    config_loader = config_loader or ConfigLoader()
    agent_config = config_loader.get_agent_config("quality_checker")
    
    return QualityCheckerAgent(
        model_client=model_client,
        system_message=agent_config.system_prompt
    )