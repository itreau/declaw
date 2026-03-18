from langchain.tools import tool

from src.integrations.github_client import GitHubClient
from src.models.config import Config


@tool
def github(command: str) -> str:
    """Execute GitHub REST API commands for repository operations.
    
    Use this tool for:
    - Listing repositories
    - Viewing repository details
    - Managing pull requests
    - Managing issues
    - Forking repositories
    
    Args:
        command: Natural language command (e.g., "repo list", "pr create --owner OWNER --repo REPO")
    
    Returns:
        Command output or error message
        
    Examples:
        github("repo list")
        github("repo list --owner microsoft")
        github("repo view owner/repo")
        github("pr list --owner owner --repo repo")
        github("pr create --owner owner --repo repo --title 'Fix bug' --body 'Description' --head branch --base main")
        github("issue list --owner owner --repo repo")
        github("issue create --owner owner --repo repo --title 'Bug report' --body 'Details'")
        github("repo fork owner/repo")
    """
    config = Config.from_env()
    
    if not config.github_token:
        return ("Error: GITHUB_TOKEN not configured. "
                "Add GITHUB_TOKEN to your .env file.\n"
                "Get a token at: https://github.com/settings/tokens\n"
                "Required scopes: 'repo:read' for read operations, 'repo:write' for PR/issue creation.")
    
    client = GitHubClient(token=config.github_token)
    
    try:
        result = client.parse_and_execute(command)
        return result
    except Exception as e:
        return f"Error executing GitHub command: {str(e)}"