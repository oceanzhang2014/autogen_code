"""
API routes for the multi-agent code generation system.
"""
import uuid
import asyncio
import queue
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, session, Response
from pydantic import ValidationError

from models.config import CodeGenerationRequest, ConfigLoader
from models.providers import get_model_manager
from utils.session import SessionManager, create_agent_team
from utils.streaming import StreamingManager
from utils.auth import verify_credentials, login_user, logout_user, login_required

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint("api", __name__)

# Global managers
session_manager = SessionManager()
streaming_manager = StreamingManager()
config_loader = ConfigLoader()


@api_bp.route("/login", methods=["POST"])
def login():
    """
    Handle user login.
    
    Returns:
        JSON response with login status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        username = data.get("username", "").strip()
        password = data.get("password", "")
        
        if not username or not password:
            return jsonify({"error": "用户名和密码不能为空"}), 400
        
        if verify_credentials(username, password):
            login_user(username)
            logger.info(f"User {username} logged in successfully")
            return jsonify({
                "status": "success",
                "message": "登录成功",
                "username": username
            })
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return jsonify({"error": "用户名或密码错误"}), 401
    
    except Exception as e:
        logger.error(f"Error in login endpoint: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@api_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Handle user logout.
    
    Returns:
        JSON response with logout status
    """
    try:
        username = session.get("username")
        logout_user()
        logger.info(f"User {username} logged out")
        return jsonify({
            "status": "success",
            "message": "登出成功"
        })
    
    except Exception as e:
        logger.error(f"Error in logout endpoint: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@api_bp.route("/auth/status")
def auth_status():
    """
    Check authentication status.
    
    Returns:
        JSON response with authentication status
    """
    try:
        from utils.auth import is_authenticated
        authenticated = is_authenticated()
        username = session.get("username") if authenticated else None
        
        return jsonify({
            "authenticated": authenticated,
            "username": username
        })
    
    except Exception as e:
        logger.error(f"Error in auth status endpoint: {e}")
        return jsonify({"error": "服务器内部错误"}), 500


@api_bp.route("/generate", methods=["POST"])
@login_required
def generate_code():
    """
    Initiate code generation workflow.
    
    Returns:
        JSON response with session ID and streaming URL
    """
    try:
        # Validate request data
        try:
            data = request.get_json()
        except Exception:
            return jsonify({"error": "Invalid JSON data provided"}), 400
            
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate using pydantic
        try:
            req = CodeGenerationRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Invalid request data", "details": str(e)}), 400
        
        # Create new session for each generation request
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
        
        logger.info(f"Creating new generation session: {session_id}")
        
        # Create session with user input queue
        import concurrent.futures
        user_input_queue = asyncio.Queue()
        # Create session with user input queue - pass the queue to session creation
        session_manager.create_session(session_id, None, req, user_input_queue)  # Create with placeholder team and queue
        
        logger.info(f"Session {session_id} created successfully")
        logger.info(f"Current active sessions: {list(session_manager.sessions.keys())}")
        
        # Start streaming for this session
        streaming_manager.create_stream(session_id)
        
        # Start async task for agent collaboration
        import threading
        def run_async_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(_process_generation_request(session_id, req))
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_async_task)
        thread.start()
        
        return jsonify({
            "session_id": session_id,
            "status": "started",
            "stream_url": f"/api/stream/{session_id}",
            "message": "Code generation started"
        })
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/stream/<session_id>")
@login_required
def stream_messages(session_id: str):
    """
    Stream real-time agent messages using Server-Sent Events.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Response: Server-sent events stream
    """
    def generate_events():
        """Generate server-sent events for the session."""
        try:
            # Get the message stream for this session
            stream = streaming_manager.get_stream(session_id)
            if not stream:
                yield 'data: {"type": "error", "message": "Session not found"}\n\n'
                return
            
            while True:
                try:
                    # Wait for next message with standard timeout
                    message = stream.get(timeout=2.0)  # 2 second timeout
                    if message is None:  # End of stream marker
                        yield 'data: {"type": "stream_end"}\n\n'
                        break
                    
                    # Send message as SSE
                    yield f"data: {message}\n\n"
                    
                except queue.Empty:
                    # Send simple heartbeat every timeout
                    import json
                    yield f'data: {json.dumps({"type": "heartbeat", "timestamp": datetime.now().isoformat()})}\n\n'
                    continue
                    
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            import traceback
            logger.error(f"Stream error traceback: {traceback.format_exc()}")
            try:
                yield 'data: {"type": "error", "message": "Stream error"}\n\n'
            except:
                pass  # If we can't even send error message, connection is likely dead
    
    return Response(
        generate_events(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


@api_bp.route("/user_input", methods=["POST"])
@login_required
def handle_user_input():
    """
    Handle user input messages during agent collaboration.
    
    Returns:
        JSON response with status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        session_id = data.get("session_id")
        content = data.get("content", "")
        
        logger.info(f"Received user input request for session: {session_id}")
        logger.info(f"Available sessions: {list(session_manager.sessions.keys())}")
        
        if not session_id or not content.strip():
            logger.error(f"Invalid request - session_id: {session_id}, content: {content}")
            return jsonify({"error": "Invalid request"}), 400
        
        # Get session
        session_data = session_manager.get_session(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found in user_input endpoint")
            logger.error(f"Available sessions: {list(session_manager.sessions.keys())}")
            return jsonify({"error": "Session not found"}), 404
        
        # Check if user input queue exists
        if "user_input_queue" not in session_data:
            logger.error(f"User input queue not found in session {session_id}")
            return jsonify({"error": "Session not ready for user input"}), 400
        
        # Send user input to user proxy agent
        user_input = {
            "type": "user_input",
            "content": content.strip(),
            "session_id": session_id
        }
        
        # Add to user proxy input queue
        try:
            # Try to get existing event loop
            loop = asyncio.get_running_loop()
            # If we have a running loop, schedule the task
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(session_data["user_input_queue"].put(user_input))
                )
                future.result(timeout=10)
        except RuntimeError:
            # No running loop, we can create one
            asyncio.run(session_data["user_input_queue"].put(user_input))
        except Exception as e:
            logger.error(f"Error putting user input to queue: {e}")
            return jsonify({"error": "Failed to process user input"}), 500
        
        return jsonify({
            "status": "success",
            "message": "User input sent successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in user_input endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/approve", methods=["POST"])
@login_required
def approve_code():
    """
    Handle user approval or rejection of generated code.
    
    Returns:
        JSON response with status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        session_id = data.get("session_id")
        action = data.get("action")  # "approve" or "reject"
        feedback = data.get("feedback", "")
        
        if not session_id or action not in ["approve", "reject"]:
            return jsonify({"error": "Invalid request"}), 400
        
        # Get session
        session_data = session_manager.get_session(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found in approve endpoint")
            return jsonify({"error": "Session not found"}), 404
        
        # Check if user input queue exists
        if "user_input_queue" not in session_data:
            logger.error(f"User input queue not found in session {session_id} for approve")
            return jsonify({"error": "Session not ready for approval"}), 400
        
        # Send approval/rejection to user proxy agent
        user_input = {
            "type": "user_input",
            "content": "APPROVE" if action == "approve" else f"REJECT: {feedback}",
            "session_id": session_id
        }
        
        # Add to user proxy input queue
        try:
            # Try to get existing event loop
            loop = asyncio.get_running_loop()
            # If we have a running loop, schedule the task
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(session_data["user_input_queue"].put(user_input))
                )
                future.result(timeout=10)
        except RuntimeError:
            # No running loop, we can create one
            asyncio.run(session_data["user_input_queue"].put(user_input))
        except Exception as e:
            logger.error(f"Error putting approval to queue: {e}")
            return jsonify({"error": "Failed to process approval"}), 500
        
        return jsonify({
            "status": "success",
            "action": action,
            "message": f"Code {action}d successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in approve endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/status/<session_id>")
@login_required
def get_session_status(session_id: str):
    """
    Get session status and information.
    
    Args:
        session_id: Session identifier
    
    Returns:
        JSON response with session status
    """
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "session_id": session_id,
            "status": session_data.get("status", "unknown"),
            "created_at": session_data.get("created_at"),
            "language": session_data.get("request", {}).language if session_data.get("request") else None,
            "active": session_data.get("active", False)
        })
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/debug_sessions")
def debug_sessions():
    """Debug endpoint to check session status."""
    try:
        sessions_info = {}
        for session_id, session_data in session_manager.sessions.items():
            sessions_info[session_id] = {
                "status": session_data.get("status"),
                "created_at": session_data.get("created_at"),
                "active": session_data.get("active"),
                "has_team": "team" in session_data,
                "has_queue": "user_input_queue" in session_data,
            }
        
        return jsonify({
            "total_sessions": len(session_manager.sessions),
            "sessions": sessions_info,
            "session_manager_id": id(session_manager),
            "streaming_manager_id": id(streaming_manager)
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/models")
@login_required
def list_models():
    """
    List available model configurations.
    
    Returns:
        JSON response with available models
    """
    try:
        model_manager = get_model_manager()
        models = model_manager.list_available_models()
        
        return jsonify({
            "models": models,
            "default_models": {
                "code_generator": "deepseek",
                "quality_checker": "moonshot", 
                "code_optimizer": "alibaba"
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({"error": "Internal server error"}), 500


async def _process_generation_request(session_id: str, request: CodeGenerationRequest):
    """
    Process code generation request with agent team.
    
    Args:
        session_id: Session identifier
        request: Code generation request
    """
    try:
        # Get session data
        session_data = session_manager.get_session(session_id)
        if not session_data:
            logger.error(f"Session {session_id} not found")
            return
        
        # Get or create team for this session
        team = session_data.get("team")
        if not team:
            logger.info(f"Creating agent team for session {session_id}")
            # Get the user input queue from session
            user_input_queue = session_data.get("user_input_queue")
            if not user_input_queue:
                logger.error(f"No user input queue found for session {session_id}")
                # Send error to stream
                stream = streaming_manager.get_stream(session_id)
                if stream:
                    stream.put(json.dumps({
                        "type": "error",
                        "message": "Session not properly initialized",
                        "timestamp": datetime.now().isoformat()
                    }))
                return
            
            try:
                # Create the agent team
                team = await create_agent_team(session_id, request.language, user_input_queue)
                session_data["team"] = team
                logger.info(f"Agent team created successfully for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to create agent team for session {session_id}: {e}")
                # Send error to stream
                stream = streaming_manager.get_stream(session_id)
                if stream:
                    stream.put(json.dumps({
                        "type": "error",
                        "message": f"Failed to initialize agents: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))
                return
        
        stream = streaming_manager.get_stream(session_id)
        if not stream:
            logger.error(f"No stream found for session {session_id}")
            return
        
        # Update session status
        session_manager.update_session_status(session_id, "running")
        
        # Send initial message to stream
        import json
        stream.put(json.dumps({
            "type": "system",
            "message": f"Starting code generation for: {request.requirements}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Run the agent team
        from utils.session import run_agent_team
        await run_agent_team(team, request, stream, session_id, session_manager)
        
        # Update session status
        session_manager.update_session_status(session_id, "completed")
        
        # Send completion message
        stream.put(json.dumps({
            "type": "system",
            "message": "Code generation completed",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Mark end of stream
        stream.put(None)
        
    except Exception as e:
        logger.error(f"Error processing generation request: {e}")
        stream = streaming_manager.get_stream(session_id)
        if stream:
            stream.put(json.dumps({
                "type": "error",
                "message": f"Error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))
            stream.put(None)