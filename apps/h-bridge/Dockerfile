FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    redis \
    pydantic \
    surrealdb \
    httpx \
    google-genai \
    Pillow

# Copy the application and shared infrastructure
COPY . .
COPY src/infrastructure/graph_schema.surql src/infrastructure/graph_schema.surql

ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "src/main.py"]
