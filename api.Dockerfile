# Use an official Python runtime as a parent image
FROM python:3.13-alpine

# Set work directory
WORKDIR /app/api

# RUN apk update && apk add --update \
#     alpine-sdk \
#     && apk -v cache clean \
#     && apk cache -v sync

# Install Python dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api /app/api

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000

# Define default command
CMD ["python", "main.py"]