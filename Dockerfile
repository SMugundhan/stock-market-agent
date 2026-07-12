# Dockerfile

# ── Base Image ────────────────────────────────────────
FROM python:3.11-slim
# python:3.11-slim = Debian Linux + Python 3.11, nothing else
# ~125MB vs ~1GB for the full image

# ── System dependencies ───────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*
# gcc = C compiler needed by some Python packages (e.g. numpy)
# rm -rf /var/lib/apt/lists/* = clean up apt cache to save space
# The && chains commands so they run as ONE layer (saves space)

# ── Working directory ─────────────────────────────────
WORKDIR /app
# Everything from here runs in /app

# ── Install dependencies (cached layer) ───────────────
COPY requirements.txt .
# Only copy requirements.txt first — isolated layer

RUN pip install --no-cache-dir -r requirements.txt
# Install all Python packages
# --no-cache-dir keeps the image smaller

# ── Copy application code ─────────────────────────────
COPY . .
# Now copy everything else
# This layer rebuilds on every code change, which is fine
# because pip install (above) is already cached

# ── Environment variables with defaults ───────────────
ENV PYTHONUNBUFFERED=1
# PYTHONUNBUFFERED=1 = print() output appears immediately in logs
# Without this, Python buffers output and you see nothing in
# docker logs until the buffer fills up — very confusing for debugging

ENV PYTHONDONTWRITEBYTECODE=1
# Don't create .pyc compiled files inside the container
# Saves a tiny bit of space, keeps container filesystem cleaner

# ── Expose port ───────────────────────────────────────
EXPOSE 8000

# ── Start command ─────────────────────────────────────
CMD ["uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
# workers=1 for now — we'll scale in Docker Compose
# --host 0.0.0.0 = listen on ALL network interfaces
# Without this: only accessible from inside the container itself