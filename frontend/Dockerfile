FROM node:22-alpine

WORKDIR /srv
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Rewrites are resolved at build time, so the proxy target must be set here.
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
