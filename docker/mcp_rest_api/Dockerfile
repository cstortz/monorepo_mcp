FROM python:3.11-slim

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Add src to Python path
ENV PYTHONPATH=/app/src

# Create logs directory and set permissions
RUN mkdir -p /app/logs && chown mcpuser:mcpuser /app/logs

# Switch to non-root user
USER mcpuser

# Expose port
EXPOSE 3004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 3004), timeout=5)" || exit 1

# Run the server
CMD ["python", "-m", "mcp_rest_api", "--host", "0.0.0.0", "--port", "3004", "--log-level", "INFO"]
