FROM python:3.11-slim

WORKDIR /app

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
COPY services/user-service/ ./services/user-service/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Run the service
CMD ["python", "services/user-service/main.py"] 