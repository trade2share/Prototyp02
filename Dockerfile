# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Chainlit port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV CHAINLIT_PORT=8000
ENV CHAINLIT_HOST=0.0.0.0

# Health check (Chainlit root should return 200)
HEALTHCHECK CMD curl --fail http://localhost:8000/ || exit 1

# Run the application (Chainlit)
CMD ["chainlit", "run", "main_chainlit.py", "--port", "8000", "--host", "0.0.0.0"]
