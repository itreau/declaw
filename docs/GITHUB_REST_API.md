# GitHub REST API Integration

This document describes the GitHub REST API integration using Personal Access Tokens (PAT).

## Overview

The bot uses the GitHub REST API for all repository operations instead of the `gh` CLI. This provides:
- Better error handling and status messages
- Direct control over API calls
- No dependency on GitHub CLI installation
- Clearer permission boundaries

## Supported Operations

### Repository Operations

#### List Repositories

```bash
# List authenticated user's repos
/github repo list

# List specific user's public repos
/github repo list --owner microsoft

# List organization repos
/github repo list --owner python
```

**Required scopes**: `public_repo` (for public repos), `repo:read` (for private repos)

#### View Repository Details

```bash
/github repo view owner/repo
```

**Required scopes**: `public_repo` (for public repos), `repo:read` (for private repos)

#### Fork Repository

```bash
/github repo fork owner/repo
```

**Required scopes**: `repo:write`

---

### Pull Request Operations

#### List Pull Requests

```bash
/github pr list --owner owner --repo repo

# List closed PRs
/github pr list --owner owner --repo repo --state closed

# List all PRs
/github pr list --owner owner --repo repo --state all
```

**Required scopes**: `public_repo` (for public repos), `repo:read` (for private repos)

#### Create Pull Request

```bash
/github pr create --owner owner --repo repo --title "Fix bug" --body "Description" --head feature-branch --base main
```

**Required scopes**: `repo:write`

---

### Issue Operations

#### List Issues

```bash
/github issue list --owner owner --repo repo

# List closed issues
/github issue list --owner owner --repo repo --state closed

# List all issues
/github issue list --owner owner --repo repo --state all
```

**Required scopes**: `public_repo` (for public repos), `repo:read` (for private repos)

#### Create Issue

```bash
/github issue create --owner owner --repo repo --title "Bug report" --body "Detailed description"
```

**Required scopes**: `repo:write`

---

## Authentication

### Getting a Personal Access Token

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "PyAgent Bot")
4. Select scopes based on your needs:
   - **Read-only**: `public_repo`
   - **Read private repos**: `repo:read`
   - **Create PRs/issues**: `repo:write`
   - **Full access**: `repo`
5. Click "Generate token"
6. Copy the token (you won't see it again!)

### Configuration

Add your token to `.env`:

```env
GITHUB_TOKEN=ghp_your_token_here
```

### Required Scopes by Operation

| Operation | Minimum Scopes |
|-----------|----------------|
| List repos (public) | `public_repo` |
| List repos (private) | `repo:read` or `repo` |
| View repo (public) | `public_repo` |
| View repo (private) | `repo:read` or `repo` |
| List PRs/issues | Same as viewing repos |
| Create PR/issue | `repo:write` or `repo` |
| Fork repository | `repo:write` or `repo` |

---

## Natural Language Commands

The tool supports natural language commands that are parsed into REST API calls:

| Command Pattern | Example |
|----------------|---------|
| `repo list [--owner OWNER]` | `repo list`, `repo list --owner microsoft` |
| `repo view OWNER/REPO` | `repo view python/cpython` |
| `repo fork OWNER/REPO` | `repo fork facebook/react` |
| `pr list --owner OWNER --repo REPO [--state STATE]` | `pr list --owner facebook --repo react --state open` |
| `pr create --owner OWNER --repo REPO --title TITLE --body BODY --head HEAD --base BASE` | See examples above |
| `issue list --owner OWNER --repo REPO [--state STATE]` | `issue list --owner facebook --repo react` |
| `issue create --owner OWNER --repo REPO --title TITLE --body BODY` | See examples above |

---

## Error Handling

The tool provides clear error messages for common issues:

### Authentication Errors

```
Error: Invalid or expired GitHub token. Please check your GITHUB_TOKEN environment variable.
```

**Solution**: Verify your token is correct and hasn't expired.

### Permission Errors

```
Permission denied. Your token has scopes: ['public_repo']. Additional scopes may be required for this operation.
```

**Solution**: Add the required scopes to your token at https://github.com/settings/tokens

### Missing Token

```
Error: GITHUB_TOKEN not configured. Add GITHUB_TOKEN to your .env file.
Get a token at: https://github.com/settings/tokens
Required scopes: 'repo:read' for read operations, 'repo:write' for PR/issue creation.
```

**Solution**: Create a token and add it to `.env`.

### Repository Not Found

```
Resource not found: /repos/owner/repo
```

**Solution**: Verify the repository exists and you have access to it.

---

## Testing

Test your configuration:

```bash
# In Slack
@bot /github repo list

# Should list your repositories or show a clear error message
```

---

## Rate Limits

GitHub API has rate limits:
- **Authenticated**: 5000 requests per hour
- **Unauthenticated**: 60 requests per hour (not supported by this integration)

The tool will return a clear message when rate limits are hit:

```
Rate limit exceeded. Resets at: <timestamp>
```

---

## Alternative: gh CLI (Deprecated)

The previous implementation used the `gh` CLI. This has been replaced with REST API calls for better error handling and control. The `gh` CLI is no longer required or supported.

---

## Troubleshooting

### Token Validation Failed

1. Check token format: should start with `ghp_` (classic) or `github_pat_` (fine-grained)
2. Verify token hasn't expired
3. Check required scopes are enabled
4. For organization repos, ensure SSO is enabled for the token

### Operation Returns Empty Results

1. Check repository exists: `repo view owner/repo`
2. Check repository visibility matches token scopes
3. For private repos, ensure `repo:read` or `repo` scope
4. For organization repos, ensure token has organization access

### Permission Denied

1. Go to GitHub Settings → Tokens
2. Find your token
3. Click "Edit"
4. Add missing scopes
5. Save changes

---

## Security Best Practices

1. **Never commit tokens** - Add `.env` to `.gitignore`
2. **Use minimal scopes** - Only grant what's needed
3. **Rotate tokens** - Create new tokens every 30-90 days
4. **Use fine-grained tokens** - For better security (GitHub's modern token format)
5. **Monitor usage** - Check token usage in GitHub settings regularly