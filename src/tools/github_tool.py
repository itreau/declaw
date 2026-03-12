import subprocess
from typing import Tuple

from langchain.tools import tool


def execute_command(
    command: list,
    timeout: int = 120,
) -> Tuple[str, bool]:
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
def github(command: str) -> str:
    """Execute GitHub CLI (gh) commands for repository operations.
    
    Use this tool for:
    - Cloning repositories
    - Creating pull requests
    - Managing issues
    - Viewing repository information
    - Any other GitHub CLI operations
    
    Args:
        command: The gh command to execute (e.g., "repo list", "pr create", "issue list")
    
    Returns:
        Command output or error message
        
    Examples:
        github("repo list")
        github("pr create --title 'Fix bug' --body 'Description'")
        github("issue list --state open")
    """
    args = command.split()
    full_command = ["gh"] + args
    output, success = execute_command(full_command)
    
    if not success:
        raise RuntimeError(f"GitHub CLI command failed: {output}")
    
    return output
