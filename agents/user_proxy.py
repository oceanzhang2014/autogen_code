"""
User proxy agent for human interaction and approval workflows.
"""
import asyncio
from typing import Optional
from autogen_agentchat.agents import UserProxyAgent
from autogen_core import CancellationToken


class WebUserProxyAgent(UserProxyAgent):
    """User proxy agent adapted for web interface."""
    
    def __init__(self, session_id: str, input_queue: Optional[asyncio.Queue] = None, **kwargs):
        """
        Initialize web user proxy agent.
        
        Args:
            session_id: Unique session identifier
            input_queue: Queue for receiving user input from web interface
            **kwargs: Additional arguments for UserProxyAgent
        """
        self.session_id = session_id
        self.input_queue = input_queue or asyncio.Queue()
        
        super().__init__(
            name="user_proxy",
            input_func=self._web_input_func,
            **kwargs
        )
    
    async def _web_input_func(self, prompt: str, cancellation_token: Optional[CancellationToken] = None) -> str:
        """
        Get user input from web interface.
        
        Args:
            prompt: Prompt to display to user
            cancellation_token: Token for cancellation
        
        Returns:
            str: User input response
        """
        # Store the prompt for the web interface to display
        await self.input_queue.put({
            "type": "input_request",
            "prompt": prompt,
            "session_id": self.session_id
        })
        
        # Wait for user response (skip any input_request messages)
        try:
            async def get_user_response():
                while True:
                    response = await self.input_queue.get()
                    
                    # Skip our own input_request messages
                    if (isinstance(response, dict) and 
                        response.get("type") == "input_request"):
                        continue
                        
                    if (isinstance(response, dict) and 
                        response.get("type") == "user_input" and 
                        response.get("session_id") == self.session_id):
                        return response.get("content", "No input provided")
                    else:
                        return "Invalid input format"
            
            if cancellation_token:
                return await asyncio.wait_for(
                    get_user_response(),
                    timeout=600.0  # 10 minute timeout
                )
            else:
                return await get_user_response()
                
        except asyncio.TimeoutError:
            return "User did not provide input within the time limit"
        except Exception as e:
            return f"Error getting user input: {str(e)}"


async def create_user_proxy(session_id: str, input_queue: Optional[asyncio.Queue] = None) -> WebUserProxyAgent:
    """
    Create user proxy agent for web interface.
    
    Args:
        session_id: Unique session identifier
        input_queue: Queue for receiving user input
    
    Returns:
        WebUserProxyAgent: Configured user proxy agent
    """
    return WebUserProxyAgent(
        session_id=session_id,
        input_queue=input_queue
    )