FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy configuration
COPY pyproject.toml poetry.lock* ./

# Disable virtualenvs creation (since we are in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy source code
COPY src ./src

# Expose port (default for uvicorn/fastapi)
EXPOSE 8000

# Command to run the app (will fail if main.py is missing, but that's for next stories)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
