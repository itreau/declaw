# Docker Setup Guide

## Overview

PyAgent can run in a Docker container for easy deployment and isolation. The container connects to Ollama and OpenCode running on your host machine.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Ollama installed and running on host
- OpenCode CLI installed on host (`/opt/homebrew/bin/opencode`)

## Quick Start

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Slack tokens
nano .env
```

### 2. Build and Run

```bash
# Build and start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

That's it! The bot is now running in Docker.

## Configuration

### Environment Variables

The container uses the same `.env` file as local execution, with one important difference:

**Ollama URL**: Must use `host.docker.internal` instead of `localhost`

```env
# Local execution
OLLAMA_URL=http://localhost:11434

# Docker execution (auto-configured in docker-compose.yml)
OLLAMA_URL=http://host.docker.internal:11434
```

The `docker-compose.yml` automatically sets this for you.

### Volume Mounts

The Docker setup mounts two volumes:

1. **Output directory**: `./output:/app/output`
   - Persists long outputs across container restarts
   - Accessible from host machine

2. **OpenCode binary**: `/opt/homebrew/bin/opencode:/usr/local/bin/opencode:ro`
   - Mounts OpenCode from host into container
   - Read-only (`:ro`) for security
   - Allows container to use host's OpenCode installation

### Network Configuration

The container uses `host.docker.internal` to connect to services on the host:

- **Ollama**: `http://host.docker.internal:11434`
- **No ports exposed**: Slack uses outbound HTTPS only

For Linux, the `extra_hosts` configuration enables `host.docker.internal`:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

## Manual Docker Commands

### Build Image

```bash
docker build -t pyagent:latest .
```

### Run Container

```bash
docker run -d \
  --name pyagent \
  --env-file .env \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  -v $(pwd)/output:/app/output \
  -v /opt/homebrew/bin/opencode:/usr/local/bin/opencode:ro \
  --add-host=host.docker.internal:host-gateway \
  pyagent:latest
```

### View Logs

```bash
docker logs -f pyagent
```

### Stop Container

```bash
docker stop pyagent
docker rm pyagent
```

## Dockerfile Details

The Dockerfile creates a minimal, secure image:

```dockerfile
FROM python:3.9-slim

# Create non-root user for security
RUN useradd -m -u 1000 pyagent

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY agent.py .

# Create output directory
RUN mkdir -p /app/output && chown -R pyagent:pyagent /app

# Run as non-root user
USER pyagent

CMD ["python", "agent.py"]
```

**Key features**:
- **Slim base image**: `python:3.9-slim` (~150MB)
- **Non-root user**: Security best practice
- **No cache**: Reduces image size
- **Minimal layers**: Faster builds

## Platform-Specific Notes

### macOS

Docker Desktop for macOS automatically provides `host.docker.internal`:

```yaml
# No extra configuration needed
environment:
  - OLLAMA_URL=http://host.docker.internal:11434
```

### Linux

Linux requires `extra_hosts` configuration:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This maps `host.docker.internal` to the host's gateway IP.

### Windows

Docker Desktop for Windows supports `host.docker.internal` automatically:

```yaml
# Same as macOS
environment:
  - OLLAMA_URL=http://host.docker.internal:11434
```

## Customization

### Change OpenCode Path

If OpenCode is installed at a different location, edit `docker-compose.yml`:

```yaml
volumes:
  - /path/to/your/opencode:/usr/local/bin/opencode:ro
```

### Change Output Directory

```yaml
volumes:
  - /custom/output/path:/app/output
```

### Use Different Ollama URL

If Ollama runs on a different server:

```yaml
environment:
  - OLLAMA_URL=http://your-server:11434
```

### Add Environment Variables

```yaml
environment:
  - OLLAMA_URL=http://host.docker.internal:11434
  - MAX_OUTPUT_LENGTH=500
  - TOOL_TIMEOUT=300
```

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
docker-compose logs pyagent
```

**Common issues**:
1. Missing `.env` file
2. Invalid Slack tokens
3. Ollama not running on host

### Ollama Connection Failed

**Symptoms**:
```
Error: Cannot connect to Ollama at http://host.docker.internal:11434
```

**Solutions**:

1. **Check Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check Docker network** (Linux only):
   ```bash
   # Ensure extra_hosts is in docker-compose.yml
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

3. **Use IP address** (fallback):
   ```bash
   # Get host IP
   ip route show default | awk '/default/ {print $3}'
   
   # Use in docker-compose.yml
   environment:
     - OLLAMA_URL=http://172.17.0.1:11434
   ```

### OpenCode Not Found

**Symptoms**:
```
Error: opencode: command not found
```

**Solutions**:

1. **Check OpenCode path**:
   ```bash
   which opencode
   # Output: /opt/homebrew/bin/opencode
   ```

2. **Update docker-compose.yml**:
   ```yaml
   volumes:
     - /actual/path/to/opencode:/usr/local/bin/opencode:ro
   ```

3. **Verify mount**:
   ```bash
   docker exec pyagent which opencode
   # Should output: /usr/local/bin/opencode
   ```

### Permission Denied

**Symptoms**:
```
Error: Permission denied: /app/output
```

**Solutions**:

1. **Fix output directory permissions**:
   ```bash
   mkdir -p output
   chmod 755 output
   ```

2. **Check ownership**:
   ```bash
   # Container runs as UID 1000
   chown -R 1000:1000 output/
   ```

### Container Restarts Continuously

**Check logs**:
```bash
docker-compose logs --tail=100 pyagent
```

**Common causes**:
1. Invalid Slack tokens
2. Missing environment variables
3. Ollama connection failure
4. OpenCode mount failure

### Slow Performance

**Symptoms**: Container is slow or unresponsive

**Solutions**:

1. **Check resources**:
   ```bash
   docker stats pyagent
   ```

2. **Increase Docker resources** (Docker Desktop):
   - Settings → Resources → Memory/CPU

3. **Check Ollama performance**:
   ```bash
   # Test Ollama directly
   time curl http://localhost:11434/api/generate -d '{"model":"qwen2.5-coder:14b","prompt":"test"}'
   ```

## Security Considerations

### Secrets Management

- **Never commit `.env`** file to Git
- Use Docker secrets for production (Swarm/Kubernetes)
- Rotate Slack tokens regularly

### Network Security

- **No exposed ports**: Container only makes outbound connections
- **Host networking**: Limited to necessary services
- **Read-only mounts**: OpenCode binary mounted as read-only

### User Permissions

- **Non-root user**: Container runs as `pyagent` user (UID 1000)
- **Limited capabilities**: No special Docker capabilities needed
- **Resource limits**: Can add resource constraints

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
```

## Production Deployment

### Use Specific Image Version

```yaml
image: pyagent:1.0.0  # Instead of 'latest'
```

### Add Health Check

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('https://slack.com/api/api.test')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Add Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '1'
      memory: 512M
```

### Use Docker Secrets

```yaml
secrets:
  slack_bot_token:
    file: ./secrets/slack_bot_token.txt

services:
  pyagent:
    secrets:
      - slack_bot_token
```

### Logging Configuration

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Advanced Usage

### Multi-Container Setup

If you want to run Ollama in Docker too:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  pyagent:
    build: .
    depends_on:
      - ollama
    environment:
      - OLLAMA_URL=http://ollama:11434
    # ... rest of config

volumes:
  ollama_data:
```

### Custom Network

```yaml
networks:
  pyagent_network:
    driver: bridge

services:
  pyagent:
    networks:
      - pyagent_network
```

### Environment-Specific Configs

```yaml
# docker-compose.yml (base)
version: '3.8'
services:
  pyagent:
    build: .

# docker-compose.prod.yml (production overrides)
version: '3.8'
services:
  pyagent:
    image: pyagent:1.0.0
    deploy:
      replicas: 2
```

```bash
# Run with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Maintenance

### Update Image

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### View Resource Usage

```bash
docker stats pyagent
```

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi pyagent:latest

# Remove volumes (if not needed)
docker volume prune
```

### Backup Output Directory

```bash
# Create backup
tar -czf output-backup-$(date +%Y%m%d).tar.gz output/

# Restore backup
tar -xzf output-backup-20240101.tar.gz
```

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs -f`
3. Check GitHub issues
4. Consult [USAGE.md](USAGE.md) for bot usage questions
