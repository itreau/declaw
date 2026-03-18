import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from langchain.tools import tool

from src.models.config import Config


def execute_git_command(
    command: list,
    cwd: Optional[str] = None,
    timeout: int = 120,
) -> Tuple[str, bool]:
    """Execute a git command.
    
    Args:
        command: Git command arguments (e.g., ['clone', 'url'])
        cwd: Working directory (defaults to workspace directory)
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (output, success)
    """
    config = Config.from_env()
    
    workspace_dir = os.getenv("WORKSPACE_DIR", str(config.output_dir / "workspace"))
    workspace_path = Path(workspace_dir)
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    working_dir = Path(cwd) if cwd else workspace_path
    
    if not working_dir.exists():
        return f"Error: Directory {working_dir} does not exist", False
    
    full_command = ["git"] + command
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(working_dir),
        )
        output = result.stdout + result.stderr
        return output.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "Command timed out", False
    except Exception as e:
        return f"Error executing git command: {str(e)}", False


@tool
def git(command: str) -> str:
    """Execute git commands for repository operations.
    
    Use this tool for:
    - Cloning repositories: git clone <url> [directory]
    - Checking status: git status
    - Viewing logs: git log [--oneline] [-n count]
    - Viewing branches: git branch [-a]
    - Checking out branches: git checkout <branch>
    - Pulling changes: git pull
    
    Note: Repositories are cloned to the configured workspace directory.
    By default: ./output/workspace/ (local) or /workspace (in container)
    
    Args:
        command: Git command to execute (e.g., "clone https://github.com/user/repo.git", "status")
        
    Returns:
        Command output or error message
        
    Examples:
        git("clone https://github.com/owner/repo.git")
        git("status")
        git("log --oneline -10")
        git("branch -a")
    """
    args = command.split()
    
    if not args:
        return "Error: Empty command. Provide a git command (e.g., 'clone <url>', 'status', 'log')"
    
    if args[0] == "clone":
        if len(args) < 2:
            return "Error: clone requires a repository URL. Usage: clone <url> [directory]"
        
        repo_url = args[1]
        target_dir = args[2] if len(args) > 2 else None
        
        config = Config.from_env()
        workspace_dir = os.getenv("WORKSPACE_DIR", str(config.output_dir / "workspace"))
        workspace_path = Path(workspace_dir)
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        clone_args = ["clone", repo_url]
        if target_dir:
            clone_args.append(target_dir)
        
        output, success = execute_git_command(clone_args)
        
        if success:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            target_path = target_dir if target_dir else repo_name
            return f"✓ Repository cloned successfully to {workspace_path / target_path}\n\n{output}"
        else:
            return f"✗ Failed to clone repository:\n{output}"
    
    elif args[0] in ["status", "log", "branch", "checkout", "pull", "push", "fetch"]:
        output, success = execute_git_command(args)
        
        if success:
            return output if output else "Command completed successfully"
        else:
            return f"✗ Git command failed:\n{output}"
    
    else:
        output, success = execute_git_command(args)
        
        if success:
            return output if output else "Command completed successfully"
        else:
            return f"✗ Git command failed:\n{output}"