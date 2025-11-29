# Hugging Face Spaces Dockerfile
# MCP Energy Hub - MCP's 1st Birthday Hackathon
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0 \
    sqlalchemy==2.0.25 \
    aiosqlite==0.19.0 \
    httpx==0.26.0 \
    aiohttp==3.9.1 \
    apscheduler==3.10.4 \
    python-dotenv==1.0.0 \
    gradio>=4.0.0

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create data directory for SQLite with correct permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

# Set environment
ENV DATABASE_URL="sqlite+aiosqlite:///./data/mcp_energy.db"
ENV EIA_API_KEY="1ZcuqVdyzysHYlYp6tyJgfvEBJwMOMklQ5ywwSjT"
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Expose port (Hugging Face uses 7860)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start script: initialize DB, load data, then start server
CMD ["sh", "-c", "python startup.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 7860"]
