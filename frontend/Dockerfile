FROM nginxinc/nginx-unprivileged:1.29.8-alpine-perl

WORKDIR /usr/share/nginx/html

COPY . /usr/share/nginx/html

COPY nginx.conf.template /etc/nginx/templates/default.conf.template

USER root
COPY start-frontend.sh /app/start-frontend.sh
RUN chmod +x /app/start-frontend.sh
USER 101

EXPOSE 8080

CMD ["/app/start-frontend.sh"]
