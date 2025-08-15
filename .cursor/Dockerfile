# Dockerfile for Cursor Background Agents
# This Dockerfile provides the base environment for background agents
# It should NOT copy in code (agent will clone it later)
# It SHOULD include all development tools needed

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for development
RUN echo "🔧 Installing system dependencies for development..." && \
    apt-get update && apt-get install -y \
    gcc \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/* && \
    echo "✅ System dependencies installed successfully!"

# Install uv package manager
RUN echo "📦 Installing uv package manager..." && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo "✅ uv package manager installed successfully!"

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Install Node.js and pnpm for frontend development
RUN echo "📦 Installing Node.js and pnpm..." && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pnpm && \
    echo "✅ Node.js and pnpm installed successfully!"

# Install Turbo for monorepo management
RUN echo "📦 Installing Turbo..." && \
    npm install -g turbo && \
    echo "✅ Turbo installed successfully!"

# Create ubuntu user and set up home directory
RUN echo "👤 Creating ubuntu user..." && \
    useradd -m -s /bin/bash ubuntu && \
    echo "✅ ubuntu user created successfully!"

# Set working directory to ubuntu's home
WORKDIR /home/ubuntu

# Change ownership of home directory
RUN chown -R ubuntu:ubuntu /home/ubuntu

# Switch to ubuntu user
USER ubuntu

# Set up environment for ubuntu user
ENV PATH="/home/ubuntu/.local/bin:$PATH"

# Install development tools for ubuntu user
RUN echo "🔧 Installing development tools for ubuntu user..." && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo "✅ Development tools installed successfully!"

# Add uv to PATH for ubuntu user
ENV PATH="/home/ubuntu/.local/bin:$PATH"

# Set default shell
SHELL ["/bin/bash", "-c"]

# The agent will clone the code into this directory later
# No CMD or ENTRYPOINT needed - the agent will handle execution
