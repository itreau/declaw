# GitHub PAT Token Configuration Guide

## Overview

This guide explains how to configure GitHub access using a Personal Access Token (PAT) with the REST API integration.

## Implementation

The bot uses the GitHub REST API directly (not the `gh` CLI) for all repository operations. This provides:
- Better error handling and status messages
- Direct control over API calls
- No dependency on GitHub CLI installation
- Clearer permission boundaries

## Why Use a PAT Token?

- **Security**: Limit permissions to only what's needed
- **Control**: Revoke access without changing passwords
- **Auditing**: Track which token was used for what operations
- **Isolation**: Separate bot access from personal GitHub account

## Setup

### Step 1: Create a GitHub PAT Token

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token"
3. Select scopes based on your needs:
   - **Read-only public repos**: `public_repo`
   - **Read-only private repos**: `repo:read` or `repo`
   - **Create PRs/issues**: `repo:write` or `repo`
   - **Full access**: `repo`
4. Copy the token (you won't see it again!)

### Step 2: Add to Configuration

Add `GITHUB_TOKEN` to your `.env` file:

```env
GITHUB_TOKEN=ghp_your_token_here
```

The configuration is already set up in `src/models/config.py` to read the `GITHUB_TOKEN` environment variable. No additional code changes needed.

### Step 3: Test the Configuration

```bash
# In Slack
@bot /github repo list
```

If configured correctly, you'll see a list of your repositories. If not, you'll see a clear error message.

## Required Scopes

Choose scopes based on what operations you need:

| Operation | Minimum Scopes |
|-----------|----------------|
| List repos (public) | `public_repo` |
| List repos (private) | `repo:read` or `repo` |
| View repo details | Same as listing |
| List PRs/issues | Same as viewing |
| Create PR/issue | `repo:write` or `repo` |
| Fork repository | `repo:write` or `repo` |

## Docker Configuration

For Docker deployments, use environment variables:

```yaml
# docker-compose.yml
services:
  pyagent:
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
```

Or use Docker secrets for enhanced security:

```yaml
services:
  pyagent:
    environment:
      - GITHUB_TOKEN_FILE=/run/secrets/github_token
    secrets:
      - github_token

secrets:
  github_token:
    file: ./secrets/github_token.txt
```

Create the secrets file:

```bash
echo "ghp_your_token_here" > secrets/github_token.txt
chmod 600 secrets/github_token.txt
```

## Security Best Practices

### 1. Minimal Scopes

Only grant the minimum required permissions:

- **Read public repos**: `public_repo`
- **Read private repos**: `repo:read`
- **Write to repos**: `repo:write` or `repo`
- **Create PRs and issues**: `repo:write` or `repo`

### 2. Never Commit Tokens

- Add `.env` to `.gitignore`
- Never commit tokens to version control
- Use environment variables or secrets

### 3. Token Rotation

- Rotate tokens regularly (every 30-90 days)
- Use fine-grained tokens with expiration dates
- Monitor token usage in GitHub settings

### 4. Docker Security

- Use Docker secrets or environment files
- Mount secrets as read-only
- Never bake tokens into Docker images

## Troubleshooting

### Token Not Working

1. Check token is valid in GitHub settings
2. Verify token hasn't expired
3. Check token has required scopes for the operation
4. Ensure `.env` file is loaded

### Permission Denied

1. Token doesn't have required scopes - add `repo:write` for PR/issue creation
2. Repository is private and token lacks `repo` scope
3. Organization requires SSO - enable SSO for the token in GitHub settings

### Command Returns Empty Results

1. Check repository exists and is accessible
2. For private repos, ensure token has `repo:read` or `repo` scope
3. For organization repos, ensure token has organization access

### Docker: Token Not Found

1. Verify secret file exists
2. Check file permissions (600)
3. Ensure secret is mounted correctly
4. Check environment variable name matches (`GITHUB_TOKEN`)

## Additional Documentation

For detailed command syntax and examples, see [GITHUB_REST_API.md](./GITHUB_REST_API.md).