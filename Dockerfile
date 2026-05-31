FROM python:3.13-slim

# Install curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-install-project --no-dev

# Copy project files
COPY . .

# Install project
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8000

# Start hypercorn
CMD uv run hypercorn main:app --bind 0.0.0.0:8000 --workers ${WORKERS:-16}
