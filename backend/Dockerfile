# Backend Dockerfile.
#
# A Dockerfile is a recipe for building an image. The image is what gets
# run as a container. Each instruction creates a new layer; layers are
# cached, so reordering them affects build speed dramatically.
#
# Rule of thumb: put rarely-changing instructions first (system packages,
# requirements.txt) so they stay cached when only your source code changes.

# `slim` = small Debian-based Python image. Trade-off: smaller download
# but missing some build tools, which is why we apt-install them below.
FROM python:3.12-slim

# ENV for Python: don't write .pyc files (saves space, no use in containers)
# and don't buffer stdout (so logs show up immediately).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install OS-level deps needed to compile psycopg2. `--no-install-recommends`
# keeps the image small. The `rm -rf /var/lib/apt/lists/*` cleanup removes
# the apt cache from the layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY requirements.txt first, then install. This way `pip install`
# is cached unless requirements.txt actually changes — code edits don't
# trigger a slow reinstall.
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Now copy the rest of the source. Anything in .dockerignore is skipped.
COPY . .

EXPOSE 8000

# CMD is the default command when the container starts. Compose's bind-mount
# replaces /app with your local source so edits hot-reload — but you'd want
# `--reload` for true autoreload. Add it here in dev if desired.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
