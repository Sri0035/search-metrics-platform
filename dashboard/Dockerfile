FROM node:20-alpine AS build

WORKDIR /app
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm install

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY dashboard/ .
RUN npm run build

FROM nginx:1.25-alpine
COPY dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
