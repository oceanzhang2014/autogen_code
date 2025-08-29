# AutoGen Multi-Agent Code Generation System

A production-ready AutoGen multi-agent system that enables collaborative code generation using specialized AI agents. Built with Flask backend, real-time streaming, and multi-provider model support.

> **Implemented using Context Engineering principles - a comprehensive approach to AI system development.**

## 🌟 Features

- **4 Specialized Agents**: CodeGenerator, QualityChecker, CodeOptimizer, UserProxy
- **Multi-Provider Support**: DeepSeek, Moonshot, Alibaba, OpenAI, Ollama
- **Real-time Streaming**: Live updates during agent collaboration
- **Web Interface**: Modern HTML/CSS/JS frontend with user approval workflow
- **Security Built-in**: Code safety scanning and input validation
- **Production Ready**: Comprehensive testing, error handling, and deployment guides

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd Context-Engineering-Intro

# 2. Set up virtual environment
conda activate autogen-project
# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run the application
python run.py

# 6. Open browser
# Visit http://localhost:5011
```

**📖 For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

## 📚 Table of Contents

- [System Architecture](#system-architecture)
- [Agent Roles](#agent-roles)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Context Engineering Background](#context-engineering-background)

## 🏗️ System Architecture

The system follows a multi-agent architecture using Microsoft AutoGen framework:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │───▶│   Flask Backend  │───▶│  Agent Manager  │
│                 │    │                  │    │                 │
│ • HTML/CSS/JS   │    │ • REST API       │    │ • Session Mgmt  │
│ • Real-time UI  │    │ • Streaming      │    │ • Orchestration │
│ • User Approval │    │ • Session Mgmt   │    │ • Error Handling│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                               ┌─────────▼─────────┐
                                               │ RoundRobinGroupChat│
                                               └─────────┬─────────┘
                      ┌────────────────────────────────┼────────────────────────────────┐
                      │                                │                                │
            ┌─────────▼──────────┐            ┌─────────▼──────────┐            ┌─────────▼──────────┐
            │   CodeGenerator    │            │  QualityChecker    │            │  CodeOptimizer     │
            │                    │            │                    │            │                    │
            │ • Requirements     │            │ • Code Review      │            │ • Performance      │
            │ • Implementation   │            │ • Best Practices   │            │ • Optimization     │
            │ • Documentation    │            │ • Security Scan    │            │ • Refactoring      │
            └────────────────────┘            └────────────────────┘            └────────────────────┘
                                                         │
                                               ┌─────────▼──────────┐
                                               │   UserProxy        │
                                               │                    │
                                               │ • User Interaction │
                                               │ • Approval Flow    │
                                               │ • Final Decision   │
                                               └────────────────────┘
```

## 🤖 Agent Roles

### CodeGenerator Agent
- **Purpose**: Primary code implementation
- **Responsibilities**: 
  - Analyze requirements and create initial code
  - Follow language best practices
  - Generate comprehensive documentation
  - Handle complex logic implementation

### QualityChecker Agent  
- **Purpose**: Code quality assurance
- **Responsibilities**:
  - Review code for bugs and issues
  - Ensure coding standards compliance
  - Perform security analysis
  - Validate against requirements

### CodeOptimizer Agent
- **Purpose**: Performance and efficiency optimization
- **Responsibilities**:
  - Optimize algorithm efficiency
  - Improve code structure and readability
  - Suggest performance enhancements
  - Refactor for maintainability

### UserProxy Agent
- **Purpose**: Human-AI interaction bridge
- **Responsibilities**:
  - Present final code to user
  - Handle approval/rejection workflow
  - Manage user feedback integration
  - Control conversation termination

## 🔌 API Endpoints

### POST `/api/generate`
Start code generation workflow
```json
{
  "requirements": "Create a function to calculate prime numbers",
  "language": "python",
  "context": "For use in mathematical computations",
  "max_iterations": 3
}
```

### GET `/api/stream/{session_id}`
Real-time agent collaboration stream (Server-Sent Events)

### POST `/api/approve` 
User approval/rejection of generated code
```json
{
  "session_id": "uuid",
  "action": "approve|reject",
  "feedback": "Optional feedback message"
}
```

### GET `/api/status/{session_id}`
Get session status and information

### GET `/api/models`
List available model configurations

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Required
SECRET_KEY=your-secret-key
DEEPSEEK_API_KEY=your-api-key

# Optional model providers
MOONSHOT_API_KEY=your-moonshot-key
ALIBABA_API_KEY=your-alibaba-key
OPENAI_API_KEY=your-openai-key
OLLAMA_BASE_URL=http://localhost:11434

# Application settings
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO
```

### Model Configuration (config/models.yaml)
```yaml
models:
  deepseek:
    provider: "deepseek"
    config:
      model: "deepseek-chat"
      api_key: "${DEEPSEEK_API_KEY}"
      base_url: "https://api.deepseek.com"
```

### Agent Configuration (config/agents.yaml)
```yaml
agents:
  code_generator:
    system_prompt: "You are a senior software engineer..."
    temperature: 0.7
    max_tokens: 2000
```

## 💻 Development

### Project Structure
```
├── agents/                 # Agent implementations
│   ├── code_generator.py
│   ├── quality_checker.py
│   ├── code_optimizer.py
│   └── user_proxy.py
├── config/                 # Configuration files
│   ├── models.yaml
│   └── agents.yaml
├── models/                 # Model management
│   ├── config.py
│   └── providers.py
├── utils/                  # Utilities
│   ├── security.py
│   ├── session.py
│   └── streaming.py
├── web/                    # Flask application
│   ├── app.py
│   ├── routes.py
│   └── static/
├── tests/                  # Test suite
└── run.py                  # Application entry point
```

### Adding New Agents
1. Create agent file in `agents/`
2. Add configuration to `config/agents.yaml`
3. Update team creation in `utils/session.py`
4. Add tests in `tests/test_agents.py`

### Adding Model Providers
1. Add provider config to `config/models.yaml`
2. Update `models/providers.py` if needed
3. Test with health check endpoint

## 🧪 Testing

Run the comprehensive test suite:
```bash
# All tests (43 tests)
python -m pytest tests/ -v

# Specific test categories
python -m pytest tests/test_agents.py -v      # Agent tests
python -m pytest tests/test_web.py -v        # Web API tests
python -m pytest tests/test_models.py -v     # Model tests
python -m pytest tests/test_integration.py -v # Integration tests

# Coverage report
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Categories
- **Agent Tests**: Agent creation, configuration, behavior
- **Web Tests**: API endpoints, request handling, CORS
- **Model Tests**: Configuration validation, provider management
- **Integration Tests**: End-to-end workflows, error handling

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions including:

- Environment setup
- Production configuration
- Docker deployment
- Scaling considerations
- Security best practices
- Monitoring and logging

### Quick Production Start
```bash
# Using Gunicorn (Linux/macOS)
gunicorn -w 4 -b 0.0.0.0:5011 --timeout 300 "web.app:create_app()"

# Using Waitress (Windows)
waitress-serve --host=0.0.0.0 --port=5000 --call web.app:create_app
```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Log Files**: `autogen_system.log`
- **Metrics**: Response times, model usage, session counts
- **Errors**: Automatic error tracking and logging

---

## Context Engineering Background

Context Engineering represents a paradigm shift from traditional prompt engineering:

### Prompt Engineering vs Context Engineering

**Prompt Engineering:**
- Focuses on clever wording and specific phrasing
- Limited to how you phrase a task
- Like giving someone a sticky note

**Context Engineering:**
- A complete system for providing comprehensive context
- Includes documentation, examples, rules, patterns, and validation
- Like writing a full screenplay with all the details

### Why Context Engineering Matters

1. **Reduces AI Failures**: Most agent failures aren't model failures - they're context failures
2. **Ensures Consistency**: AI follows your project patterns and conventions
3. **Enables Complex Features**: AI can handle multi-step implementations with proper context
4. **Self-Correcting**: Validation loops allow AI to fix its own mistakes

## Template Structure

```
context-engineering-intro/
├── .claude/
│   ├── commands/
│   │   ├── generate-prp.md    # Generates comprehensive PRPs
│   │   └── execute-prp.md     # Executes PRPs to implement features
│   └── settings.local.json    # Claude Code permissions
├── PRPs/
│   ├── templates/
│   │   └── prp_base.md       # Base template for PRPs
│   └── EXAMPLE_multi_agent_prp.md  # Example of a complete PRP
├── examples/                  # Your code examples (critical!)
├── CLAUDE.md                 # Global rules for AI assistant
├── INITIAL.md               # Template for feature requests
├── INITIAL_EXAMPLE.md       # Example feature request
└── README.md                # This file
```

This template doesn't focus on RAG and tools with context engineering because I have a LOT more in store for that soon. ;)

## Step-by-Step Guide

### 1. Set Up Global Rules (CLAUDE.md)

The `CLAUDE.md` file contains project-wide rules that the AI assistant will follow in every conversation. The template includes:

- **Project awareness**: Reading planning docs, checking tasks
- **Code structure**: File size limits, module organization
- **Testing requirements**: Unit test patterns, coverage expectations
- **Style conventions**: Language preferences, formatting rules
- **Documentation standards**: Docstring formats, commenting practices

**You can use the provided template as-is or customize it for your project.**

### 2. Create Your Initial Feature Request

Edit `INITIAL.md` to describe what you want to build:

```markdown
## FEATURE:
[Describe what you want to build - be specific about functionality and requirements]

## EXAMPLES:
[List any example files in the examples/ folder and explain how they should be used]

## DOCUMENTATION:
[Include links to relevant documentation, APIs, or MCP server resources]

## OTHER CONSIDERATIONS:
[Mention any gotchas, specific requirements, or things AI assistants commonly miss]
```

**See `INITIAL_EXAMPLE.md` for a complete example.**

### 3. Generate the PRP

PRPs (Product Requirements Prompts) are comprehensive implementation blueprints that include:

- Complete context and documentation
- Implementation steps with validation
- Error handling patterns
- Test requirements

They are similar to PRDs (Product Requirements Documents) but are crafted more specifically to instruct an AI coding assistant.

Run in Claude Code:
```bash
/generate-prp INITIAL.md
```

**Note:** The slash commands are custom commands defined in `.claude/commands/`. You can view their implementation:
- `.claude/commands/generate-prp.md` - See how it researches and creates PRPs
- `.claude/commands/execute-prp.md` - See how it implements features from PRPs

The `$ARGUMENTS` variable in these commands receives whatever you pass after the command name (e.g., `INITIAL.md` or `PRPs/your-feature.md`).

This command will:
1. Read your feature request
2. Research the codebase for patterns
3. Search for relevant documentation
4. Create a comprehensive PRP in `PRPs/your-feature-name.md`

### 4. Execute the PRP

Once generated, execute the PRP to implement your feature:

```bash
/execute-prp PRPs/your-feature-name.md
```

The AI coding assistant will:
1. Read all context from the PRP
2. Create a detailed implementation plan
3. Execute each step with validation
4. Run tests and fix any issues
5. Ensure all success criteria are met

## Writing Effective INITIAL.md Files

### Key Sections Explained

**FEATURE**: Be specific and comprehensive
- ❌ "Build a web scraper"
- ✅ "Build an async web scraper using BeautifulSoup that extracts product data from e-commerce sites, handles rate limiting, and stores results in PostgreSQL"

**EXAMPLES**: Leverage the examples/ folder
- Place relevant code patterns in `examples/`
- Reference specific files and patterns to follow
- Explain what aspects should be mimicked

**DOCUMENTATION**: Include all relevant resources
- API documentation URLs
- Library guides
- MCP server documentation
- Database schemas

**OTHER CONSIDERATIONS**: Capture important details
- Authentication requirements
- Rate limits or quotas
- Common pitfalls
- Performance requirements

## The PRP Workflow

### How /generate-prp Works

The command follows this process:

1. **Research Phase**
   - Analyzes your codebase for patterns
   - Searches for similar implementations
   - Identifies conventions to follow

2. **Documentation Gathering**
   - Fetches relevant API docs
   - Includes library documentation
   - Adds gotchas and quirks

3. **Blueprint Creation**
   - Creates step-by-step implementation plan
   - Includes validation gates
   - Adds test requirements

4. **Quality Check**
   - Scores confidence level (1-10)
   - Ensures all context is included

### How /execute-prp Works

1. **Load Context**: Reads the entire PRP
2. **Plan**: Creates detailed task list using TodoWrite
3. **Execute**: Implements each component
4. **Validate**: Runs tests and linting
5. **Iterate**: Fixes any issues found
6. **Complete**: Ensures all requirements met

See `PRPs/EXAMPLE_multi_agent_prp.md` for a complete example of what gets generated.

## Using Examples Effectively

The `examples/` folder is **critical** for success. AI coding assistants perform much better when they can see patterns to follow.

### What to Include in Examples

1. **Code Structure Patterns**
   - How you organize modules
   - Import conventions
   - Class/function patterns

2. **Testing Patterns**
   - Test file structure
   - Mocking approaches
   - Assertion styles

3. **Integration Patterns**
   - API client implementations
   - Database connections
   - Authentication flows

4. **CLI Patterns**
   - Argument parsing
   - Output formatting
   - Error handling

### Example Structure

```
examples/
├── README.md           # Explains what each example demonstrates
├── cli.py             # CLI implementation pattern
├── agent/             # Agent architecture patterns
│   ├── agent.py      # Agent creation pattern
│   ├── tools.py      # Tool implementation pattern
│   └── providers.py  # Multi-provider pattern
└── tests/            # Testing patterns
    ├── test_agent.py # Unit test patterns
    └── conftest.py   # Pytest configuration
```

## Best Practices

### 1. Be Explicit in INITIAL.md
- Don't assume the AI knows your preferences
- Include specific requirements and constraints
- Reference examples liberally

### 2. Provide Comprehensive Examples
- More examples = better implementations
- Show both what to do AND what not to do
- Include error handling patterns

### 3. Use Validation Gates
- PRPs include test commands that must pass
- AI will iterate until all validations succeed
- This ensures working code on first try

### 4. Leverage Documentation
- Include official API docs
- Add MCP server resources
- Reference specific documentation sections

### 5. Customize CLAUDE.md
- Add your conventions
- Include project-specific rules
- Define coding standards

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Context Engineering Best Practices](https://www.philschmid.de/context-engineering)