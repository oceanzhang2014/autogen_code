### 🔄 Project Awareness & Context
- **Always read `INITIAL.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check `TASK.md`** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `INITIAL.md`.
- **Use venv_linux** (the virtual environment) whenever executing Python commands, including for unit tests.

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
  For AutoGen multi-agent systems this looks like:
    - `agents/` - Directory containing agent definitions
      - `code_generator.py` - Code generation agent
      - `quality_checker.py` - Code quality checking agent  
      - `code_optimizer.py` - Code optimization agent
      - `user_proxy.py` - User interaction proxy agent
    - `models/` - Model client configurations and management
      - `providers.py` - Model provider implementations (DeepSeek, Moonshot, etc.)
      - `config.py` - Model configuration loading and validation
    - `web/` - Flask web application
      - `app.py` - Main Flask application
      - `routes.py` - API routes and endpoints
      - `static/` - Frontend HTML/CSS/JS files
    - `utils/` - Shared utilities and helpers
    - `config/` - Configuration files (YAML model configs)
- **Use clear, consistent imports** (prefer relative imports within packages).
- **Use python_dotenv and load_dotenv()** for environment variables.

### 🧪 Testing & Reliability
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case

### ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- Add new sub-tasks or TODOs discovered during development to `TASK.md` under a “Discovered During Work” section.

### 📎 Style & Conventions
- **Use Python** as the primary language.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for data validation**.
- Use `Flask` for web APIs and `SQLAlchemy` or `SQLModel` for ORM if applicable.
- **AutoGen-specific conventions**:
  - Use `AsyncIO` for all agent interactions and streaming
  - Implement proper error handling for agent failures and model timeouts
  - Use YAML configuration files for model and agent settings
  - Follow AutoGen naming conventions for agents (CamelCase for classes, snake_case for instances)
- Write **docstrings for every function** using the Google style:
  ```python
  async def create_agent(name: str, model_config: dict) -> AssistantAgent:
      """
      Create an AutoGen assistant agent with specified configuration.

      Args:
          name (str): Agent name identifier.
          model_config (dict): Model client configuration dictionary.

      Returns:
          AssistantAgent: Configured AutoGen agent instance.
      """
  ```

### 📚 Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.
- **AutoGen-specific rules**:
  - Always use `CancellationToken()` for agent operations that might need interruption
  - Implement proper session management for multi-user web applications
  - Use streaming patterns (`run_stream`, `on_messages_stream`) for real-time UI updates
  - Handle `ModelClientStreamingChunkEvent` and `TaskResult` message types appropriately
  - Never hard-code model configurations - always load from YAML files
  - Implement graceful degradation when agents fail or models are unavailable

### 🤖 Multi-Agent System Guidelines  
- **Agent Design Principles**:
  - Each agent should have a single, well-defined responsibility
  - Use clear, descriptive system prompts that define agent behavior
  - Implement proper termination conditions for agent conversations
  - Design agents to be stateless and session-independent
- **Team Coordination**:
  - Use `RoundRobinGroupChat` for sequential agent interactions
  - Implement `TextMentionTermination` for controlled conversation endings
  - Handle user approval/rejection flows through `UserProxyAgent`
  - Maintain conversation history and context across agent interactions
- **Model Management**:
  - Support multiple model providers simultaneously
  - Allow runtime model switching for different agents
  - Implement model fallback mechanisms for reliability
  - Monitor model usage and implement rate limiting if needed