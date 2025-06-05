# Use Red Hat Universal Base Image 9 with Python 3.12
FROM registry.access.redhat.com/ubi9/python-312:latest

# Set metadata
LABEL name="mcp-todo-server" \
      version="1.0.0" \
      description="MCP Todo Server with MCPO support" \
      maintainer="your-email@example.com"

# Switch to root to install additional packages (if needed)
USER root

# Install any additional system packages if needed
# RUN dnf update -y && \
#     dnf install -y curl && \
#     dnf clean all && \
#     rm -rf /var/cache/dnf

# Set working directory
WORKDIR /opt/app-root/src

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir mcpo

# Copy application source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY docs/ ./docs/

# Create data directory for persistent storage
RUN mkdir -p /opt/app-root/src/data

# Switch back to the default user (already configured in the base image)
USER 1001

# Expose the port MCPO will use
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/opt/app-root/src \
    PYTHONUNBUFFERED=1 \
    TODO_STORAGE_PATH=/opt/app-root/src/data/todos.json \
    MCPO_API_KEY=top-secret

# Health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command to run MCPO with the todo server
CMD ["sh", "-c", "mcpo --port 8000 --api-key \"${MCPO_API_KEY}\" -- python src/todo_server.py"]
