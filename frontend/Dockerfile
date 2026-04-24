FROM nginxinc/nginx-unprivileged:1.29.8-alpine-perl

WORKDIR /usr/share/nginx/html

COPY . /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
