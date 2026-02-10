#!/bin/bash

# Start Ollama in the background
ollama serve &

# Wait for Ollama to be ready (using ollama list as a health check)
echo "Waiting for Ollama service to start..."
until ollama list > /dev/null 2>&1; do
    echo "Service not ready yet, sleeping 2s..."
    sleep 2
done

# Check if model exists, if not pull it
MODEL="qwen2.5:1.5b"
if ! ollama list | grep -q "$MODEL"; then
    echo "Model $MODEL not found. Pulling..."
    ollama pull "$MODEL"
else
    echo "Model $MODEL already present."
fi

echo "Sentinel Engine is READY."

# Keep the process running
wait