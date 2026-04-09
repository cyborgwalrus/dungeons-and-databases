FROM nginx:stable-alpine

WORKDIR /usr/share/nginx/html

# Copy all frontend files into nginx html directory
COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
