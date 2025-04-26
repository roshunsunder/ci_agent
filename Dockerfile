# Use an official Python 3.12 image as the base
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for Poetry
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Poetry (Ensure Poetry installs globally and doesn't require virtualenvs inside the container)
RUN curl -sSL https://install.python-poetry.org | python3.12 - && \
    echo "export PATH=$HOME/.local/bin:$PATH" >> ~/.bashrc && \
    /root/.local/bin/poetry config virtualenvs.create false

# Copy only the dependency files first for caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN /root/.local/bin/poetry install --no-root

# Copy the rest of the application
COPY . .

# Expose the FastAPI port
EXPOSE 8080
