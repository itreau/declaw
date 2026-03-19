import subprocess
from typing import Callable, Optional, List


def stream_command(
    command: List[str],
    on_output: Optional[Callable[[str], None]] = None,
    timeout: int = 300,
) -> int:
    """Execute a command with streaming output.
    
    Args:
        command: List of command arguments
        on_output: Callback function called with each line of output
        timeout: Timeout in seconds
        
    Returns:
        Return code of the command
    """
    process = None
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        
        while process.stdout is not None:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                if on_output:
                    on_output(line.rstrip('\n'))
        
        result = process.poll()
        return result if result is not None else 0
        
    except subprocess.TimeoutExpired:
        if process:
            process.kill()
        if on_output:
            on_output("Command timed out")
        return -1
    except Exception as e:
        if on_output:
            on_output(f"Error executing command: {str(e)}")
        return -1


class OpenCodeTool:
    """OpenCode CLI tool for handling user requests."""
    
    def invoke(
        self,
        prompt: str,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Execute OpenCode CLI with the given prompt.
        
        Args:
            prompt: The user's request or task description
            on_output: Optional callback for streaming output
        
        Returns:
            OpenCode output or error message
        """
        command = ["opencode", "run", prompt]
        
        output_lines: List[str] = []
        
        def capture_output(line: str):
            output_lines.append(line)
            if on_output:
                on_output(line)
        
        returncode = stream_command(
            command,
            on_output=capture_output,
            timeout=300,
        )
        
        output = '\n'.join(output_lines)
        
        if returncode != 0:
            raise RuntimeError(f"OpenCode CLI command failed: {output}")
        
        return output


opencode = OpenCodeTool()