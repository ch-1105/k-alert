# Stage 1: Build the Vue application
FROM node:18-slim AS build-stage

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Expose the dist folder via a volume
# We use a slim image just to hold the built files
FROM alpine:latest

WORKDIR /app

# Copy the built files from the build stage
COPY --from=build-stage /app/dist /app/dist

# The volume will be used by the external Nginx container
VOLUME /app/dist
