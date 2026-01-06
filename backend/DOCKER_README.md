# Docker Production Setup

This directory contains Docker configuration files for running the FairPath backend in production.

## Files

- `Dockerfile` - Standard production Dockerfile
- `Dockerfile.prod` - Production-optimized Dockerfile with additional optimizations
- `docker-compose.yml` - Docker Compose configuration for development/testing
- `docker-compose.prod.yml` - Docker Compose configuration for production
- `.dockerignore` - Files to exclude from Docker build context
- `.env.production.example` - Example production environment variables

## Quick Start

### Using Docker Compose (Recommended)

1. **Copy the example environment file:**
   ```bash
   cp .env.production.example .env.production
   ```

2. **Edit `.env.production` with your actual values:**
   - Set `OPENAI_API_KEY` to your OpenAI API key
   - Configure `CORS_ORIGINS` with your frontend domain(s)
   - Adjust other settings as needed

3. **Build and run:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

4. **Check logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

5. **Stop the service:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -f Dockerfile.prod -t fairpath-backend:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name fairpath-backend \
     -p 8000:8000 \
     --env-file .env.production \
     -v $(pwd)/artifacts:/app/artifacts \
     -v $(pwd)/data:/app/data \
     --restart unless-stopped \
     fairpath-backend:latest
   ```

3. **Check logs:**
   ```bash
   docker logs -f fairpath-backend
   ```

4. **Stop the container:**
   ```bash
   docker stop fairpath-backend
   docker rm fairpath-backend
   ```

## Health Checks

The container includes a health check endpoint. You can verify the service is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "data_loaded": true
}
```

## Volumes

The Docker setup mounts two volumes:
- `./artifacts` - Contains ML models and processed data
- `./data` - Contains source data files

These volumes ensure that:
- Model updates persist across container restarts
- Data files are accessible to the application

## Production Considerations

1. **Environment Variables**: Never commit `.env.production` to version control. Use secrets management in your deployment platform.

2. **Resource Limits**: The `docker-compose.prod.yml` includes resource limits. Adjust based on your server capacity:
   - CPU: 2 cores limit, 1 core reserved
   - Memory: 2GB limit, 1GB reserved

3. **Workers**: The default is 4 workers. Adjust in the Dockerfile CMD based on your CPU cores: `(2 x CPU cores) + 1`

4. **Logging**: Logs are configured to rotate (max 10MB per file, 3 files) in production compose file.

5. **Security**: The container runs as a non-root user (appuser) for better security.

6. **CORS**: Make sure to set `CORS_ORIGINS` to your actual frontend domain(s) in production.

## Troubleshooting

### Container won't start
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Verify environment variables are set correctly
- Ensure port 8000 is not already in use

### Health check failing
- Check if models are loaded: `curl http://localhost:8000/health`
- Verify artifacts directory contains model files
- Check application logs for errors

### Out of memory
- Reduce the number of workers in the Dockerfile CMD
- Increase memory limits in docker-compose.prod.yml
- Check for memory leaks in the application

## Updating the Application

1. **Pull latest code:**
   ```bash
   git pull
   ```

2. **Rebuild and restart:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

The container will automatically restart with the new code.


