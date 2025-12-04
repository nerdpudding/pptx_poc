# Frontend Service - Nginx Static File Server
# Builds nginx:alpine image to serve static HTML/CSS/JS files

FROM nginx:alpine

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/

# Copy static files
COPY static/ /usr/share/nginx/html/

# Expose HTTP port
EXPOSE 80

# Health check (using wget since curl is not available in alpine)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 -O /dev/null http://127.0.0.1:80/health || exit 1

# Command to run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]