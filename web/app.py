"""
Main Flask application factory.
"""
import os
import logging
from flask import Flask, redirect, request
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
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours
    
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
    
    # Authentication routes
    @app.route("/login.html")
    def login_page():
        """Serve login page."""
        return app.send_static_file("login.html")
    
    # Serve static files for frontend
    @app.route("/")
    def index():
        """Serve main frontend page."""
        from utils.auth import is_authenticated
        if not is_authenticated():
            # Check if we're running under a path prefix (like /autogen/)
            forwarded_prefix = request.headers.get('X-Forwarded-Prefix', '')
            print(f"DEBUG: X-Forwarded-Prefix header: '{forwarded_prefix}'")
            print(f"DEBUG: Request path: {request.path}")
            print(f"DEBUG: Host header: {request.headers.get('Host', '')}")
            
            # Check all headers that might indicate path prefix
            for header in ['X-Forwarded-Prefix', 'X-Script-Name', 'X-Original-URI']:
                value = request.headers.get(header, '')
                if value:
                    print(f"DEBUG: {header}: {value}")
            
            if forwarded_prefix:
                redirect_url = f"{forwarded_prefix}/login.html"
                print(f"DEBUG: Redirecting to: {redirect_url}")
                return redirect(redirect_url)
            print("DEBUG: Redirecting to: /login.html")
            return redirect("/login.html")
        return app.send_static_file("index.html")
    
    return app