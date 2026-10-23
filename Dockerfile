# ==============================================================================
# Stage 1: Build Frontend (Vite + React + Tailwind)
# ==============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Python Backend & Unified Production Runner
# ==============================================================================
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Initialize SQLite database and baseline seed data
WORKDIR /app/backend
RUN python ../scripts/seed_demo_data.py

EXPOSE 8000

# Run FastAPI server binding to $PORT (dynamically assigned by Render / Railway / Cloud)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
