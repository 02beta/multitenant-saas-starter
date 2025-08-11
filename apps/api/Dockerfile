# Multi-stage build for better caching and smaller final image
FROM python:3.11-slim AS builder

# Set working directory4
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

# Copy virtual environment from builder stage and use it
# RUN echo "🐍 Copying virtual environment from builder stage..." && \
#     cp -r /app/.venv /app/venv && \
#     echo "✅ Virtual environment copied successfully!"

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

# Create entrypoint script in a user-writable location first
RUN echo "📜 Creating entrypoint script..." && \
    echo '#!/bin/bash' > /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'echo "🚀 ================================================================================"' >> /tmp/entrypoint.sh && \
    echo 'echo "🚀 Starting FastAPI Application"' >> /tmp/entrypoint.sh && \
    echo 'echo "🚀 ================================================================================"' >> /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'echo "📋 Required environment variables for this FastAPI application:"' >> /tmp/entrypoint.sh && \
    echo 'echo "📋 -------------------------------------------------------------------------------"' >> /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'echo "🔗 Database Configuration:"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - DATABASE_URL (required)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - DATABASE_ASYNC_URL (required)"' >> /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'echo "⚙️  API Configuration:"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - DEBUG (optional, defaults to False)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - API_CORS_ORIGINS (optional, defaults to localhost ports 3000-3003, 02beta.com subdomains and any vercel or fly.dev app)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - API_VERSION (optional)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - API_TITLE (optional)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - API_DESCRIPTION (optional)"' >> /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'echo "🔐 Authentication Configuration (Supabase):"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - SUPABASE_API_URL (required)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - SUPABASE_PUBLIC_KEY (required)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - SUPABASE_SECRET_KEY (required)"' >> /tmp/entrypoint.sh && \
    echo 'echo "   - AUTH_JWT_SECRET (required)"' >> /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'echo "⚠️  Please ensure these environment variables are set before running the container."' >> /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'echo "🚀 ================================================================================"' >> /tmp/entrypoint.sh && \
    echo 'echo "🚀 Launching FastAPI on 0.0.0.0:8080"' >> /tmp/entrypoint.sh && \
    echo 'echo "🚀 ================================================================================"' >> /tmp/entrypoint.sh && \
    echo 'echo ""' >> /tmp/entrypoint.sh && \
    echo 'exec fastapi run --host 0.0.0.0 --port 8080' >> /tmp/entrypoint.sh && \
    echo "✅ Entrypoint script created successfully!"

# Copy entrypoint script to final location and set permissions
RUN echo "📋 Copying entrypoint script to final location..." && \
    cp /tmp/entrypoint.sh /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    rm /tmp/entrypoint.sh && \
    echo "✅ Entrypoint script copied and permissions set successfully!"

# Change ownership of the app directory to the non-root user
RUN echo "🔐 Changing ownership to non-root user..." && \
    chown -R appuser:appuser /app && \
    echo "✅ Ownership changed successfully!"

# Switch to non-root user
USER appuser

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/docs || exit 1

# Run the entrypoint script
CMD ["/app/entrypoint.sh"]
