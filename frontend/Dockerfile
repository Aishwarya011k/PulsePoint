### Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
COPY frontend/package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY frontend/ ./
ARG VITE_API_BASE_URL=http://backend-api:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

### Production stage
FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -f http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
