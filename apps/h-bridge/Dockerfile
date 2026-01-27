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
    surrealdb==1.0.8 \
    python-dotenv

# Copy the application
COPY . .

ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "src/main.py"]
