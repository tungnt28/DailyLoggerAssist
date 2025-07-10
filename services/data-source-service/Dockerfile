FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set Python path
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ ./shared/

# Copy service code
COPY services/data-source-service/ ./services/data-source-service/

# Expose port
EXPOSE 8006

# Run the service
CMD ["python", "services/data-source-service/main.py"] 