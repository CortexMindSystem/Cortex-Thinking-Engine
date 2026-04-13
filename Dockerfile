# CortexOS API Dockerfile
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY cortex_core/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY cortex_core/ ./cortex_core/

# Expose port
EXPOSE 8420

# Run API server
CMD ["python", "-m", "cortex_core.api.server"]
