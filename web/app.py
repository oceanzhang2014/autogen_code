"""
Main Flask application factory.
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_app(testing: bool = False) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        testing: Whether to configure for testing
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__, static_folder='static', static_url_path='')
    
    # Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    if testing:
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
    
    # Enable CORS for frontend communication
    CORS(app, origins=["http://localhost:3000", "http://localhost:5011"])
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Register blueprints
    from web.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")
    
    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "autogen-multi-agent-system"}
    
    # Serve static files for frontend
    @app.route("/")
    def index():
        """Serve main frontend page."""
        return app.send_static_file("index.html")
    
    return app