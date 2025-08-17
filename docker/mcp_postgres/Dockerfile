# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' mcpuser \
    && chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port
EXPOSE 3003

# Health check - test if the MCP server can start
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from src.mcp_postgres.__main__ import main; asyncio.run(main())" || exit 1

# Run the PostgreSQL MCP server
CMD ["python", "-m", "src.mcp_postgres", "--host", "0.0.0.0", "--port", "3003", "--log-level", "INFO", "--no-auth"]
