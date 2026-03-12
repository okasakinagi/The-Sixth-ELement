FROM node:20.19.0-slim AS build
WORKDIR /app

# 复制 package.json 以利用缓存
COPY frontend/sixth_element/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci

# 复制源代码并构建
COPY frontend/sixth_element/ /app/frontend/
RUN npm run build

FROM nginx:stable-alpine
# 将构建产物放到 nginx 的默认静态目录
COPY --from=build /app/frontend/dist /usr/share/nginx/html
# 复制自定义 nginx 配置，代理 /api 到 web:8000
COPY docker/nginx_frontend.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
