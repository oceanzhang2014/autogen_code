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

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint("api", __name__)

# Global managers
session_manager = SessionManager()
streaming_manager = StreamingManager()
config_loader = ConfigLoader()


@api_bp.route("/generate", methods=["POST"])
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
        
        # Create or get session
        session_id = session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            session["session_id"] = session_id
        
        # Create session first with user input queue
        import concurrent.futures
        user_input_queue = asyncio.Queue()
        session_manager.create_session(session_id, None, req)  # Create with placeholder team
        session_data = session_manager.get_session(session_id)
        session_data["user_input_queue"] = user_input_queue  # Set the queue
        
        # Create agent team for this session
        try:
            # Run async function in sync context
            try:
                # Try to get existing event loop
                loop = asyncio.get_running_loop()
                # If we have a running loop, schedule the task
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(create_agent_team(session_id, req.language, user_input_queue))
                    )
                    team = future.result(timeout=30)
            except RuntimeError:
                # No running loop, we can create one
                team = asyncio.run(create_agent_team(session_id, req.language, user_input_queue))
            
            # Update session with the created team
            session_data["team"] = team
        except Exception as e:
            logger.error(f"Failed to create agent team: {e}")
            return jsonify({"error": "Failed to initialize agents"}), 500
        
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
                yield 'data: {"error": "Session not found"}\n\n'
                return
            
            while True:
                try:
                    # Wait for next message with timeout
                    message = stream.get(timeout=1.0)
                    if message is None:  # End of stream marker
                        yield 'data: {"type": "stream_end"}\n\n'
                        break
                    
                    # Send message as SSE
                    yield f"data: {message}\n\n"
                    
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield 'data: {"type": "heartbeat"}\n\n'
                    continue
                    
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield 'data: {"error": "Stream error"}\n\n'
    
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
def handle_user_input():
    """
    Handle user input messages during agent collaboration.
    
    Returns:
        JSON response with status
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        content = data.get("content", "")
        
        if not session_id or not content.strip():
            return jsonify({"error": "Invalid request"}), 400
        
        # Get session
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404
        
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
        
        return jsonify({
            "status": "success",
            "message": "User input sent successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in user_input endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/approve", methods=["POST"])
def approve_code():
    """
    Handle user approval or rejection of generated code.
    
    Returns:
        JSON response with status
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        action = data.get("action")  # "approve" or "reject"
        feedback = data.get("feedback", "")
        
        if not session_id or action not in ["approve", "reject"]:
            return jsonify({"error": "Invalid request"}), 400
        
        # Get session
        session_data = session_manager.get_session(session_id)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404
        
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
        
        return jsonify({
            "status": "success",
            "action": action,
            "message": f"Code {action}d successfully"
        })
        
    except Exception as e:
        logger.error(f"Error in approve endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/status/<session_id>")
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


@api_bp.route("/models")
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
        
        team = session_data["team"]
        stream = streaming_manager.get_stream(session_id)
        
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