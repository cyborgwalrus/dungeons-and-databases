FROM nginxinc/nginx-unprivileged:1.29.8-alpine-perl

WORKDIR /usr/share/nginx/html

COPY . /usr/share/nginx/html

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY start-frontend.sh /start-frontend.sh

RUN chmod +x /start-frontend.sh

USER root

EXPOSE 8080

CMD ["/start-frontend.sh"]
