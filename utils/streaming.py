"""
Real-time streaming utilities for agent communication.
"""
import queue
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamingManager:
    """Manages real-time message streaming for multiple sessions."""
    
    def __init__(self):
        """Initialize streaming manager."""
        self.streams: Dict[str, queue.Queue] = {}
    
    def create_stream(self, session_id: str) -> queue.Queue:
        """
        Create a new message stream for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Message queue for the session
        """
        stream = queue.Queue(maxsize=1000)  # Prevent memory issues
        self.streams[session_id] = stream
        logger.info(f"Created stream for session {session_id}")
        return stream
    
    def get_stream(self, session_id: str) -> Optional[queue.Queue]:
        """
        Get message stream for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Message queue or None if not found
        """
        return self.streams.get(session_id)
    
    def send_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a session stream.
        
        Args:
            session_id: Session identifier
            message: Message to send
        
        Returns:
            True if message was sent, False otherwise
        """
        stream = self.get_stream(session_id)
        if not stream:
            logger.warning(f"No stream found for session {session_id}")
            return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
            
            # Convert to JSON string for SSE
            json_message = json.dumps(message)
            stream.put(json_message, timeout=1.0)
            return True
            
        except queue.Full:
            logger.warning(f"Stream queue full for session {session_id}")
            return False
        except Exception as e:
            logger.error(f"Error sending message to stream {session_id}: {e}")
            return False
    
    def close_stream(self, session_id: str) -> None:
        """
        Close and remove a session stream.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.streams:
            # Send end-of-stream marker
            self.send_message(session_id, {"type": "stream_end"})
            del self.streams[session_id]
            logger.info(f"Closed stream for session {session_id}")
    
    def cleanup_inactive_streams(self) -> None:
        """Remove streams that haven't been accessed recently."""
        # This could be enhanced with activity tracking
        pass


class MessageFormatter:
    """Formats messages for different output types."""
    
    @staticmethod
    def format_agent_message(agent_name: str, content: str, timestamp: str = None) -> Dict[str, Any]:
        """
        Format an agent message.
        
        Args:
            agent_name: Name of the agent
            content: Message content
            timestamp: Message timestamp
        
        Returns:
            Formatted message
        """
        return {
            "type": "agent_message",
            "agent": agent_name,
            "message": content,
            "timestamp": timestamp or datetime.now().isoformat()
        }
    
    @staticmethod
    def format_system_message(content: str, timestamp: str = None) -> Dict[str, Any]:
        """
        Format a system message.
        
        Args:
            content: Message content
            timestamp: Message timestamp
        
        Returns:
            Formatted message
        """
        return {
            "type": "system",
            "message": content,
            "timestamp": timestamp or datetime.now().isoformat()
        }
    
    @staticmethod
    def format_code_output(code: str, language: str, timestamp: str = None) -> Dict[str, Any]:
        """
        Format a code output message.
        
        Args:
            code: Code content
            language: Programming language
            timestamp: Message timestamp
        
        Returns:
            Formatted message
        """
        return {
            "type": "code_output",
            "code": code,
            "language": language,
            "timestamp": timestamp or datetime.now().isoformat()
        }
    
    @staticmethod
    def format_error_message(error: str, timestamp: str = None) -> Dict[str, Any]:
        """
        Format an error message.
        
        Args:
            error: Error message
            timestamp: Message timestamp
        
        Returns:
            Formatted message
        """
        return {
            "type": "error",
            "message": error,
            "timestamp": timestamp or datetime.now().isoformat()
        }


# Global streaming manager instance
_streaming_manager: Optional[StreamingManager] = None


def get_streaming_manager() -> StreamingManager:
    """Get the global streaming manager instance."""
    global _streaming_manager
    if _streaming_manager is None:
        _streaming_manager = StreamingManager()
    return _streaming_manager