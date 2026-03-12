# PyAgent - Intelligent Slack Bot with LangChain Orchestration

A Python Slack bot that integrates with Ollama and OpenCode CLI using LangChain for intelligent tool orchestration. Supports both natural language intent inference and explicit slash commands.

## Features

- **Dual Mode Operation**: Supports both slash commands and natural language intent inference
- **Intelligent Tool Selection**: Ollama LLM automatically selects appropriate tools based on context
- **Sequential Execution**: Tools execute in order, stopping on first failure
- **LangChain Orchestration**: Uses LangChain's agent framework for robust tool calling
- **Slack Integration**: Full Slack integration with threading support
- **Streaming Status Updates**: Real-time status updates via Slack message updates
- **Smart Output Handling**: Automatically uploads long outputs as files (>200 chars)

## Architecture

```
pyagent/
├── src/
│   ├── integrations/
│   │   ├── slack_client.py       # Slack Bolt wrapper with threading
│   │   └── ollama_client.py      # LangChain Ollama integration
│   ├── models/
│   │   ├── config.py             # Configuration management
│   │   └── messages.py           # Message data models
│   ├── prompts/
│   │   ├── templates/
│   │   │   └── system_prompt.j2  # Jinja2 system prompt
│   │   └── prompt_manager.py     # Template rendering
│   ├── tools/
│   │   ├── github_tool.py        # GitHub CLI tool (gh)
│   │   ├── opencode_tool.py      # OpenCode CLI tool
│   │   └── ollama_tool.py        # Ollama generation tool
│   └── orchestrator.py           # LangChain agent orchestration
├── output/                       # Long output storage
├── agent.py                      # Main entry point
├── requirements.txt              # Dependencies
└── .env                          # Configuration
```

## Setup

### 1. Prerequisites

- Python 3.9+
- Slack Bot with proper permissions
- OpenCode CLI (`opencode`)
- GitHub CLI (`gh`)
- Ollama running locally

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
OLLAMA_URL=http://localhost:11434
MODEL=qwen2.5-coder:14b
BACKEND=opencode
MAX_OUTPUT_LENGTH=200
OUTPUT_DIR=./output
TOOL_TIMEOUT=120
```

### Configuration Options

- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_SIGNING_SECRET`: Slack signing secret
- `SLACK_APP_TOKEN`: Slack app-level token
- `OLLAMA_URL`: Ollama server URL (default: http://localhost:11434)
- `MODEL`: Ollama model to use (default: qwen2.5-coder:14b)
- `BACKEND`: Backend to use - opencode or ollama (default: opencode)
- `MAX_OUTPUT_LENGTH`: Character limit before file upload (default: 200)
- `OUTPUT_DIR`: Directory for long outputs (default: ./output)
- `TOOL_TIMEOUT`: Tool execution timeout in seconds (default: 120)

### 4. Run the Application

```bash
source venv/bin/activate
python agent.py
```

## Usage

### Mode 1: Slash Commands

Use explicit slash commands for direct tool execution:

#### Git Commands
```
@bot /git repo list
@bot /git pr create --title "Fix bug" --body "Description"
@bot /git issue list --state open
```

#### OpenCode Commands
```
@bot /opencode create a hello world program in Python
@bot /opencode review this code and suggest improvements
@bot /opencode fix the bug in the authentication module
```

#### Multiple Commands
```
@bot /git status /opencode analyze the changes
@bot /git clone https://github.com/user/repo /opencode review the codebase
```

### Mode 2: Natural Language

Let the agent infer which tool to use:

```
@bot list my GitHub repositories
@bot create a Python function to calculate fibonacci numbers
@bot explain how async/await works in Python
@bot write documentation for this API endpoint
```

The agent will automatically:
1. Analyze your request
2. Select the appropriate tool(s)
3. Execute sequentially
4. Report results

## How It Works

### Slash Command Flow

1. User sends message with `/git` or `/opencode`
2. Slack client parses slash commands
3. Orchestrator executes commands directly
4. Status updates sent via Slack message updates
5. Long outputs uploaded as files

### Natural Language Flow

1. User sends natural language message
2. Orchestrator passes to LangChain agent
3. Ollama LLM analyzes request
4. Agent selects appropriate tool(s)
5. Tools execute sequentially
6. Results streamed back to Slack

### Tool Execution

All tools:
- Execute sequentially
- Stop on first failure (no fallbacks)
- Timeout protection
- Clear error reporting

## Available Tools

### 1. GitHub Tool
- Repository operations
- PR management
- Issue tracking
- Any `gh` CLI command

### 2. OpenCode Tool
- Code generation
- Code analysis
- Refactoring
- Debugging
- Test writing

### 3. Ollama Tool
- Text generation
- Explanations
- Documentation
- General questions
- Brainstorming

## Example Interactions

### Example 1: Slash Commands
```
User: @bot /git repo list /opencode suggest improvements

Bot: Analyzing your request...
Bot: Executing command 1/2: /git repo list...
Bot: Command 1 completed successfully. Moving to next command...
Bot: Executing command 2/2: /opencode suggest improvements...
Bot: ✅ All commands completed successfully!
     
     ✅ Command 1: /git
     repo1/repo2/repo3...
     
     ✅ Command 2: /opencode
     Here are some improvements...
```

### Example 2: Natural Language
```
User: @bot create a Python script that monitors CPU usage

Bot: Analyzing request and determining which tools to use...
Bot: ✅ Task completed!
     
     I'll use the opencode tool to create a CPU monitoring script...
     [Generated code and explanation]
```

### Example 3: Error Handling
```
User: @bot /git invalid-command

Bot: Executing command 1/1: /git invalid-command...
Bot: ⚠️ Command execution stopped due to failure:
     
     ❌ Command 1: /git
     Error: unknown command "invalid-command"
```

## Development

### Code Style
- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters
- Use `black` for formatting
- Use `isort` for imports

### Linting
```bash
pip install ruff
ruff check .
ruff check --fix .
```

### Project Structure

- **integrations/**: External service clients (Slack, Ollama)
- **models/**: Data models and configuration
- **prompts/**: Jinja2 templates for LLM prompts
- **tools/**: LangChain tools for agent use
- **orchestrator.py**: Main orchestration logic

### Adding New Tools

1. Create tool in `src/tools/`:
```python
from langchain.tools import tool

@tool
def my_new_tool(arg: str) -> str:
    """Tool description."""
    # Implementation
```

2. Import in `src/orchestrator.py`:
```python
from src.tools.my_new_tool import my_new_tool

self.tools = [github, opencode, ollama_generate, my_new_tool]
```

3. Update system prompt in `src/prompts/templates/system_prompt.j2`

## Error Handling

- **Tool Failure**: Stops execution immediately, reports error
- **Timeout**: Tools timeout after configured duration
- **No Fallbacks**: No silent failures or alternative approaches
- **Clear Reporting**: All errors reported to user

## Monitoring

- LangChain verbose mode enabled
- Tool execution logged
- Error traces preserved

## Security

- Never commit `.env` file
- Tokens stored securely in environment
- No secrets in logs or output

## Troubleshooting

### Bot not responding
- Check Slack tokens are valid
- Verify bot has necessary permissions
- Check logs for errors

### Tool execution failures
- Verify CLI tools installed (`gh`, `opencode`)
- Check Ollama is running
- Verify tool permissions

### Long response times
- Check Ollama model is loaded
- Consider increasing timeout
- Check system resources

## License

[Your License Here]

## Contributing

[Contribution Guidelines]
