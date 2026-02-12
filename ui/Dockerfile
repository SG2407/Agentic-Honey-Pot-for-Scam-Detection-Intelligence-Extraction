# Dockerfile for UI Backend and Streamlit
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy UI requirements
COPY ui/requirements_ui.txt ui/requirements_ui.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r ui/requirements_ui.txt

# Copy UI code
COPY ui/ ui/

# Create directory for database
RUN mkdir -p ui/data

# Expose ports
# 8001 for UI backend
# 8501 for Streamlit
EXPOSE 8001 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "ui.ui_backend:app", "--host", "0.0.0.0", "--port", "8001"]
