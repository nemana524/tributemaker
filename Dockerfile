# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads/images uploads/videos uploads/music assets/music

# Expose port
EXPOSE $PORT

# Start command
CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 2 --timeout 120 --preload 