FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords

# Copy the application code
COPY . .

# Create upload directory
RUN mkdir -p uploads && chmod 777 uploads

# Create a non-root user with UID and GID between 10000-20000
RUN groupadd -g 10001 appuser && useradd -u 10001 -g appuser -d /home/appuser -m appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Expose the port the app runs on
EXPOSE 8080

# Switch to non-root user
USER 10001

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
