FROM node:22-bookworm-slim

WORKDIR /app

COPY front/package.json front/package-lock.json /app/
RUN npm ci

COPY front/ /app/
