# Orchestrator Service - FastAPI Backend
# Builds Python 3.11 slim image with FastAPI and Ollama client dependencies

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
# Note: --reload enables hot-reloading for development (works with volume mount)
# For production, remove --reload flag
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]