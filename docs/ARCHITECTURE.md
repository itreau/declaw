# Architecture

## Overview

PyAgent is a Slack bot that integrates with local LLM services (Ollama) and coding tools (OpenCode CLI) using LangChain for intelligent tool orchestration. The system supports both natural language intent inference and explicit slash commands.

## System Architecture

```
┌─────────────┐
│   Slack     │
│   User      │
└──────┬──────┘
       │ @mention
       ▼
┌─────────────────────────────────────────┐
│         Slack Bolt Framework            │
│  (src/integrations/slack_client.py)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Agent Orchestrator                 │
│      (src/orchestrator.py)              │
│                                         │
│  ┌──────────────┐  ┌────────────────┐  │
│  │ Slash Command│  │ Natural Lang.  │  │
│  │   Handler    │  │    Handler     │  │
│  └──────┬───────┘  └────────┬───────┘  │
│         │                   │          │
│         └───────────┬───────┘          │
│                     ▼                  │
│         ┌─────────────────────┐        │
│         │   LangChain Agent   │        │
│         └──────────┬──────────┘        │
└────────────────────┼───────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ GitHub  │  │OpenCode │  │ Ollama  │
   │   CLI   │  │   CLI   │  │   API   │
   └─────────┘  └─────────┘  └─────────┘
```

## Components

### 1. Slack Integration (`src/integrations/slack_client.py`)

**Responsibilities**:
- Listen for bot mentions via Slack Socket Mode
- Parse incoming messages
- Manage message threading
- Send status updates and responses
- Handle file uploads for long outputs

**Key Features**:
- Real-time message processing
- Thread-based responses
- Dynamic status updates using `chat.update`
- Automatic file upload for outputs > 200 characters

### 2. Orchestrator (`src/orchestrator.py`)

**Responsibilities**:
- Route messages to appropriate handler (slash command vs natural language)
- Execute slash commands sequentially
- Coordinate LangChain agent for natural language queries
- Manage tool execution flow
- Handle errors and timeouts

**Execution Flow**:

#### Slash Command Mode
```
1. Parse command (e.g., /git status /opencode review)
2. Split into individual commands
3. Execute each command sequentially
4. Stop on first failure
5. Return aggregated results
```

#### Natural Language Mode
```
1. Pass message to LangChain agent
2. Agent (Ollama) analyzes intent
3. Select appropriate tool(s)
4. Execute tool(s) sequentially
5. Return results
```

### 3. LangChain Integration (`src/integrations/ollama_client.py`)

**Responsibilities**:
- Configure Ollama LLM connection
- Manage LangChain agent creation
- Handle tool binding
- Process agent responses

**Configuration**:
- Model: Configurable (default: `qwen2.5-coder:14b`)
- Backend: Ollama (local inference)
- URL: Configurable (default: `http://localhost:11434`)

### 4. Tools (`src/tools/`)

Each tool is a LangChain `@tool` decorated function that provides specific capabilities:

#### GitHub Tool (`github_tool.py`)
- Wraps `gh` CLI commands
- Repository operations
- PR management
- Issue tracking

#### OpenCode Tool (`opencode_tool.py`)
- Wraps `opencode` CLI
- Code generation
- Code review
- Refactoring
- Documentation

#### Ollama Tool (`ollama_tool.py`)
- Direct LLM text generation
- Explanations
- Brainstorming
- General Q&A

### 5. Prompt Management (`src/prompts/`)

**Structure**:
- `prompt_manager.py`: Jinja2 template rendering
- `templates/system_prompt.j2`: System prompt for LangChain agent

**System Prompt Components**:
- Tool descriptions and usage guidelines
- Response formatting rules
- Error handling instructions
- Sequential execution constraints

### 6. Configuration (`src/models/config.py`)

**Environment Variables**:
- `SLACK_BOT_TOKEN`: Bot authentication
- `SLACK_SIGNING_SECRET`: Request verification
- `SLACK_APP_TOKEN`: Socket Mode connection
- `OLLAMA_URL`: Ollama server endpoint
- `MODEL`: LLM model name
- `BACKEND`: Backend selection (opencode/ollama)
- `MAX_OUTPUT_LENGTH`: Threshold for file upload
- `OUTPUT_DIR`: Directory for long outputs
- `TOOL_TIMEOUT`: Execution timeout in seconds

## Data Flow

### Example: Natural Language Request

```
User: "@bot create a Python function to calculate fibonacci"

1. Slack Client receives message
2. Orchestrator detects no slash commands
3. Passes to LangChain agent with system prompt
4. Ollama analyzes: "This is a code generation task"
5. Agent selects: opencode_tool
6. Tool executes: opencode "create a Python function to calculate fibonacci"
7. Result: Generated code
8. Orchestrator returns to Slack Client
9. Slack Client posts in thread
```

### Example: Slash Command Request

```
User: "@bot /git status /opencode review the changes"

1. Slack Client receives message
2. Orchestrator parses 2 commands: ["/git status", "/opencode review the changes"]
3. Execute command 1: github_tool("status")
   - Result: "On branch main, working tree clean"
4. Execute command 2: opencode_tool("review the changes")
   - Result: "No changes to review"
5. Aggregate results
6. Return to Slack Client
7. Slack Client posts in thread
```

## Design Decisions

### Why LangChain?
- **Native Ollama integration**: Built-in support via `langchain-ollama`
- **Tool abstraction**: Clean `@tool` decorator pattern
- **Agent loop**: Automatic tool calling and reasoning
- **Extensibility**: Easy to add new tools
- **Prompt management**: Structured system prompts

### Why Dual Mode?
- **Explicit control**: Slash commands for precise operations
- **Flexibility**: Natural language for exploratory tasks
- **User choice**: Different users prefer different interaction styles
- **Learning curve**: Slash commands easier for beginners

### Why Sequential Execution?
- **Predictability**: Clear execution order
- **Debugging**: Easy to identify failure points
- **Simplicity**: No race conditions or dependency issues
- **Safety**: Prevents unintended parallel operations

### Why No Fallbacks?
- **Explicitness**: User knows exactly what failed
- **Debugging**: Clear error messages
- **Trust**: No unexpected behavior
- **Simplicity**: Reduces complexity

## Error Handling

### Tool Execution Errors
- Tools raise `RuntimeError` with descriptive messages
- Orchestrator catches and formats for Slack
- Execution stops immediately
- User receives clear error message

### Timeout Protection
- Each tool has configurable timeout
- Prevents hanging on long operations
- Clear timeout message to user

### Connection Errors
- Ollama connection failures reported clearly
- Slack API errors logged and reported
- Graceful degradation when possible

## Security Considerations

### Secrets Management
- All tokens in `.env` file (never committed)
- Environment variables loaded at runtime
- No secrets in logs or error messages

### Tool Permissions
- Tools run with user's permissions
- GitHub CLI uses user's authentication
- OpenCode runs in user's context

### Network Security
- Slack uses HTTPS only
- Ollama connection is local (configurable)
- No external API calls (fully local)

## Performance Characteristics

### Latency
- Slash commands: ~1-5 seconds (CLI execution)
- Natural language: ~5-30 seconds (LLM inference + tool execution)
- Depends on Ollama model and hardware

### Resource Usage
- Memory: ~200-500MB (Python + dependencies)
- CPU: Minimal when idle, spikes during LLM inference
- Disk: ~150MB (Docker image), outputs stored in `./output/`

### Scalability
- Single-threaded message processing
- One conversation at a time
- Suitable for small teams (< 50 users)

## Future Improvements

### Potential Enhancements
1. **Parallel tool execution**: For independent operations
2. **Conversation memory**: Context across messages
3. **Streaming responses**: Real-time output streaming
4. **Tool marketplace**: Easy tool installation
5. **Multi-model support**: Switch between different LLMs
6. **Caching**: Cache frequent operations
7. **Rate limiting**: Prevent abuse

### Known Limitations
- No conversation history (each message is independent)
- Single-threaded execution
- No parallel tool support
- Limited to installed CLI tools
- No authentication/authorization beyond Slack
