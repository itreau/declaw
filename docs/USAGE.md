# Usage Guide

## Table of Contents

- [Interaction Modes](#interaction-modes)
- [Slash Commands](#slash-commands)
- [Natural Language](#natural-language)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Interaction Modes

PyAgent supports two modes of interaction:

1. **Slash Commands**: Explicit tool invocation with `/git`, `/opencode`, `/ollama`
2. **Natural Language**: Describe what you want in plain English

Both modes can be used interchangeably in the same conversation.

## Slash Commands

Slash commands provide explicit control over which tool to use.

### GitHub Commands (`/github`)

Uses GitHub REST API for repository operations. Requires GITHUB_TOKEN configured in `.env`.

#### Repository Operations

```bash
# List your repositories
@bot /github repo list

# List repositories for a specific user/org
@bot /github repo list --owner microsoft

# View repository details
@bot /github repo view owner/repo

# Fork a repository
@bot /github repo fork owner/repo
```

#### Pull Requests

```bash
# List PRs
@bot /github pr list --owner owner --repo repo

# List closed PRs
@bot /github pr list --owner owner --repo repo --state closed

# Create a PR
@bot /github pr create --owner owner --repo repo --title "Fix bug" --body "Description" --head branch --base main
```

#### Issues

```bash
# List issues
@bot /github issue list --owner owner --repo repo

# List closed issues
@bot /github issue list --owner owner --repo repo --state closed

# Create an issue
@bot /github issue create --owner owner --repo repo --title "Bug report" --body "Description"
```

**Note**: For repository/PR/issue operations, you must specify `--owner` and `--repo` parameters.

See [GITHUB_REST_API.md](./GITHUB_REST_API.md) for complete command reference.

### OpenCode Commands (`/opencode`)

Uses OpenCode CLI for intelligent code operations.

#### Code Generation

```bash
# Create a function
@bot /opencode create a Python function to calculate fibonacci numbers

# Generate a class
@bot /opencode create a User class with name, email, and age attributes

# Generate a script
@bot /opencode create a Python script that monitors CPU usage and logs to a file
```

#### Code Review

```bash
# Review changes
@bot /opencode review the current git changes

# Review specific file
@bot /opencode review src/auth.py and suggest improvements

# Review for security
@bot /opencode check this code for security vulnerabilities
```

#### Refactoring

```bash
# Refactor code
@bot /opencode refactor this function to be more readable

# Optimize performance
@bot /opencode optimize this code for better performance

# Add type hints
@bot /opencode add type hints to this function
```

#### Documentation

```bash
# Generate docstrings
@bot /opencode add docstrings to this class

# Create README
@bot /opencode generate a README for this module

# Explain code
@bot /opencode explain how this async function works
```

#### Testing

```bash
# Write tests
@bot /opencode write unit tests for the calculator module

# Generate test cases
@bot /opencode create test cases for edge cases in this function
```

### Ollama Commands (`/ollama`)

Direct text generation using Ollama LLM.

#### Explanations

```bash
@bot /ollama explain how async/await works in Python
@bot /ollama what is the difference between a list and a tuple
```

#### Brainstorming

```bash
@bot /ollama suggest 5 ways to improve API performance
@bot /ollama what are best practices for error handling
```

#### Documentation

```bash
@bot /ollama write a tutorial on using decorators
@bot /ollama create API documentation for these endpoints
```

## Natural Language

Let the agent infer which tool(s) to use based on context.

### Examples

```bash
# GitHub operations
@bot list my repositories
@bot show me open pull requests
@bot create an issue about the login bug

# Code generation
@bot create a Python function to validate email addresses
@bot write a script to backup files to S3
@bot generate a REST API endpoint for user registration

# Code review
@bot review my recent changes
@bot check if this code follows best practices
@bot find potential bugs in this function

# Explanations
@bot explain how this regex pattern works
@bot what does this SQL query do
@bot describe the architecture of this module

# Documentation
@bot write documentation for this API
@bot create a user guide for this feature
```

## Multiple Commands

Chain multiple commands in a single message (executed sequentially):

```bash
# Check status then review
@bot /git status /opencode review the changes

# List repos then analyze one
@bot /git repo list /opencode analyze the most active repository

# Generate code then create PR
@bot /opencode create a hello world function /git add . /git commit -m "Add hello world" /git push
```

**Note**: Execution stops on first failure. If command 2 fails, commands 3+ won't execute.

## Examples

### Example 1: Bug Fix Workflow

```
User: @bot /git status /opencode review the changes and suggest fixes

Bot: Analyzing your request...
     Executing command 1/2: /git status...
     ✅ Command 1 completed successfully.
     
     On branch feature/auth, 3 files modified:
     - src/auth.py
     - tests/test_auth.py
     - requirements.txt
     
     Executing command 2/2: /opencode review...
     ✅ All commands completed successfully!
     
     === Command 1: /git ===
     On branch feature/auth
     Changes not staged for commit:
       modified:   src/auth.py
       modified:   tests/test_auth.py
       modified:   requirements.txt
     
     === Command 2: /opencode ===
     Review of changes:
     
     src/auth.py:
     - Line 42: Potential SQL injection vulnerability. Use parameterized queries.
     - Line 58: Missing error handling for network timeouts.
     
     tests/test_auth.py:
     - Good coverage! Consider adding edge case for empty input.
     
     requirements.txt:
     - Consider pinning versions for reproducibility.
     
     Suggested fixes:
     1. Replace string concatenation with parameterized query
     2. Add try/except block for network operations
     3. Pin package versions: package==1.2.3
```

### Example 2: Code Generation

```
User: @bot create a Python function to download a file from a URL with progress tracking

Bot: Analyzing request and determining which tools to use...
     ✅ Task completed!
     
     I'll use the opencode tool to create a file download function with progress tracking.
     
     ```python
     import requests
     from tqdm import tqdm
     
     def download_file_with_progress(url: str, destination: str) -> None:
         """
         Download a file from URL with progress tracking.
         
         Args:
             url: URL of the file to download
             destination: Local path to save the file
         """
         response = requests.get(url, stream=True)
         response.raise_for_status()
         
         total_size = int(response.headers.get('content-length', 0))
         
         with open(destination, 'wb') as f:
             with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                 for chunk in response.iter_content(chunk_size=8192):
                     f.write(chunk)
                     pbar.update(len(chunk))
         
         print(f"Downloaded: {destination}")
     ```
     
     This function:
     - Uses requests with streaming for large files
     - Shows progress bar using tqdm
     - Handles errors with raise_for_status()
     - Writes in chunks to avoid memory issues
```

### Example 3: Natural Language Query

```
User: @bot what are the best practices for Python error handling?

Bot: Analyzing request...
     ✅ Task completed!
     
     Python Error Handling Best Practices:
     
     1. **Be Specific**: Catch specific exceptions, not bare `except:`
        ```python
        try:
            result = int(user_input)
        except ValueError:
            print("Invalid number")
        ```
     
     2. **Use Custom Exceptions**: Create domain-specific exceptions
        ```python
        class ValidationError(Exception):
            pass
        ```
     
     3. **Always Clean Up**: Use `finally` or context managers
        ```python
        with open('file.txt') as f:
            data = f.read()
        ```
     
     4. **Preserve Tracebacks**: Use `raise ... from e`
        ```python
        try:
            process(data)
        except ValueError as e:
            raise ProcessingError("Invalid data") from e
        ```
     
     5. **Log Exceptions**: Don't just print
        ```python
        logger.exception("Failed to process request")
        ```
```

### Example 4: Error Handling

```
User: @bot /git push-to-nonexistent-remote

Bot: Executing command 1/1: /git push-to-nonexistent-remote...
     ⚠️ Command execution stopped due to failure:
     
     ❌ Command 1: /git
     Error: remote 'nonexistent-remote' not found
     
     Available remotes:
     - origin (https://github.com/user/repo.git)
     
     Tip: Use '/git remote -v' to list all remotes
```

## Best Practices

### When to Use Slash Commands

- **Precision needed**: You know exactly which tool to use
- **Complex operations**: Multi-step workflows with specific tools
- **Debugging**: Clearer execution path for troubleshooting
- **Learning**: Easier to understand what's happening

### When to Use Natural Language

- **Exploratory**: Not sure which tool is best
- **Simple requests**: Quick, straightforward tasks
- **Combining operations**: Agent can choose multiple tools
- **Convenience**: Natural expression

### Tips for Better Results

1. **Be specific**: "Create a REST API endpoint" vs "Create an endpoint"
2. **Provide context**: "Review this authentication code" vs "Review this"
3. **Use threading**: Keep related messages in the same thread
4. **Check outputs**: Review generated code before using
5. **Iterate**: Refine requests based on results

### Performance Tips

1. **Use slash commands**: Faster than natural language processing
2. **Be concise**: Shorter prompts process faster
3. **Batch operations**: Combine multiple commands in one message
4. **Check model**: Larger models are slower but more capable

## Troubleshooting

### Bot Not Responding

**Symptoms**: No response after mentioning the bot

**Solutions**:
1. Check bot is running: `ps aux | grep agent.py`
2. Verify Slack tokens in `.env`
3. Check bot has necessary permissions in Slack
4. Review logs for errors

### Tool Execution Failures

**Symptoms**: "Command failed" or timeout errors

**Solutions**:
1. **GitHub Integration**: Ensure GITHUB_TOKEN is set in `.env` and has required scopes
2. **OpenCode**: Ensure `opencode` is in PATH: `which opencode`
3. **Ollama**: Check Ollama is running: `curl http://localhost:11434/api/tags`
4. **Timeouts**: Increase `TOOL_TIMEOUT` in `.env`

### GitHub Authentication Issues

**Symptoms**: "Permission denied" or "Invalid token" errors

**Solutions**:
1. Verify GITHUB_TOKEN is correctly set in `.env`
2. Check token hasn't expired at GitHub Settings → Tokens
3. Ensure token has required scopes (`public_repo`, `repo:write`, or `repo`)
4. For organization repos, enable SSO for the token
5. See [GITHUB_REST_API.md](./GITHUB_REST_API.md) for operation-specific scopes

### Long Response Times

**Symptoms**: Bot takes > 30 seconds to respond

**Solutions**:
1. **Check Ollama**: Model might be loading, first request is slow
2. **Hardware**: Ensure sufficient RAM/CPU for model
3. **Model size**: Consider smaller model (e.g., `qwen2.5-coder:7b`)
4. **Network**: If using remote Ollama, check connection speed

### Unexpected Tool Selection

**Symptoms**: Agent chooses wrong tool for natural language query

**Solutions**:
1. **Be more specific**: Add context about which tool to use
2. **Use slash command**: Switch to explicit slash commands
3. **Check system prompt**: Review `src/prompts/templates/system_prompt.j2`
4. **Model capability**: Larger models better at intent inference

### File Upload Issues

**Symptoms**: Long outputs not uploaded as files

**Solutions**:
1. Check `OUTPUT_DIR` exists and is writable
2. Verify Slack app has `files:write` permission
3. Check `MAX_OUTPUT_LENGTH` setting (default: 200)
4. Review logs for upload errors

### Connection Errors

**Symptoms**: "Connection refused" or "Timeout" errors

**Solutions**:
1. **Ollama**: Verify Ollama URL in `.env` matches actual server
2. **Slack**: Check internet connection and Slack status
3. **Docker**: If using Docker, ensure proper networking (see [DOCKER.md](DOCKER.md))
4. **Firewall**: Check firewall rules allow necessary connections

## Advanced Usage

### Custom Tool Chains

Create custom workflows by chaining commands:

```bash
# Full PR workflow
@bot /git checkout -b feature/new-feature \
     /opencode implement user authentication \
     /git add . \
     /git commit -m "Add user authentication" \
     /git push -u origin feature/new-feature \
     /git pr create --title "Add authentication" --body "Implements user auth"
```

### Using with CI/CD

Automate bot interactions in CI/CD pipelines:

```yaml
# Example GitLab CI
deploy:
  script:
    - |
      curl -X POST $SLACK_WEBHOOK_URL \
      -d '{"text": "@bot /git tag v1.0.0 /git push --tags"}'
```

### Integration with Other Tools

The bot can work with any CLI tool:

1. Create a new tool in `src/tools/`
2. Wrap the CLI command
3. Register in `orchestrator.py`
4. Update system prompt

See [DEVELOPMENT.md](DEVELOPMENT.md) for details.
