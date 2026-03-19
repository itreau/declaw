import subprocess
from typing import Tuple


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


class OpenCodeTool:
    """OpenCode CLI tool for handling user requests."""
    
    def invoke(self, prompt: str) -> str:
        """Execute OpenCode CLI with the given prompt.
        
        Args:
            prompt: The user's request or task description
        
        Returns:
            OpenCode output or error message
        """
        command = ["opencode", "run", prompt]
        output, success = execute_command(command)
        
        if not success:
            raise RuntimeError(f"OpenCode CLI command failed: {output}")
        
        return output


opencode = OpenCodeTool()