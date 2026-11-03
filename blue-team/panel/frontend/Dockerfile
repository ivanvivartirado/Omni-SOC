FROM node:20-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
RUN apk add --no-cache openssl
COPY --from=build /src/dist /usr/share/nginx/html
COPY nginx/ /etc/nginx/templates-omni/
COPY nginx/entrypoint.sh /docker-entrypoint.d/05-omni-certs.sh
RUN chmod +x /docker-entrypoint.d/05-omni-certs.sh \
 && cp /etc/nginx/templates-omni/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 8443
