"""
Session management and multi-agent orchestration.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.messages import TextMessage, ModelClientStreamingChunkEvent
from autogen_agentchat.base import TaskResult
from autogen_core import CancellationToken

from agents.code_generator import create_code_generator
from agents.quality_checker import create_quality_checker
from agents.code_optimizer import create_code_optimizer
from agents.user_proxy import create_user_proxy
from models.providers import get_model_manager
from models.config import CodeGenerationRequest, ConfigLoader

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions and agent teams."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(minutes=30)
    
    def create_session(self, session_id: str, team: RoundRobinGroupChat, request: CodeGenerationRequest) -> None:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            team: Agent team for the session
            request: Code generation request
        """
        self.sessions[session_id] = {
            "team": team,
            "request": request,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "active": True,
            "user_input_queue": asyncio.Queue()
        }
        logger.info(f"Created session {session_id}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None if not found
        """
        return self.sessions.get(session_id)
    
    def update_session_status(self, session_id: str, status: str) -> None:
        """
        Update session status.
        
        Args:
            session_id: Session identifier
            status: New status
        """
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = status
            logger.info(f"Updated session {session_id} status to {status}")
    
    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions."""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            created_at = datetime.fromisoformat(session_data["created_at"])
            if current_time - created_at > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session {session_id}")


async def create_agent_team(session_id: str, language: str, user_input_queue: asyncio.Queue = None) -> RoundRobinGroupChat:
    """
    Create specialized agent team for code generation.
    
    Args:
        session_id: Session identifier
        language: Programming language
        user_input_queue: Existing user input queue (optional)
    
    Returns:
        RoundRobinGroupChat: Configured agent team
    """
    config_loader = ConfigLoader()
    model_manager = get_model_manager()
    
    # Load model configurations for each agent
    agent_models = {
        "code_generator": "deepseek",
        "quality_checker": "moonshot", 
        "code_optimizer": "alibaba"
    }
    
    # Create model clients
    generator_client = await model_manager.get_client_with_fallback(agent_models["code_generator"])
    checker_client = await model_manager.get_client_with_fallback(agent_models["quality_checker"])
    optimizer_client = await model_manager.get_client_with_fallback(agent_models["code_optimizer"])
    
    # Create specialized agents
    generator = await create_code_generator(generator_client, config_loader)
    checker = await create_quality_checker(checker_client, config_loader)
    optimizer = await create_code_optimizer(optimizer_client, config_loader)
    user_proxy = await create_user_proxy(session_id, user_input_queue)
    
    # Create termination condition
    termination = TextMentionTermination("APPROVE", sources=["user_proxy"])
    
    # Create team with round-robin collaboration
    team = RoundRobinGroupChat(
        [generator, checker, optimizer, user_proxy],
        termination_condition=termination
    )
    
    logger.info(f"Created agent team for session {session_id}")
    return team


async def run_agent_team(team: RoundRobinGroupChat, request: CodeGenerationRequest, 
                        stream, session_id: str, session_manager) -> None:
    """
    Run the agent team collaboration.
    
    Args:
        team: Agent team
        request: Code generation request
        stream: Message stream for real-time updates
        session_id: Session identifier
        session_manager: Session manager instance
    """
    
    try:
        # Get session data to access user input queue
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        
        user_input_queue = session_data["user_input_queue"]
        
        # Start monitoring user input requests in background
        input_monitor_task = asyncio.create_task(
            _monitor_user_input_requests(user_input_queue, stream, session_id)
        )
        
        # Create initial task message
        task_message = f"""
        Generate {request.language} code for the following requirements:
        
        {request.requirements}
        
        Additional context: {request.context or 'None provided'}
        
        Please collaborate to create high-quality, well-documented code that follows best practices.
        """
        
        # Run the team with streaming
        async for message in team.run_stream(
            task=[TextMessage(content=task_message, source="user")],
            cancellation_token=CancellationToken()
        ):
            await _handle_team_message(message, stream, session_id)
        
        # Cancel the input monitor task
        input_monitor_task.cancel()
        try:
            await input_monitor_task
        except asyncio.CancelledError:
            pass
            
    except Exception as e:
        logger.error(f"Error running agent team for session {session_id}: {e}")
        stream.put(json.dumps({
            "type": "error",
            "message": f"Agent team error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }))


async def _monitor_user_input_requests(user_input_queue: asyncio.Queue, stream, session_id: str) -> None:
    """
    Monitor user input queue for input requests and forward them to the stream.
    
    Args:
        user_input_queue: Queue to monitor for input requests
        stream: Output stream to send input requests
        session_id: Session identifier
    """
    try:
        while True:
            try:
                # Wait for input request with timeout to allow cancellation
                input_request = await asyncio.wait_for(user_input_queue.get(), timeout=1.0)
                
                # Check if this is an input request
                if (isinstance(input_request, dict) and 
                    input_request.get("type") == "input_request"):
                    
                    # Forward the input request to the frontend stream
                    stream.put(json.dumps({
                        "type": "input_request",
                        "prompt": input_request.get("prompt", "Please provide input:"),
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id
                    }))
                    
                    logger.info(f"Forwarded input request to stream for session {session_id}")
                
                # Put the message back in the queue for the user proxy to handle
                await user_input_queue.put(input_request)
                
            except asyncio.TimeoutError:
                # Continue the loop to allow cancellation
                continue
                
    except asyncio.CancelledError:
        logger.info(f"Input monitor cancelled for session {session_id}")
        raise
    except Exception as e:
        logger.error(f"Error monitoring user input requests for session {session_id}: {e}")


async def _handle_team_message(message, stream, session_id: str) -> None:
    """
    Handle messages from the agent team in real-time.
    
    Args:
        message: Message from team
        stream: Output stream
        session_id: Session identifier
    """
    try:
        if isinstance(message, ModelClientStreamingChunkEvent):
            # Handle streaming content from agents
            stream.put(json.dumps({
                "type": "agent_message",
                "agent": message.source,
                "message": message.content,
                "timestamp": datetime.now().isoformat(),
                "is_chunk": True
            }))
            
        elif isinstance(message, TaskResult):
            # Handle task completion
            if message.stop_reason:
                stream.put(json.dumps({
                    "type": "system",
                    "message": f"Task completed: {message.stop_reason}",
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Extract final code if available
            if hasattr(message, 'messages') and message.messages:
                final_message = message.messages[-1]
                if hasattr(final_message, 'content'):
                    # Try to extract code blocks
                    code = _extract_code_from_message(final_message.content)
                    if code:
                        stream.put(json.dumps({
                            "type": "code_output",
                            "code": code,
                            "language": "python",  # Default, could be detected
                            "timestamp": datetime.now().isoformat()
                        }))
        
        else:
            # Handle regular agent messages in real-time
            if hasattr(message, 'content') and hasattr(message, 'source'):
                # Send the message immediately to the frontend
                stream.put(json.dumps({
                    "type": "agent_message",
                    "agent": message.source,
                    "message": message.content,
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Add a small delay to make the conversation flow more naturally
                await asyncio.sleep(0.1)
                
    except Exception as e:
        logger.error(f"Error handling team message: {e}")


def _extract_code_from_message(content: str) -> Optional[str]:
    """
    Extract code blocks from message content.
    
    Args:
        content: Message content
    
    Returns:
        Extracted code or None
    """
    import re
    
    # Look for code blocks (```language...```)
    code_block_pattern = r'```(?:\w+)?\n(.*?)\n```'
    matches = re.findall(code_block_pattern, content, re.DOTALL)
    
    if matches:
        # Return the largest code block
        return max(matches, key=len).strip()
    
    # Look for inline code (`code`)
    inline_code_pattern = r'`([^`]+)`'
    inline_matches = re.findall(inline_code_pattern, content)
    
    if inline_matches:
        # Return if it looks like substantial code
        longest_inline = max(inline_matches, key=len)
        if len(longest_inline) > 50:  # Arbitrary threshold
            return longest_inline.strip()
    
    return None