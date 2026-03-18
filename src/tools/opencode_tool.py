import subprocess
from typing import Tuple

from langchain.tools import tool


def execute_command(
    command: list,
    timeout: int = 120,
) -> Tuple[str, bool]:
    """Execute a command.
    
    Args:
        command: List of command arguments
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (output, success)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return output.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "Command timed out", False
    except Exception as e:
        return f"Error executing command: {str(e)}", False


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
