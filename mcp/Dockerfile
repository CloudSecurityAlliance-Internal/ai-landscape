FROM node:22-alpine AS builder
WORKDIR /app
COPY mcp/package*.json ./
RUN npm ci
COPY mcp/src/ src/
COPY mcp/tsconfig.json ./
RUN npx tsc

FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/dist/ dist/
COPY --from=builder /app/node_modules/ node_modules/
COPY data/landscape.yaml data/landscape.yaml
ENV LANDSCAPE_YAML=/app/data/landscape.yaml
EXPOSE 3000
CMD ["node", "dist/server.js"]
