# Development Guide

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Adding New Tools](#adding-new-tools)
- [Testing](#testing)
- [Debugging](#debugging)
- [Contributing](#contributing)

## Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git
- GitHub PAT Token - for GitHub tool (see [GITHUB_REST_API.md](GITHUB_REST_API.md))
- OpenCode CLI (`opencode`) - for OpenCode tool
- Ollama - for local LLM inference

### Setup Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/pyagent.git
   cd pyagent
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install development tools**:
   ```bash
   pip install ruff black isort
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Slack tokens
   ```

6. **Run the bot**:
   ```bash
   python agent.py
   ```

## Project Structure

```
pyagent/
├── src/
│   ├── integrations/          # External service clients
│   │   ├── slack_client.py    # Slack Bolt wrapper
│   │   └── ollama_client.py   # LangChain Ollama integration
│   ├── models/                # Data models
│   │   ├── config.py          # Configuration management
│   │   └── messages.py        # Message data models
│   ├── prompts/               # Prompt templates
│   │   ├── templates/
│   │   │   └── system_prompt.j2
│   │   └── prompt_manager.py
│   ├── tools/                 # LangChain tools
│   │   ├── github_tool.py     # GitHub REST API client
│   │   ├── opencode_tool.py   # OpenCode CLI wrapper
│   │   └── ollama_tool.py     # Ollama generation
│   └── orchestrator.py        # Main orchestration logic
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md
│   ├── USAGE.md
│   ├── DOCKER.md
│   └── DEVELOPMENT.md
├── output/                    # Long output storage
├── agent.py                   # Entry point
├── requirements.txt           # Dependencies
├── .env.example              # Environment template
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker compose config
└── README.md                 # Project overview
```

## Code Style

We follow PEP 8 with some specific conventions:

### Formatting

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings, single for dict keys

**Tools**:
```bash
# Format code
black .

# Sort imports
isort .

# Both at once
black . && isort .
```

### Type Hints

Use type hints for all function arguments and return values:

```python
from typing import Optional, List

def process_message(
    message: str,
    timeout: int = 30,
) -> dict[str, Any]:
    """Process a message and return results."""
    ...
```

### Imports

Group imports by type:

```python
# Standard library
import os
from typing import TYPE_CHECKING, List, Optional

# Third-party
from langchain.tools import tool
from pydantic import BaseModel

# Local
from src.models.config import Config

if TYPE_CHECKING:
    from src.orchestrator import AgentOrchestrator
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Error Handling

- Raise specific exceptions with clear messages
- No silent failures
- Log errors appropriately
- Never expose secrets in errors

```python
# Good
if not response.ok:
    raise RuntimeError(f"API request failed: {response.status_code} - {response.text}")

# Bad
if not response.ok:
    pass  # Silent failure
```

### Linting

Use Ruff for fast linting:

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Check specific file
ruff check src/orchestrator.py
```

## Adding New Tools

### Step 1: Create Tool File

Create a new file in `src/tools/`:

```python
# src/tools/my_tool.py

from langchain.tools import tool
from src.models.config import Config

@tool
def my_tool(command: str, config: Config) -> str:
    """
    Execute my custom tool.
    
    Args:
        command: The command to execute
        config: Application configuration
        
    Returns:
        Tool output as string
        
    Raises:
        RuntimeError: If execution fails
    """
    try:
        # Your tool implementation here
        result = execute_command(command)
        return result
    except Exception as e:
        raise RuntimeError(f"My tool failed: {str(e)}")

def execute_command(command: str) -> str:
    """Helper function to execute the command."""
    # Implementation
    return "result"
```

### Step 2: Register Tool in Orchestrator

Edit `src/orchestrator.py`:

```python
from src.tools.github_tool import github
from src.tools.opencode_tool import opencode
from src.tools.ollama_tool import ollama_generate
from src.tools.my_tool import my_tool  # Add import

class AgentOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.tools = [
            github,
            opencode,
            ollama_generate,
            my_tool,  # Add to list
        ]
        # ... rest of initialization
```

### Step 3: Update System Prompt

Edit `src/prompts/templates/system_prompt.j2` to describe your tool:

```jinja2
You have access to the following tools:

1. github: Execute GitHub REST API commands
   Usage: Provide natural language command (e.g., "repo list", "pr create")
   
2. opencode: Execute OpenCode CLI commands
   Usage: Provide opencode command arguments
   
3. my_tool: [Description of what your tool does]
   Usage: [How to use it]
   
   Examples:
   - [Example 1]
   - [Example 2]
```

### Step 4: Add Slash Command Support (Optional)

If you want to support `/mytool` slash commands, update `src/orchestrator.py`:

```python
def _parse_slash_commands(self, message: str) -> list[tuple[str, str]]:
    """Parse slash commands from message."""
    commands = []
    
    # Add your command prefix
    patterns = [
        (r'/git\s+(.+)', self.github),
        (r'/opencode\s+(.+)', self.opencode),
        (r'/ollama\s+(.+)', self.ollama_generate),
        (r'/mytool\s+(.+)', my_tool),  # Add this
    ]
    
    # ... rest of parsing logic
```

### Step 5: Test Your Tool

1. **Unit test** (create `tests/test_my_tool.py`):
   ```python
   from src.tools.my_tool import my_tool
   from src.models.config import Config
   
   def test_my_tool():
       config = Config.from_env()
       result = my_tool("test command", config)
       assert result is not None
   ```

2. **Integration test**:
   ```bash
   # Start bot
   python agent.py
   
   # In Slack, test:
   @bot /mytool test command
   ```

3. **Natural language test**:
   ```
   @bot use my tool to do something
   ```

## Testing

### Manual Testing

Currently, the project relies on manual testing. Follow these steps:

1. **Start the bot**:
   ```bash
   python agent.py
   ```

2. **Test slash commands**:
   ```
   @bot /git status
   @bot /opencode create a hello world function
   @bot /ollama explain Python decorators
   ```

3. **Test natural language**:
   ```
   @bot list my repositories
   @bot create a Python script
   @bot explain how async works
   ```

4. **Test error handling**:
   ```
   @bot /git invalid-command
   @bot /opencode [malformed input]
   ```

5. **Test multiple commands**:
   ```
   @bot /git status /opencode review changes
   ```

### Automated Testing (Future)

Planned improvements include:

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_orchestrator.py
```

## Debugging

### Enable Verbose Logging

Edit `src/orchestrator.py`:

```python
def __init__(self, config: Config):
    # ... existing code ...
    
    # Enable LangChain verbose mode
    self.agent = create_agent(
        llm=self.llm,
        tools=self.tools,
        verbose=True,  # Set to True
    )
```

### Check Logs

The bot prints logs to stdout:

```bash
python agent.py 2>&1 | tee bot.log
```

### Common Issues

#### Tool Not Found

**Symptom**: `ModuleNotFoundError: No module named 'src.tools.my_tool'`

**Solution**: 
- Check file exists in `src/tools/`
- Verify import in `orchestrator.py`
- Ensure `__init__.py` exists in `src/tools/`

#### Tool Not Executing

**Symptom**: Agent doesn't call your tool

**Solution**:
- Check system prompt includes tool description
- Verify tool is in `self.tools` list
- Test with explicit slash command first
- Check LangChain verbose output

#### Import Errors

**Symptom**: Circular import errors

**Solution**:
- Use `TYPE_CHECKING` for type hints
- Import inside functions if needed
- Restructure code to avoid cycles

### Debugging Tools

```python
# Print available tools
print(f"Tools: {[t.name for t in orchestrator.tools]}")

# Test tool directly
from src.tools.my_tool import my_tool
result = my_tool("test", config)
print(result)

# Check LangChain agent
print(orchestrator.agent.agent.llm_chain.prompt.template)
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-tool
   ```

3. **Make changes**:
   - Write code
   - Follow code style guidelines
   - Test thoroughly

4. **Run linting**:
   ```bash
   ruff check .
   black .
   isort .
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "Add: Description of changes"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/my-new-tool
   ```

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**: What changes and why
- **Testing**: How you tested
- **Documentation**: Update docs if needed
- **Breaking changes**: Note any breaking changes

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Type hints added
- [ ] Error handling implemented
- [ ] No secrets in code
- [ ] Documentation updated
- [ ] Tested manually
- [ ] Linting passes

## Architecture Decisions

### Why LangChain?

- **Pros**:
  - Native Ollama integration
  - Clean tool abstraction
  - Built-in agent loop
  - Good documentation
  
- **Cons**:
  - Adds dependency
  - Can be verbose
  - Learning curve

### Why Sequential Execution?

- **Pros**:
  - Predictable behavior
  - Easy debugging
  - Clear failure points
  
- **Cons**:
  - Slower than parallel
  - No optimization

### Why No Fallbacks?

- **Pros**:
  - Explicit behavior
  - Clear errors
  - User knows what happened
  
- **Cons**:
  - Less robust
  - Requires retry

## Performance Optimization

### Reduce Latency

1. **Use slash commands**: Faster than natural language
2. **Smaller model**: Use smaller Ollama model
3. **Caching**: Cache frequent operations (not yet implemented)
4. **Parallel execution**: For independent operations (not yet implemented)

### Reduce Memory Usage

1. **Minimal dependencies**: Only what's needed
2. **Stream responses**: Instead of buffering (not yet implemented)
3. **Cleanup outputs**: Periodic cleanup of `output/` directory

## Future Improvements

See [ARCHITECTURE.md](ARCHITECTURE.md) for planned enhancements.
