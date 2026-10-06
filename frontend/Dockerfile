# ==============================================================================
# Multi-stage Frontend Production Dockerfile
# Stage 1: Build TypeScript + React assets with Node 20 LTS
# Stage 2: Serve optimized static assets with hardened Nginx Alpine
# ==============================================================================

# Build Stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency specifications first for Docker layer caching
COPY package*.json ./
RUN npm ci

# Copy frontend source code and compile production bundles
COPY . .
RUN npm run build

# Production Runtime Stage
FROM nginx:alpine

# Remove default Nginx welcome assets and copy compiled React application
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SPA routing and API reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose web server port
EXPOSE 80

# Container healthcheck using lightweight wget on container IPv4 loopback
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
