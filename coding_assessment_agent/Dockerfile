# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by psycopg2 or other libs
# Add other dependencies if needed (e.g., build-essential for C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Add any system dependencies here, e.g., postgresql-client if needed for checks
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini ./
# DO NOT copy .env file - provide environment variables at runtime

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Use Gunicorn for production deployments typically, but uvicorn is fine for basics
# Note: The number of workers might need adjustment based on the server resources
# CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
# For simplicity, using uvicorn directly:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 