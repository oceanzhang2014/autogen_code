#!/usr/bin/env python3
"""
AutoGen Multi-Agent Code Generation System Entry Point
"""
import os
import sys
import logging
from web.app import create_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def validate_environment():
    """
    Validate required environment variables and configuration.
    
    Returns:
        bool: True if environment is valid
    """
    required_vars = [
        'SECRET_KEY',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("📝 Please create a .env file based on .env.example")
        return False
    
    # Check for at least one model provider API key
    model_keys = [
        'DEEPSEEK_API_KEY',
        'MOONSHOT_API_KEY', 
        'ALIBABA_API_KEY',
        'OPENAI_API_KEY'
    ]
    
    available_models = [key for key in model_keys if os.getenv(key)]
    
    if not available_models and not os.getenv('OLLAMA_BASE_URL'):
        print("⚠️  Warning: No model provider API keys found.")
        print("   Either provide API keys or ensure Ollama is running locally.")
        print("   Available providers: DeepSeek, Moonshot, Alibaba, OpenAI, Ollama")
        return False
    
    return True


def check_config_files():
    """
    Check if required configuration files exist.
    
    Returns:
        bool: True if all config files exist
    """
    required_files = [
        'config/models.yaml',
        'config/agents.yaml'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing configuration files: {', '.join(missing_files)}")
        return False
    
    return True


def setup_logging():
    """Configure logging for the application."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('autogen_system.log', mode='a')
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def print_startup_info():
    """Print startup information and instructions."""
    print("🤖 AutoGen Multi-Agent Code Generation System")
    print("=" * 50)
    print("")
    print("🚀 Starting Flask application...")
    print("")
    print("📋 System Components:")
    print("   • Flask Web Server")
    print("   • AutoGen Agent Framework") 
    print("   • Multi-Provider Model Support")
    print("   • Real-time Streaming Interface")
    print("")
    print("🔧 Available Model Providers:")
    
    providers = []
    if os.getenv('DEEPSEEK_API_KEY'):
        providers.append("DeepSeek")
    if os.getenv('MOONSHOT_API_KEY'):
        providers.append("Moonshot")
    if os.getenv('ALIBABA_API_KEY'):
        providers.append("Alibaba")
    if os.getenv('OPENAI_API_KEY'):
        providers.append("OpenAI")
    if os.getenv('OLLAMA_BASE_URL'):
        providers.append("Ollama (Local)")
    
    if providers:
        for provider in providers:
            print(f"   ✅ {provider}")
    else:
        print("   ⚠️  No providers configured")
    
    print("")
    print("🌐 Access URLs:")
    port = os.getenv('PORT', '5011')
    print(f"   • Web Interface: http://localhost:{port}")
    print(f"   • Health Check:  http://localhost:{port}/health")
    print(f"   • API Docs:      http://localhost:{port}/api/models")
    print("")


def main():
    """Main application entry point."""
    print_startup_info()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Check configuration files
    if not check_config_files():
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    
    # Create Flask application
    app = create_app()
    
    # Get configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5011'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("✅ Environment validation passed")
    print("✅ Configuration files found")
    print("✅ Application initialized")
    print("")
    print(f"🌍 Server starting on {host}:{port}")
    print(f"🐛 Debug mode: {debug}")
    print("")
    print("📖 Usage Instructions:")
    print("   1. Open web interface in your browser")
    print("   2. Enter code generation requirements")
    print("   3. Select programming language")
    print("   4. Watch agents collaborate in real-time")
    print("   5. Review and approve/reject final code")
    print("")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run Flask application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        print("Thank you for using AutoGen Multi-Agent System!")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()