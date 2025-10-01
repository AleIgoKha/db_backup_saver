# Use official Python image as base
FROM python:3.13-slim

# Install PostgreSQL client for pg_dump
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Default command to run your script
CMD ["python", "script.py"]
