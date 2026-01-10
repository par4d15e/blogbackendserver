# Use Python 3.13 as base image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm

# Install required tools and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        ffmpeg \
        procps \
        fontconfig \
        default-mysql-client \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user for running the application
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -d /server -s /bin/bash appuser

# Set working directory
WORKDIR /server

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PATH="/server/.venv/bin:$PATH"


# Copy project files
COPY pyproject.toml uv.lock ./
COPY README.md ./
COPY app ./app
# alembic and alembic.ini are mounted via volume, not copied to image
COPY static ./static
COPY script/setup-server.sh ./script/setup-server.sh

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Make startup script executable
RUN chmod +x /server/script/setup-server.sh

# Ensure appuser can access necessary directories and files
# Create Celery working directory and set permissions
RUN mkdir -p /server/.celery /var/cache/fontconfig && \
    chown -R appuser:appuser /server/.celery && \
    chmod -R 777 /var/cache/fontconfig && \
    chmod -R o+rX /server && \
    chmod -R o+w /server/.venv 2>/dev/null || true

# Expose port
EXPOSE 8000



# Use startup script as entrypoint
ENTRYPOINT ["/server/script/setup-server.sh"]

