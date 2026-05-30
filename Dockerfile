FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application
COPY server.py .

# Trust torch.hub repositories
ENV TORCH_HUB_TRUST_REPO="*"

EXPOSE 8000

CMD ["python", "server.py"]
