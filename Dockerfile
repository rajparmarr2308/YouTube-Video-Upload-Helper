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

# Create a non-root user with UID and GID between 10000-20000
RUN groupadd -g 10001 appuser && useradd -u 10001 -g appuser -d /home/appuser -m appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Create upload directory with proper permissions
RUN mkdir -p uploads && chmod 777 uploads

# Pre-download NLTK data to the app directory (which we've already given permissions to)
# This avoids trying to write to /home/appuser/nltk_data at runtime
ENV NLTK_DATA /app/nltk_data
RUN mkdir -p /app/nltk_data && \
    python -m nltk.downloader -d /app/nltk_data punkt stopwords && \
    chmod -R 755 /app/nltk_data

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Create a temporary directory with appropriate permissions
RUN mkdir -p /tmp/app_temp && chmod 777 /tmp/app_temp
ENV TMPDIR /tmp/app_temp

# Switch to non-root user
USER 10001

# Command to run the application with increased max request size and timeouts
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "--limit-request-line", "8190", "--limit-request-field_size", "8190", "app:app"]
