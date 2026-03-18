# PyAgent - Free, Secure, Local Coding Agent for Slack

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](docs/DOCKER.md)

A Python Slack bot that integrates with Ollama (local LLM) and OpenCode CLI using LangChain orchestration. Supports both natural language intent inference and explicit slash commands.

## Why PyAgent?

- **✓ Free** - Uses local Ollama, no API costs or rate limits
- **✓ Secure** - Runs entirely locally, your code never leaves your machine
- **✓ Small** - Minimal dependencies, ~150MB Docker image
- **✓ Easy** - Natural language or slash commands, your choice

## Quick Start

### Option 1: Local Installation

```bash
# 1. Clone and install
git clone https://github.com/your-username/pyagent.git
cd pyagent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your Slack tokens

# 3. Run
python agent.py
```

### Option 2: Docker (Recommended)

```bash
# 1. Configure
cp .env.example .env
# Edit .env with your Slack tokens

# 2. Run
docker-compose up -d
```

## Requirements

| Requirement  | Version  | Purpose             |
| ------------ | -------- | ------------------- |
| Python       | 3.9+     | Runtime             |
| Slack Bot    | -        | Slack integration   |
| Ollama       | -        | Local LLM inference |
| OpenCode CLI | -        | Code generation     |

## Features

- **Dual Mode**: Slash commands (`/git`, `/opencode`) or natural language
- **Intelligent Tool Selection**: LLM automatically chooses appropriate tools
- **Sequential Execution**: Tools execute in order, clear failure reporting
- **Slack Integration**: Threading, status updates, file uploads
- **Local & Private**: Everything runs on your machine

## Usage Examples

### Natural Language

```
@bot create a Python function to calculate fibonacci numbers
@bot review my recent git changes
@bot explain how async/await works in Python
```

### Slash Commands

```
@bot /git status
@bot /opencode create a REST API endpoint
@bot /git pr list /opencode review the changes
```

## Configuration

Minimal `.env` configuration:

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
OLLAMA_URL=http://localhost:11434
MODEL=qwen2.5-coder:14b

# Optional: Restrict GitHub access with PAT token
# GITHUB_TOKEN=ghp_your_token_here
```

See [`.env.example`](.env.example) for all options.

### GitHub Integration

The bot uses the GitHub REST API for repository operations. Configure with a Personal Access Token:

1. Create a PAT token at [GitHub Settings](https://github.com/settings/tokens)
2. Select required scopes: `public_repo` (read), `repo:write` (PR/issue creation), or `repo` (full access)
3. Add to `.env`: `GITHUB_TOKEN=ghp_your_token_here`

See [GitHub REST API Guide](docs/GITHUB_REST_API.md) for supported operations and [GitHub Token Guide](docs/GITHUB_TOKEN.md) for security best practices.

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Usage Guide](docs/USAGE.md)** - Detailed examples and best practices
- **[Docker Setup](docs/DOCKER.md)** - Docker deployment guide
- **[Development](docs/DEVELOPMENT.md)** - Contributing and adding tools

## Architecture

```
User → Slack → Orchestrator → LangChain Agent → Tools (GitHub, OpenCode, Ollama)
                                                    ↓
                                                Local Services
```

The orchestrator routes messages to either slash command handlers or the LangChain agent, which uses Ollama to intelligently select and execute tools.

## License

MIT License - see [LICENSE](LICENSE.txt) for details.

## Contributing

Contributions welcome! See [Development Guide](docs/DEVELOPMENT.md) for:

- Code style guidelines
- Adding new tools
- Testing procedures
- Pull request process

## Support

- **Issues**: [GitHub Issues](https://github.com/your-username/pyagent/issues)
- **Docs**: See `docs/` directory
- **Troubleshooting**: See [USAGE.md](docs/USAGE.md#troubleshooting)
