FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for rembg and onnxruntime
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    redis \
    pydantic \
    pyyaml \
    watchdog \
    litellm \
    "litellm[google]" \
    google-cloud-aiplatform \
    google-genai \
    httpx \
    surrealdb \
    pillow \
    fastembed

# Copy the application
COPY . .

ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "src/main.py"]
