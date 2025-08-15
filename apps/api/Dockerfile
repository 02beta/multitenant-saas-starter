# Multi-stage build for better caching and smaller final image
FROM python:3.11-slim AS builder

# Set working directory
ENV APP_HOME=/app
WORKDIR $APP_HOME

# Install system dependencies for building
RUN echo "🔧 Installing system dependencies for building..." && \
    apt-get update && apt-get install -y \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    echo "✅ System dependencies installed successfully!"

# Install uv with proper PATH setup
RUN echo "📦 Installing uv package manager..." && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo "✅ uv package manager installed successfully!"

# Add uv to PATH for current shell session
ENV PATH="/root/.local/bin:$PATH"

# Copy the entire monorepo structure to maintain workspace dependencies
RUN echo "📂 Copying monorepo structure..."
COPY . .
RUN echo "✅ Monorepo structure copied successfully!"

# Install dependencies only for the API project and create lock/venv if needed
RUN echo "🔄 Syncing API dependencies with uv..." && \
    cd apps/api && \
    /root/.local/bin/uv sync --frozen --no-dev && \
    echo "✅ API dependencies synced successfully!"

# Export API requirements.txt from the API project
RUN echo "📝 Exporting API requirements.txt..." && \
    cd apps/api && \
    /root/.local/bin/uv export --no-hashes --no-dev --format requirements-txt --output-file requirements.txt && \
    echo "✅ API requirements exported successfully!"

# Production stage
FROM python:3.11-slim AS production

# Set working directory
ENV APP_HOME=/app
WORKDIR $APP_HOME

# Set environment variables
ENV PYTHONPATH=$APP_HOME/apps/api
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for runtime
RUN echo "🔧 Installing runtime system dependencies..." && \
    apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    echo "✅ Runtime system dependencies installed successfully!"

# Install uv for production
RUN echo "📦 Installing uv for production..." && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo "✅ uv installed for production successfully!"

# Add uv to PATH for production
ENV PATH="/root/.local/bin:$PATH"

# Copy the entire monorepo from builder stage
RUN echo "📂 Copying monorepo from builder stage..."
COPY --from=builder /app .
RUN echo "✅ Monorepo copied from builder stage successfully!"

# Use the virtual environment from the builder stage
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user
RUN echo "👤 Creating non-root user..." && \
    groupadd -r appuser && useradd -r -g appuser appuser && \
    echo "✅ Non-root user created successfully!"

# Expose port 8080
EXPOSE 8080

# Change to the API directory
WORKDIR $APP_HOME/apps/api

# Change ownership of the app directory to the non-root user
RUN echo "🔐 Changing ownership to non-root user..." && \
    chown -R appuser:appuser /app && \
    echo "✅ Ownership changed successfully!"

# Switch to non-root user
USER appuser

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/docs || exit 1

# Run the FastAPI app in production mode using start.py
CMD ["uv", "run", "python", "apps/api/start.py"]
