# Multi-stage Dockerfile for Network Investigation Agent
# Builds both backend (FastAPI) and frontend (React)

# ============================================================================
# Stage 1: Backend Builder
# ============================================================================
FROM python:3.11-slim as backend-builder

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependency files
COPY pyproject.toml ./
COPY starter_code/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e . || \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Frontend Builder
# ============================================================================
FROM node:18-alpine as frontend-builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# ============================================================================
# Stage 3: Backend Runtime
# ============================================================================
FROM python:3.11-slim as backend

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY starter_code/ ./starter_code/
COPY db/ ./db/

# Create directory for DuckDB database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DUCKDB_PATH=/app/data/network_rca.duckdb

WORKDIR /app/starter_code

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# Stage 4: Frontend Runtime (Nginx)
# ============================================================================
FROM nginx:alpine as frontend

# Copy built frontend from builder
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
