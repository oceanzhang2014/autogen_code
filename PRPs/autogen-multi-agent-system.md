name: "AutoGen Multi-Agent Code Generation System"
description: |

## Purpose
Build a production-ready multi-agent code generation system using AutoGen framework with Flask backend and HTML frontend. The system features specialized agents for code generation, quality checking, and optimization, with real-time streaming output and user approval workflows.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a complete multi-agent system where users can request code generation through a web interface, and specialized AutoGen agents collaborate to produce, review, and optimize code. The system should support multiple LLM providers, provide real-time streaming output, and include human-in-the-loop approval workflows.

## Why
- **Business value**: Automates complex code generation workflows with multiple expert perspectives
- **Integration**: Demonstrates advanced AutoGen patterns with web interface
- **Problems solved**: Reduces manual code review cycles and improves code quality through automated collaboration
- **User impact**: Provides an interactive platform for high-quality code generation

## What
A web-based application featuring:
- **Backend**: Flask server with AutoGen multi-agent orchestration
- **Frontend**: HTML/CSS/JavaScript interface with real-time streaming
- **Agents**: CodeGenerator, QualityChecker, CodeOptimizer, UserProxy
- **Configuration**: YAML-based multi-model support (DeepSeek, Moonshot, Alibaba, Ollama)
- **Workflow**: Real-time agent collaboration with user approval gates

### Success Criteria
- [ ] Three specialized agents successfully collaborate using RoundRobinGroupChat
- [ ] Flask backend provides RESTful API with streaming responses
- [ ] Frontend displays real-time agent conversations with syntax highlighting
- [ ] Multi-model configuration system supports provider switching
- [ ] User approval workflow enables human oversight
- [ ] Code safety scanning prevents malicious code generation
- [ ] All tests pass and system handles errors gracefully

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html
  why: Core AutoGen patterns, agent types, team configurations
  
- url: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/models.html
  why: Model client configuration and multi-provider setup
  
- file: examples/app_team.py
  why: RoundRobinGroupChat pattern, streaming, termination conditions
  
- file: examples/app_team_user_proxy.py
  why: UserProxyAgent integration, user input/action functions
  
- file: examples/flask_server.py
  why: Flask Blueprint architecture pattern for web services
  
- file: examples/model_config.yaml
  why: Model configuration structure
  
- file: examples/model_config_template.yaml
  why: Multi-provider model configuration examples
  
- file: examples/README.md
  why: AutoGen setup patterns and best practices
  
- file: CLAUDE.md
  why: Project conventions, modularity rules, testing requirements
```

### Current Codebase Tree
```bash
.
├── examples/
│   ├── README.md                    # AutoGen usage guide
│   ├── app_team.py                  # Multi-agent team example
│   ├── app_team_user_proxy.py       # UserProxy integration
│   ├── flask_server.py              # Flask Blueprint pattern
│   ├── model_config.yaml            # Model configuration
│   └── model_config_template.yaml   # Multi-provider template
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md              # PRP template
│   └── EXAMPLE_multi_agent_prp.md   # Multi-agent example
├── CLAUDE.md                        # Project conventions
├── INITIAL.md                       # Feature specification
└── README.md                        # Project documentation
```

### Desired Codebase Tree with Files to Add
```bash
.
├── agents/
│   ├── __init__.py                  # Package initialization
│   ├── code_generator.py            # Code generation specialist agent
│   ├── quality_checker.py           # Code quality analysis agent
│   ├── code_optimizer.py            # Code optimization specialist agent
│   └── user_proxy.py                # User interaction proxy agent
├── models/
│   ├── __init__.py                  # Package initialization
│   ├── providers.py                 # Multi-provider model clients
│   └── config.py                    # Model configuration management
├── web/
│   ├── __init__.py                  # Package initialization
│   ├── app.py                       # Main Flask application
│   ├── routes.py                    # API route definitions
│   └── static/
│       ├── index.html               # Main frontend interface
│       ├── style.css                # Styling and responsive design
│       └── app.js                   # Frontend JavaScript logic
├── utils/
│   ├── __init__.py                  # Package initialization
│   ├── streaming.py                 # Real-time streaming utilities
│   ├── security.py                  # Code safety scanning
│   └── session.py                   # User session management
├── config/
│   ├── __init__.py                  # Package initialization
│   ├── models.yaml                  # Multi-provider model configuration
│   └── agents.yaml                  # Agent system prompts and settings
├── tests/
│   ├── __init__.py                  # Package initialization
│   ├── test_agents.py               # Agent behavior tests
│   ├── test_models.py               # Model provider tests
│   ├── test_web.py                  # Flask API tests
│   └── test_integration.py          # End-to-end integration tests
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── run.py                           # Application entry point
└── venv_linux/                      # Virtual environment (existing)
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: AutoGen requires async throughout - use run_stream for real-time output
# CRITICAL: RoundRobinGroupChat needs TextMentionTermination for proper endings
# CRITICAL: ModelClientStreamingChunkEvent requires proper message handling
# CRITICAL: Flask-SocketIO needed for real-time frontend updates
# CRITICAL: UserProxyAgent requires input_func and action_func for human interaction
# CRITICAL: ChatCompletionClient.load_component() for model configuration
# CRITICAL: CancellationToken() required for all agent operations
# CRITICAL: Session management needed for multi-user web application
# CRITICAL: Code safety scanning essential to prevent malicious generation
# CRITICAL: YAML configuration must support multiple provider formats
# CRITICAL: Always use venv_linux for Python execution
# CRITICAL: File size limit: never create files >500 lines
```

## Implementation Blueprint

### Data Models and Structure

```python
# models/config.py - Configuration management
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

class ModelProvider(str, Enum):
    DEEPSEEK = "deepseek"
    MOONSHOT = "moonshot"
    ALIBABA = "alibaba_bailian"
    OLLAMA = "ollama"
    OPENAI = "openai"

class ModelConfig(BaseModel):
    provider: ModelProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str
    config: Dict[str, Any] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    model: str
    system_prompt: str
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2000, ge=1, le=8000)

class CodeGenerationRequest(BaseModel):
    requirements: str = Field(..., min_length=10)
    language: str = Field("python", regex="^(python|javascript|java|go|rust)$")
    context: Optional[str] = None
    max_iterations: int = Field(3, ge=1, le=10)

class AgentResponse(BaseModel):
    agent_name: str
    message: str
    timestamp: str
    message_type: str = Field("message", regex="^(message|tool_use|error|termination)$")
```

### List of Tasks to Complete in Order

```yaml
Task 1: Setup Project Structure and Configuration
CREATE config/models.yaml:
  - PATTERN: Follow examples/model_config_template.yaml structure
  - Support DeepSeek, Moonshot, Alibaba, Ollama providers
  - Include API key placeholders and configuration options
  
CREATE config/agents.yaml:
  - Define system prompts for each specialized agent
  - Set model assignments and parameters
  - Configure termination conditions and workflows

CREATE .env.example:
  - Include all required environment variables
  - API keys for supported model providers
  - Flask configuration variables

Task 2: Implement Model Provider System
CREATE models/providers.py:
  - PATTERN: Use ChatCompletionClient.load_component() like examples
  - Support dynamic provider switching
  - Handle authentication and configuration per provider
  - Implement fallback mechanisms for reliability

CREATE models/config.py:
  - PATTERN: Use pydantic for configuration validation
  - Load YAML configurations with proper error handling
  - Provide configuration hot-reloading capabilities

Task 3: Create Specialized Agents
CREATE agents/code_generator.py:
  - PATTERN: Follow examples/app_team.py AssistantAgent structure
  - System prompt for code generation expertise
  - Enable model_client_stream=True for real-time output
  - Input validation and requirements parsing

CREATE agents/quality_checker.py:
  - PATTERN: Similar to critic agent in examples/app_team.py
  - System prompt for code quality analysis
  - Security scanning integration
  - Best practices evaluation

CREATE agents/code_optimizer.py:
  - PATTERN: AssistantAgent with optimization focus
  - Performance analysis and improvement suggestions
  - Code refactoring recommendations

CREATE agents/user_proxy.py:
  - PATTERN: Follow examples/app_team_user_proxy.py
  - Implement input_func and action_func
  - Handle user approval/rejection workflow
  - Session state management

Task 4: Implement Web Backend
CREATE web/app.py:
  - PATTERN: Flask application factory pattern
  - Blueprint registration for modular design
  - CORS configuration for frontend communication
  - Session management and security

CREATE web/routes.py:
  - PATTERN: Flask Blueprint like examples/flask_server.py
  - POST /api/generate - initiate code generation
  - GET /api/stream - real-time agent communication
  - POST /api/approve - user approval endpoint
  - GET /api/status - session status and health

CREATE utils/streaming.py:
  - PATTERN: Handle ModelClientStreamingChunkEvent from examples
  - WebSocket or Server-Sent Events for real-time updates
  - Message queuing and delivery management

Task 5: Create Frontend Interface
CREATE web/static/index.html:
  - Responsive design with agent conversation display
  - Code syntax highlighting using Prism.js
  - Real-time message streaming interface
  - User approval/rejection controls

CREATE web/static/style.css:
  - Modern responsive design
  - Agent-specific color coding
  - Code block styling and syntax highlighting
  - Mobile-friendly layout

CREATE web/static/app.js:
  - WebSocket connection for real-time updates
  - Message rendering with agent identification
  - Code copying functionality
  - User interaction handling

Task 6: Implement Multi-Agent Orchestration
CREATE utils/session.py:
  - PATTERN: Use RoundRobinGroupChat like examples/app_team.py
  - Session-based agent state management
  - Multi-user support with isolation
  - Conversation history tracking

MODIFY agents/__init__.py:
  - Agent factory functions
  - Team composition and configuration
  - Termination condition setup using TextMentionTermination

Task 7: Add Security and Utilities
CREATE utils/security.py:
  - Code safety scanning for malicious patterns
  - Input sanitization and validation
  - Rate limiting and abuse prevention

CREATE run.py:
  - PATTERN: Application entry point
  - Environment validation
  - Database initialization if needed
  - Development vs production configuration

Task 8: Comprehensive Testing
CREATE tests/test_agents.py:
  - PATTERN: Mirror examples test structure
  - Mock model responses for consistent testing
  - Test agent collaboration and termination
  - Validate system prompts and behavior

CREATE tests/test_models.py:
  - Model provider configuration testing
  - Authentication and connection validation
  - Fallback mechanism testing

CREATE tests/test_web.py:
  - Flask API endpoint testing
  - WebSocket connection testing
  - Session management validation

CREATE tests/test_integration.py:
  - End-to-end workflow testing
  - Multi-agent collaboration validation
  - Frontend-backend integration testing

Task 9: Documentation and Deployment
UPDATE README.md:
  - Installation and setup instructions
  - Configuration guide for multiple providers
  - Usage examples and API documentation
  - Architecture overview and design decisions

CREATE requirements.txt:
  - All necessary dependencies
  - Version pinning for stability
  - Development vs production dependencies
```

### Per Task Pseudocode

```python
# Task 3: Code Generator Agent
# agents/code_generator.py
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient

async def create_code_generator(model_client: ChatCompletionClient) -> AssistantAgent:
    """Create specialized code generation agent."""
    # PATTERN: Follow examples/app_team.py structure
    system_prompt = """
    You are an expert software engineer specializing in clean, efficient code generation.
    
    Your responsibilities:
    - Generate well-structured, documented code based on requirements
    - Follow language-specific best practices and conventions
    - Include proper error handling and edge case considerations
    - Provide clear explanations of implementation choices
    
    Always respond with complete, runnable code and explanations.
    """
    
    return AssistantAgent(
        name="code_generator",
        model_client=model_client,
        system_message=system_prompt,
        model_client_stream=True,  # CRITICAL: Enable streaming
    )

# Task 4: Web Routes Implementation
# web/routes.py
from flask import Blueprint, request, jsonify, session
from utils.streaming import StreamingManager
from agents import create_agent_team

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate', methods=['POST'])
async def generate_code():
    """Initiate code generation workflow."""
    # PATTERN: Session-based agent management
    data = request.get_json()
    session_id = session.get('session_id', str(uuid.uuid4()))
    
    # CRITICAL: Validate input using pydantic
    try:
        req = CodeGenerationRequest(**data)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    
    # Create agent team for this session
    team = await create_agent_team(session_id, req.language)
    
    # PATTERN: Use run_stream like examples/app_team.py
    stream_manager = StreamingManager(session_id)
    
    # Start async task for agent collaboration
    task = asyncio.create_task(
        process_generation_request(team, req, stream_manager)
    )
    
    return jsonify({
        "session_id": session_id,
        "status": "started",
        "stream_url": f"/api/stream/{session_id}"
    })

# Task 6: Multi-Agent Orchestration
# utils/session.py
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

async def create_agent_team(session_id: str, language: str) -> RoundRobinGroupChat:
    """Create specialized agent team for code generation."""
    # PATTERN: Follow examples/app_team.py team creation
    
    # Load model configuration
    model_client = ChatCompletionClient.load_component(model_config)
    
    # Create specialized agents
    generator = await create_code_generator(model_client)
    checker = await create_quality_checker(model_client)
    optimizer = await create_code_optimizer(model_client)
    user_proxy = await create_user_proxy(session_id)
    
    # CRITICAL: Termination condition for workflow control
    termination = TextMentionTermination("APPROVE", sources=["user_proxy"])
    
    # Create team with round-robin collaboration
    team = RoundRobinGroupChat(
        [generator, checker, optimizer, user_proxy],
        termination_condition=termination
    )
    
    return team
```

### Integration Points
```yaml
ENVIRONMENT:
  - add to: .env
  - vars: |
      # Flask Configuration
      FLASK_ENV=development
      SECRET_KEY=your-secret-key-here
      
      # Model Provider Configuration
      DEEPSEEK_API_KEY=sk-...
      MOONSHOT_API_KEY=sk-...
      ALIBABA_API_KEY=sk-...
      OLLAMA_BASE_URL=http://localhost:11434
      
      # Security Configuration
      CODE_SAFETY_ENABLED=true
      MAX_CONCURRENT_SESSIONS=10
      
VIRTUAL_ENVIRONMENT:
  - Always use: venv_linux for Python execution
  - Activation: source venv_linux/bin/activate
  - Package installation: pip install -r requirements.txt
  
DEPENDENCIES:
  - autogen-agentchat: AutoGen framework
  - autogen-ext: Model provider extensions
  - flask: Web framework
  - flask-socketio: Real-time communication
  - pydantic: Data validation
  - pyyaml: Configuration management
  - python-dotenv: Environment management
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# CRITICAL: Run in venv_linux environment
source venv_linux/bin/activate

# Fix style issues automatically
ruff check . --fix

# Type checking validation
mypy agents/ models/ web/ utils/

# Expected: No errors. If errors exist, read carefully and fix.
```

### Level 2: Unit Tests
```python
# tests/test_agents.py
import pytest
from unittest.mock import AsyncMock, patch
from agents.code_generator import create_code_generator

@pytest.mark.asyncio
async def test_code_generator_creation():
    """Test code generator agent creation and configuration."""
    mock_client = AsyncMock()
    agent = await create_code_generator(mock_client)
    
    assert agent.name == "code_generator"
    assert agent.model_client_stream is True
    assert "expert software engineer" in agent.system_message

@pytest.mark.asyncio
async def test_agent_collaboration():
    """Test multi-agent team collaboration workflow."""
    with patch('models.providers.ChatCompletionClient') as mock_client:
        team = await create_agent_team("test_session", "python")
        
        # Test team composition
        assert len(team.agents) == 4
        assert any(agent.name == "code_generator" for agent in team.agents)
        assert any(agent.name == "quality_checker" for agent in team.agents)

# tests/test_web.py
import pytest
from web.app import create_app

def test_generate_endpoint():
    """Test code generation API endpoint."""
    app = create_app(testing=True)
    client = app.test_client()
    
    response = client.post('/api/generate', json={
        "requirements": "Create a function to sort a list",
        "language": "python"
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert "session_id" in data
    assert data["status"] == "started"
```

```bash
# Run comprehensive test suite
source venv_linux/bin/activate
pytest tests/ -v --cov=agents --cov=models --cov=web --cov=utils --cov-report=term-missing

# If failing: Debug specific test, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Start the application
source venv_linux/bin/activate
python run.py

# Test web interface
curl -X POST http://localhost:5011/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": "Create a Python function that calculates fibonacci numbers",
    "language": "python",
    "context": "Educational example with clear documentation"
  }'

# Expected response:
# {
#   "session_id": "uuid-here",
#   "status": "started", 
#   "stream_url": "/api/stream/uuid-here"
# }

# Test streaming endpoint
curl -N http://localhost:5011/api/stream/[session_id]

# Expected: Server-sent events with agent messages
# data: {"agent": "code_generator", "message": "I'll create a fibonacci function...", "type": "message"}
# data: {"agent": "quality_checker", "message": "The code looks good, but...", "type": "message"}

# Open browser to http://localhost:5011 for full frontend testing
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check .`
- [ ] No type errors: `mypy agents/ models/ web/ utils/`
- [ ] Flask application starts without errors
- [ ] Frontend loads and displays correctly
- [ ] Agent collaboration workflow completes successfully
- [ ] Real-time streaming works in browser
- [ ] User approval/rejection workflow functions
- [ ] Multi-model configuration switching works
- [ ] Code safety scanning prevents malicious output
- [ ] Session management isolates users properly
- [ ] Error handling provides informative messages
- [ ] Documentation is comprehensive and accurate

---

## Anti-Patterns to Avoid
- ❌ Don't create files longer than 500 lines - refactor into modules
- ❌ Don't hardcode model configurations - use YAML files
- ❌ Don't skip security scanning for generated code
- ❌ Don't use sync functions in async agent context
- ❌ Don't ignore session isolation in multi-user scenarios
- ❌ Don't forget CancellationToken for agent operations
- ❌ Don't skip proper error handling in streaming responses
- ❌ Don't use relative imports - use absolute imports
- ❌ Don't commit API keys or sensitive configuration
- ❌ Don't skip virtual environment usage (venv_linux)

## Confidence Score: 9/10

High confidence due to:
- Clear examples available in codebase for AutoGen patterns
- Well-defined Flask Blueprint architecture reference
- Established streaming patterns from examples
- Comprehensive validation gates with specific commands
- Detailed implementation blueprint with pseudocode
- CLAUDE.md conventions clearly defined

Minor uncertainty on:
- Chinese language requirements in system prompts (can be adapted)
- Specific model provider API quirks (will be discovered during implementation)