import re
from typing import Any, Dict, List, Optional, Tuple

import requests


class GitHubClient:
    BASE_URL = "https://api.github.com"
    
    REQUIRED_SCOPES = {
        "repo_list": [],
        "repo_view": [],
        "pr_list": [],
        "pr_create": ["repo:write"],
        "issue_list": [],
        "issue_create": ["repo:write"],
        "repo_fork": ["repo:write"],
    }
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self._token_validated = False
        self._token_scopes: List[str] = []
        
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
    ) -> Tuple[Any, bool]:
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=json_data,
                timeout=30,
            )
            
            self._extract_scopes_from_response(response)
            
            if response.status_code == 401:
                return "Invalid or expired GitHub token. Please check your GITHUB_TOKEN environment variable.", False
            elif response.status_code == 403:
                scopes = self._token_scopes or []
                return f"Permission denied. Your token has scopes: {scopes}. Additional scopes may be required for this operation.", False
            elif response.status_code == 404:
                return f"Resource not found: {endpoint}", False
            elif response.status_code == 422:
                errors = response.json().get("errors", [])
                error_msgs = [e.get("message", str(e)) for e in errors]
                return f"Validation failed: {', '.join(error_msgs)}", False
            elif response.status_code == 429:
                reset_time = response.headers.get("X-RateLimit-Reset", "unknown")
                return f"Rate limit exceeded. Resets at: {reset_time}", False
            elif response.status_code >= 400:
                return f"GitHub API error ({response.status_code}): {response.text}", False
            
            return response.json(), True
            
        except requests.Timeout:
            return "Request timed out after 30 seconds", False
        except requests.ConnectionError:
            return "Failed to connect to GitHub API. Check your network connection.", False
        except Exception as e:
            return f"Unexpected error: {str(e)}", False
    
    def _extract_scopes_from_response(self, response: requests.Response) -> None:
        if "X-OAuth-Scopes" in response.headers:
            scopes_header = response.headers.get("X-OAuth-Scopes", "")
            self._token_scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
            self._token_validated = True
    
    def validate_token(self) -> Tuple[bool, str]:
        if not self.token:
            return False, "No GitHub token configured. Set GITHUB_TOKEN environment variable."
        
        result, success = self._make_request("GET", "/user")
        
        if success:
            username = result.get("login", "unknown")
            return True, f"Token valid for user: {username} (Scopes: {self._token_scopes})"
        else:
            return False, str(result)
    
    def check_scopes(self, operation: str) -> Tuple[bool, str]:
        if not self._token_validated:
            valid, msg = self.validate_token()
            if not valid:
                return False, msg
        
        required = self.REQUIRED_SCOPES.get(operation, [])
        if not required:
            return True, "No special scopes required"
        
        missing = [s for s in required if s not in self._token_scopes]
        if missing:
            return False, f"Token lacks required scopes: {missing}. Visit https://github.com/settings/tokens to update."
        
        return True, "Sufficient scopes available"
    
    def list_repos(self, owner: Optional[str] = None) -> Tuple[str, bool]:
        has_scopes, scope_msg = self.check_scopes("repo_list")
        if not has_scopes:
            return scope_msg, False
        
        if owner:
            endpoint = f"/users/{owner}/repos"
        else:
            endpoint = "/user/repos"
        
        result, success = self._make_request("GET", endpoint, params={"per_page": 100})
        
        if not success:
            return str(result), False
        
        if not result:
            return "No repositories found", True
        
        lines = [f"Found {len(result)} repositories:\n"]
        for repo in result[:20]:
            name = repo.get("full_name", "unknown")
            visibility = "private" if repo.get("private") else "public"
            stars = repo.get("stargazers_count", 0)
            lines.append(f"  • {name} ({visibility}, ⭐ {stars})")
        
        if len(result) > 20:
            lines.append(f"  ... and {len(result) - 20} more")
        
        return "\n".join(lines), True
    
    def get_repo(self, owner: str, repo: str) -> Tuple[str, bool]:
        has_scopes, scope_msg = self.check_scopes("repo_view")
        if not has_scopes:
            return scope_msg, False
        
        endpoint = f"/repos/{owner}/{repo}"
        result, success = self._make_request("GET", endpoint)
        
        if not success:
            return str(result), False
        
        lines = [
            f"Repository: {result.get('full_name', 'unknown')}",
            f"Visibility: {'Private' if result.get('private') else 'Public'}",
            f"Stars: {result.get('stargazers_count', 0)}",
            f"Forks: {result.get('forks_count', 0)}",
            f"Language: {result.get('language', 'Unknown')}",
            f"Description: {result.get('description', 'No description')}",
            f"URL: {result.get('html_url', 'N/A')}",
        ]
        
        return "\n".join(lines), True
    
    def list_prs(
        self,
        owner: str,
        repo: str,
        state: str = "open",
    ) -> Tuple[str, bool]:
        has_scopes, scope_msg = self.check_scopes("pr_list")
        if not has_scopes:
            return scope_msg, False
        
        endpoint = f"/repos/{owner}/{repo}/pulls"
        result, success = self._make_request(
            "GET",
            endpoint,
            params={"state": state, "per_page": 100},
        )
        
        if not success:
            return str(result), False
        
        if not result:
            return f"No {state} pull requests found in {owner}/{repo}", True
        
        lines = [f"Found {len(result)} {state} pull requests in {owner}/{repo}:\n"]
        for pr in result[:20]:
            number = pr.get("number", "?")
            title = pr.get("title", "No title")
            user = pr.get("user", {}).get("login", "unknown")
            lines.append(f"  #{number}: {title} (by {user})")
        
        if len(result) > 20:
            lines.append(f"  ... and {len(result) - 20} more")
        
        return "\n".join(lines), True
    
    def create_pr(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> Tuple[str, bool]:
        has_scopes, scope_msg = self.check_scopes("pr_create")
        if not has_scopes:
            return scope_msg, False
        
        endpoint = f"/repos/{owner}/{repo}/pulls"
        json_data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        
        result, success = self._make_request("POST", endpoint, json_data=json_data)
        
        if not success:
            return str(result), False
        
        lines = [
            "✓ Pull request created successfully!",
            f"  Title: {result.get('title', 'Unknown')}",
            f"  PR #: {result.get('number', '?')}",
            f"  URL: {result.get('html_url', 'N/A')}",
        ]
        
        return "\n".join(lines), True
    
    def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
    ) -> Tuple[str, bool]:
        has_scopes, scope_msg = self.check_scopes("issue_list")
        if not has_scopes:
            return scope_msg, False
        
        endpoint = f"/repos/{owner}/{repo}/issues"
        result, success = self._make_request(
            "GET",
            endpoint,
            params={"state": state, "per_page": 100},
        )
        
        if not success:
            return str(result), False
        
        if not result:
            return f"No {state} issues found in {owner}/{repo}", True
        
        lines = [f"Found {len(result)} {state} issues in {owner}/{repo}:\n"]
        for issue in result[:20]:
            number = issue.get("number", "?")
            title = issue.get("title", "No title")
            user = issue.get("user", {}).get("login", "unknown")
            lines.append(f"  #{number}: {title} (by {user})")
        
        if len(result) > 20:
            lines.append(f"  ... and {len(result) - 20} more")
        
        return "\n".join(lines), True
    
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
    ) -> Tuple[str, bool]:
        has_scopes, scope_msg = self.check_scopes("issue_create")
        if not has_scopes:
            return scope_msg, False
        
        endpoint = f"/repos/{owner}/{repo}/issues"
        json_data = {
            "title": title,
            "body": body,
        }
        
        result, success = self._make_request("POST", endpoint, json_data=json_data)
        
        if not success:
            return str(result), False
        
        lines = [
            "✓ Issue created successfully!",
            f"  Title: {result.get('title', 'Unknown')}",
            f"  Issue #: {result.get('number', '?')}",
            f"  URL: {result.get('html_url', 'N/A')}",
        ]
        
        return "\n".join(lines), True
    
    def fork_repo(self, owner: str, repo: str) -> Tuple[str, bool]:
        has_scopes, scope_msg = self.check_scopes("repo_fork")
        if not has_scopes:
            return scope_msg, False
        
        endpoint = f"/repos/{owner}/{repo}/forks"
        result, success = self._make_request("POST", endpoint)
        
        if not success:
            return str(result), False
        
        lines = [
            "✓ Repository forked successfully!",
            f"  Fork: {result.get('full_name', 'Unknown')}",
            f"  URL: {result.get('html_url', 'N/A')}",
        ]
        
        return "\n".join(lines), True
    
    def parse_and_execute(self, command: str) -> str:
        command = command.strip()
        
        patterns = {
            "repo_view": r'^repo\s+view\s+([a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+)$',
            "repo_fork": r'^repo\s+fork\s+([a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+)$',
        }
        
        def parse_args(cmd: str) -> Dict[str, Any]:
            args: Dict[str, Any] = {}
            parts = cmd.split()
            i = 0
            while i < len(parts):
                part = parts[i]
                if part.startswith("--"):
                    key = part[2:]
                    if i + 1 < len(parts) and not parts[i + 1].startswith("--"):
                        args[key] = parts[i + 1]
                        i += 2
                        continue
                i += 1
            return args
        
        parts = command.split()
        if not parts:
            return "Error: Empty command. Available commands: repo list, repo view, pr list, pr create, issue list, issue create, repo fork"
        
        if parts[0] == "repo" and len(parts) > 1:
            if parts[1] == "list":
                args = parse_args(command)
                owner = args.get("owner")
                result, success = self.list_repos(owner)
                return result
            
            elif parts[1] == "view":
                match = re.match(patterns["repo_view"], command)
                if match:
                    owner_repo = match.group(1)
                    owner, repo = owner_repo.split("/", 1)
                    result, success = self.get_repo(owner, repo)
                    return result
                else:
                    return "Error: Invalid format. Use: repo view OWNER/REPO"
            
            elif parts[1] == "fork":
                match = re.match(patterns["repo_fork"], command)
                if match:
                    owner_repo = match.group(1)
                    owner, repo = owner_repo.split("/", 1)
                    result, success = self.fork_repo(owner, repo)
                    return result
                else:
                    return "Error: Invalid format. Use: repo fork OWNER/REPO"
        
        elif parts[0] == "pr" and len(parts) > 1:
            if parts[1] == "list":
                args = parse_args(command)
                owner = args.get("owner")
                repo = args.get("repo")
                if not owner or not repo:
                    return "Error: Missing required arguments. Use: pr list --owner OWNER --repo REPO [--state STATE]"
                state = args.get("state", "open")
                result, success = self.list_prs(owner, repo, state)
                return result
            
            elif parts[1] == "create":
                args = parse_args(command)
                required = ["owner", "repo", "title", "body", "head", "base"]
                missing = [r for r in required if r not in args]
                if missing:
                    return f"Error: Missing required arguments: {', '.join(missing)}. Use: pr create --owner OWNER --repo REPO --title TITLE --body BODY --head HEAD --base BASE"
                result, success = self.create_pr(
                    args["owner"],
                    args["repo"],
                    args["title"],
                    args["body"],
                    args["head"],
                    args["base"],
                )
                return result
        
        elif parts[0] == "issue" and len(parts) > 1:
            if parts[1] == "list":
                args = parse_args(command)
                owner = args.get("owner")
                repo = args.get("repo")
                if not owner or not repo:
                    return "Error: Missing required arguments. Use: issue list --owner OWNER --repo REPO [--state STATE]"
                state = args.get("state", "open")
                result, success = self.list_issues(owner, repo, state)
                return result
            
            elif parts[1] == "create":
                args = parse_args(command)
                required = ["owner", "repo", "title", "body"]
                missing = [r for r in required if r not in args]
                if missing:
                    return f"Error: Missing required arguments: {', '.join(missing)}. Use: issue create --owner OWNER --repo REPO --title TITLE --body BODY"
                result, success = self.create_issue(
                    args["owner"],
                    args["repo"],
                    args["title"],
                    args["body"],
                )
                return result
        
        return "Error: Unknown command. Available commands: repo list, repo view, pr list, pr create, issue list, issue create, repo fork"