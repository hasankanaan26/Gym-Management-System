# Frontend Dockerfile (development).
#
# This image runs the Vite dev server, NOT a production build. That's
# convenient for local development (hot reload + helpful error messages)
# but ships way more JS than you'd want in production.
#
# A production-ready upgrade would be a multi-stage build:
#   1. `node:20-alpine AS builder`  — runs `npm run build`, produces /dist
#   2. `nginx:alpine`               — copies /dist into nginx's html dir
# This keeps the final image tiny (~30 MB) and serves static files fast.
# Adding it would be a great contribution. See CONTRIBUTING.md → "CI/CD".

FROM node:20-alpine

WORKDIR /app

# Copy package.json first — same caching trick as the backend Dockerfile.
# `npm install` only re-runs when dependencies actually change.
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

# Vite's dev server. The package.json `dev` script binds to 0.0.0.0 so the
# port is reachable from outside the container.
CMD ["npm", "run", "dev"]
