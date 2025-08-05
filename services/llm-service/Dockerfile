FROM nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
# Set up virtual environment
RUN python3 -m venv /opt/venv

# Activate it and install requirements
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["python", "vllm_server.py"]