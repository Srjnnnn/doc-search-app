FROM python:3.9-slim

# Install system dependencies including git and the C compiler
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and its home directory
RUN useradd -ms /bin/bash vllmuser
USER vllmuser
WORKDIR /home/vllmuser/app

# CORRECTED: Create the virtual environment inside the user's home directory
RUN python3 -m venv /home/vllmuser/venv

# CORRECTED: Update the PATH to point to the new venv location
ENV PATH="/home/vllmuser/venv/bin:$PATH"

# Copy and install Python dependencies
COPY --chown=vllmuser:vllmuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=vllmuser:vllmuser . .

# Expose the application port
EXPOSE 8002

# Add a health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python", "vllm_server.py"]