from langchain.tools import tool

from src.tools.github_tool import execute_command


@tool
def opencode(prompt: str) -> str:
    """Execute OpenCode CLI for code-related tasks.
    
    Use this tool for:
    - Code generation
    - Code analysis and review
    - Refactoring
    - Debugging
    - Writing tests
    - Any other code-related operations
    
    Args:
        prompt: The task description or prompt for OpenCode
    
    Returns:
        OpenCode output or error message
        
    Examples:
        opencode("create a hello world program in Python")
        opencode("review this code and suggest improvements")
        opencode("fix the bug in the authentication module")
        opencode("write unit tests for the calculator class")
    """
    command = ["opencode", prompt]
    output, success = execute_command(command)
    
    if not success:
        raise RuntimeError(f"OpenCode CLI command failed: {output}")
    
    return output
