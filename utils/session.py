"""
Session management and multi-agent orchestration.
"""
import asyncio
import json
import logging
import pickle
import os
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
    
    def __init__(self, persistence_dir: str = "sessions"):
        """Initialize session manager."""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(minutes=30)
        self.persistence_dir = persistence_dir
        
        # Create persistence directory if it doesn't exist
        if not os.path.exists(self.persistence_dir):
            os.makedirs(self.persistence_dir)
        
        # Load existing sessions
        self._load_sessions()
        
        # Register cleanup on app shutdown
        import atexit
        atexit.register(self._save_all_sessions)
    
    def create_session(self, session_id: str, team: RoundRobinGroupChat, request: CodeGenerationRequest, user_input_queue: Optional[asyncio.Queue] = None) -> None:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            team: Agent team for the session
            request: Code generation request
            user_input_queue: Optional user input queue
        """
        self.sessions[session_id] = {
            "team": team,
            "request": request,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "active": True,
            "user_input_queue": user_input_queue or asyncio.Queue()
        }
        logger.info(f"Created session {session_id}")
        self._save_session(session_id)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None if not found
        """
        session_data = self.sessions.get(session_id)
        if session_data is None:
            logger.warning(f"Session {session_id} not found. Available sessions: {list(self.sessions.keys())}")
        return session_data
    
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
            self._remove_session_file(session_id)
            logger.info(f"Cleaned up expired session {session_id}")

    def _save_session(self, session_id: str) -> None:
        """Save session to disk (excluding non-serializable objects)."""
        try:
            session_data = self.sessions.get(session_id)
            if not session_data:
                return
            
            # Create a serializable copy (exclude team and queue)
            serializable_data = {
                "request": {
                    "requirements": session_data["request"].requirements,
                    "language": session_data["request"].language,
                    "context": session_data["request"].context,
                    "max_iterations": session_data["request"].max_iterations
                },
                "created_at": session_data["created_at"],
                "status": session_data["status"],
                "active": session_data["active"]
            }
            
            session_file = os.path.join(self.persistence_dir, f"{session_id}.json")
            with open(session_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            logger.debug(f"Saved session {session_id} to disk")
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
    
    def _load_sessions(self) -> None:
        """Load sessions from disk."""
        try:
            if not os.path.exists(self.persistence_dir):
                return
            
            for filename in os.listdir(self.persistence_dir):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json extension
                    session_file = os.path.join(self.persistence_dir, filename)
                    
                    try:
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                        
                        # Check if session is expired
                        created_at = datetime.fromisoformat(session_data["created_at"])
                        if datetime.now() - created_at > self.session_timeout:
                            os.remove(session_file)
                            continue
                        
                        # Reconstruct the session (will need to recreate team and queue when needed)
                        from models.config import CodeGenerationRequest
                        request_data = session_data["request"]
                        request = CodeGenerationRequest(**request_data)
                        
                        self.sessions[session_id] = {
                            "team": None,  # Will be recreated when needed
                            "request": request,
                            "created_at": session_data["created_at"],
                            "status": session_data["status"],
                            "active": session_data["active"],
                            "user_input_queue": asyncio.Queue()  # New queue
                        }
                        
                        logger.info(f"Loaded session {session_id} from disk")
                        
                    except Exception as e:
                        logger.error(f"Error loading session {session_id}: {e}")
                        # Remove corrupted session file
                        try:
                            os.remove(session_file)
                        except:
                            pass
        
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
    
    def _remove_session_file(self, session_id: str) -> None:
        """Remove session file from disk."""
        try:
            session_file = os.path.join(self.persistence_dir, f"{session_id}.json")
            if os.path.exists(session_file):
                os.remove(session_file)
                logger.debug(f"Removed session file {session_id}")
        except Exception as e:
            logger.error(f"Error removing session file {session_id}: {e}")
    
    def _save_all_sessions(self) -> None:
        """Save all active sessions to disk on shutdown."""
        try:
            for session_id in list(self.sessions.keys()):
                self._save_session(session_id)
            logger.info("Saved all sessions on shutdown")
        except Exception as e:
            logger.error(f"Error saving sessions on shutdown: {e}")


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
        "quality_checker": "deepseek",  # Use deepseek instead of moonshot due to API key issue
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
    
    # Create termination condition for iterative workflow
    # Note: Termination will be handled by the iterative collaboration logic
    # The team itself doesn't need complex termination since we control the flow
    approve_termination = TextMentionTermination("APPROVE", sources=["user_proxy"])
    terminate_termination = TextMentionTermination("TERMINATE", sources=["user_proxy"])
    termination = approve_termination | terminate_termination
    
    # Create team for iterative collaboration (not round-robin since we control the flow)
    team = RoundRobinGroupChat(
        [generator, checker, optimizer, user_proxy],
        termination_condition=termination
    )
    
    logger.info(f"Created agent team for session {session_id}")
    return team


async def run_agent_team(team: RoundRobinGroupChat, request: CodeGenerationRequest, 
                        stream, session_id: str, session_manager) -> None:
    """
    Run the agent team collaboration with iterative optimization loop.
    
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
        
        # Get agents from the team
        session_agents = session_data.get("agents")
        if not session_agents:
            # Create and store agents for reuse
            from agents.code_generator import create_code_generator
            from agents.quality_checker import create_quality_checker  
            from agents.code_optimizer import create_code_optimizer
            from agents.user_proxy import create_user_proxy
            from models.providers import get_model_manager
            from models.config import ConfigLoader
            
            config_loader = ConfigLoader()
            model_manager = get_model_manager()
            
            # Create model clients
            generator_client = await model_manager.get_client_with_fallback("deepseek")
            checker_client = await model_manager.get_client_with_fallback("deepseek")
            optimizer_client = await model_manager.get_client_with_fallback("alibaba")
            
            # Create agents
            generator = await create_code_generator(generator_client, config_loader)
            checker = await create_quality_checker(checker_client, config_loader)
            optimizer = await create_code_optimizer(optimizer_client, config_loader)
            user_proxy = await create_user_proxy(session_id, user_input_queue)
            
            session_agents = {
                "generator": generator,
                "checker": checker,
                "optimizer": optimizer,
                "user_proxy": user_proxy
            }
            
            # Store agents in session for reuse
            session_data["agents"] = session_agents
        
        # Run iterative collaboration loop with individual agents
        await _run_iterative_collaboration(session_agents, request, stream, session_id, user_input_queue)
        
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


async def _run_iterative_collaboration(agents: dict, request: CodeGenerationRequest,
                                     stream, session_id: str, user_input_queue: asyncio.Queue) -> None:
    """
    Run iterative collaboration loop between agents.
    
    Args:
        agents: Dictionary containing generator, checker, optimizer, and user_proxy agents
        request: Code generation request
        stream: Message stream for real-time updates
        session_id: Session identifier
        user_input_queue: Queue for user input
    """
    max_iterations = getattr(request, 'max_iterations', 3)
    min_quality_score = 95
    current_iteration = 0
    
    # Get agents from the provided dictionary
    generator = agents.get("generator")
    checker = agents.get("checker") 
    optimizer = agents.get("optimizer")
    user_proxy = agents.get("user_proxy")
    
    if not all([generator, checker, optimizer, user_proxy]):
        logger.error(f"Available agents: {list(agents.keys())}")
        raise ValueError("Missing required agents in team")
    
    # Create initial task message
    current_requirements = f"""
    Generate {request.language} code for the following requirements:
    
    {request.requirements}
    
    Additional context: {request.context or 'None provided'}
    
    Please create high-quality, well-documented code that follows best practices.
    """
    
    latest_code = None
    
    while current_iteration < max_iterations:
        current_iteration += 1
        
        # Send iteration start message
        stream.put(json.dumps({
            "type": "system",
            "message": f"开始第 {current_iteration} 轮迭代优化",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Step 1: Code Generator creates/improves code
        generator_prompt = current_requirements if current_iteration == 1 else f"""
        基于以下反馈改进代码：
        
        {current_requirements}
        
        请只输出完整的优化后代码，不要包含解释性文字。
        """
        
        generator_response = await _get_agent_response(generator, generator_prompt, stream)
        latest_code = _extract_code_from_message(generator_response)
        
        # Step 2: Quality Checker evaluates the code
        checker_prompt = f"""
        请评估以下代码的质量：
        
        ```{request.language}
        {latest_code if latest_code else generator_response}
        ```
        
        请提供详细的质量分析和具体的评分。
        """
        
        checker_response = await _get_agent_response(checker, checker_prompt, stream)
        
        # Extract quality score
        quality_score = None
        if hasattr(checker, 'extract_quality_score'):
            quality_score = checker.extract_quality_score(checker_response)
        
        # Send score update to frontend
        if quality_score is not None:
            stream.put(json.dumps({
                "type": "quality_score", 
                "score": quality_score,
                "iteration": current_iteration,
                "timestamp": datetime.now().isoformat()
            }))
        
        # Check if quality threshold is met
        if quality_score is not None and quality_score >= min_quality_score:
            stream.put(json.dumps({
                "type": "system",
                "message": f"代码质量达到 {quality_score} 分，超过阈值 {min_quality_score} 分",
                "timestamp": datetime.now().isoformat()
            }))
            break
            
        # Step 3: Code Optimizer suggests improvements (if not final iteration)
        if current_iteration < max_iterations:
            optimizer_prompt = f"""
            基于以下代码和质量评估，提供具体的优化建议：
            
            代码：
            ```{request.language}
            {latest_code if latest_code else generator_response}
            ```
            
            质量评估：
            {checker_response}
            
            请提供具体的优化建议和改进方向。
            """
            
            optimizer_response = await _get_agent_response(optimizer, optimizer_prompt, stream)
            
            # Prepare requirements for next iteration
            current_requirements = f"""
            原始需求：{request.requirements}
            
            当前代码：
            ```{request.language}
            {latest_code if latest_code else generator_response}
            ```
            
            质量评估：{checker_response}
            
            优化建议：{optimizer_response}
            """
    
    # After iteration loop, involve user proxy for final approval
    stream.put(json.dumps({
        "type": "system", 
        "message": f"迭代优化完成（{current_iteration} 轮），等待用户确认",
        "timestamp": datetime.now().isoformat()
    }))
    
    # Send final code to frontend
    if latest_code:
        stream.put(json.dumps({
            "type": "code_output",
            "code": latest_code,
            "language": request.language,
            "iteration": current_iteration,
            "final_score": quality_score,
            "timestamp": datetime.now().isoformat()
        }))
    
    # Get user approval/feedback
    user_prompt = f"""
    代码优化已完成 {current_iteration} 轮迭代。
    
    最终质量评分：{quality_score if quality_score else '未评分'}/100
    
    请审核最终代码并选择：
    1. 批准代码（输入 APPROVE）
    2. 提供修改建议（输入具体建议）
    3. 终止会话（输入 TERMINATE）
    """
    
    # Send input request directly to stream for frontend display
    stream.put(json.dumps({
        "type": "input_request",
        "prompt": user_prompt,
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id
    }))
    
    user_response = await _get_user_input(user_proxy, user_prompt, user_input_queue)
    
    if user_response.upper() == "APPROVE":
        stream.put(json.dumps({
            "type": "system",
            "message": "用户已批准最终代码",
            "timestamp": datetime.now().isoformat()
        }))
    elif user_response.upper() == "TERMINATE":
        stream.put(json.dumps({
            "type": "system", 
            "message": "用户终止了会话",
            "timestamp": datetime.now().isoformat()
        }))
    else:
        # User provided feedback, start new iteration cycle
        stream.put(json.dumps({
            "type": "system",
            "message": "收到用户反馈，开始新的优化循环",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Update requirements with user feedback
        feedback_requirements = f"""
        用户反馈：{user_response}
        
        当前代码：
        ```{request.language}
        {latest_code}
        ```
        
        请根据用户反馈进行改进。
        """
        
        # Create new request object for new cycle with user feedback
        from models.config import CodeGenerationRequest
        feedback_request = CodeGenerationRequest(
            requirements=feedback_requirements,
            language=request.language,
            context=request.context,
            max_iterations=getattr(request, 'max_iterations', 3)
        )
        await _run_iterative_collaboration(agents, feedback_request, stream, session_id, user_input_queue)


async def _get_agent_response(agent, prompt: str, stream, max_retries: int = 3) -> str:
    """
    Get response from an agent and stream it to frontend.
    Support continuation for incomplete code output.
    
    Args:
        agent: The agent to get response from
        prompt: Prompt to send to agent
        stream: Stream for real-time updates
        max_retries: Maximum retry attempts for continuation
        
    Returns:
        str: Agent's response content
    """
    try:
        response_content = ""
        retry_count = 0
        
        while retry_count <= max_retries:
            current_prompt = prompt if retry_count == 0 else f"""
请继续输出完整代码，从以下内容继续：

{response_content}

请只输出剩余的代码部分，不要重复已有内容。
"""
            
            # Create message and get response
            message = TextMessage(content=current_prompt, source="user")
            chunk_response = ""
            
            async for chunk in agent.on_messages_stream([message], CancellationToken()):
                if hasattr(chunk, 'content'):
                    chunk_content = chunk.content
                    chunk_response += chunk_content
                    
                    # Stream chunk to frontend
                    stream.put(json.dumps({
                        "type": "agent_message",
                        "agent": agent.name,
                        "message": chunk_content,
                        "timestamp": datetime.now().isoformat(),
                        "is_chunk": True,
                        "retry_count": retry_count
                    }))
            
            response_content += chunk_response
            
            # Check if response seems complete (for code generator)
            if agent.name == "code_generator":
                # Check for common completion indicators
                if _is_code_complete(response_content):
                    break
                    
                # If we got significant content but seems incomplete, try to continue
                if len(chunk_response.strip()) > 50 and retry_count < max_retries:
                    retry_count += 1
                    
                    # Send continuation message
                    stream.put(json.dumps({
                        "type": "system",
                        "message": f"代码输出可能不完整，正在继续生成... (第{retry_count + 1}次)",
                        "timestamp": datetime.now().isoformat()
                    }))
                    continue
                else:
                    break
            else:
                # For non-code generators, don't retry
                break
        
        return response_content
        
    except Exception as e:
        logger.error(f"Error getting response from {agent.name}: {e}")
        return f"Error: Failed to get response from {agent.name}"


def _is_code_complete(code_content: str) -> bool:
    """
    Check if code output appears to be complete.
    
    Args:
        code_content: The code content to check
        
    Returns:
        bool: True if code appears complete
    """
    # Remove code block markers for analysis
    clean_content = code_content.strip()
    if clean_content.startswith('```'):
        lines = clean_content.split('\n')
        if len(lines) > 1:
            # Remove first line (```language)
            lines = lines[1:]
            # Check if ends with ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            clean_content = '\n'.join(lines)
    
    # Basic completeness checks
    checks = [
        # Check for balanced braces (for most languages)
        clean_content.count('{') == clean_content.count('}'),
        # Check for balanced parentheses
        clean_content.count('(') == clean_content.count(')'),
        # Check for balanced brackets
        clean_content.count('[') == clean_content.count(']'),
        # Check it doesn't end abruptly (not just whitespace)
        len(clean_content.strip()) > 0,
        # Check it doesn't end with incomplete line
        not clean_content.rstrip().endswith(('=', '+', '-', '*', '/', '\\', ',', '&', '|'))
    ]
    
    # If most checks pass, consider it complete
    passed_checks = sum(checks)
    return passed_checks >= len(checks) - 1  # Allow one check to fail


async def _get_user_input(user_proxy, prompt: str, user_input_queue: asyncio.Queue) -> str:
    """
    Get input from user through user proxy agent.
    
    Args:
        user_proxy: User proxy agent
        prompt: Prompt to display to user
        user_input_queue: Queue for user input
        
    Returns:
        str: User's input response
    """
    try:
        # Wait for user response from the input queue
        while True:
            response = await asyncio.wait_for(user_input_queue.get(), timeout=600.0)  # 5 minute timeout
            
            # Skip any input_request messages we put in the queue
            if (isinstance(response, dict) and 
                response.get("type") == "input_request"):
                continue
                
            if (isinstance(response, dict) and 
                response.get("type") == "user_input"):
                content = response.get("content", "No input provided")
                logger.info(f"Received user input: {content}")
                return content
                
    except asyncio.TimeoutError:
        logger.warning("User input timeout after 10 minutes")
        return "TERMINATE"  # Auto-terminate on timeout
    except Exception as e:
        logger.error(f"Error getting user input: {e}")
        return "Error: Failed to get user input"