FROM python:3.14.2-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite and PDFs
RUN mkdir -p /app/data/invoices

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port for FastAPI
EXPOSE 8000

# Run migrations then start app
CMD ["/app/entrypoint.sh"]
