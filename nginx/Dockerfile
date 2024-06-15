FROM nginx:1.25.5-alpine

#should COPY to "/etc/nginx/conf.d/nginx.conf", i.e. container's config, but cannot put worker_processes there
#put at "/etc/nginx/nginx.conf"
#in container, "/etc/nginx/nginx.conf" has "include /etc/nginx/conf.d/*.conf;"
#ensure it does not exist in our own nginx.conf

#we use default.conf.template because it envsubst will replace default.conf at /conf.d/, which already exists
#our /etc/nginx/nginx.conf has wildcard *.conf
#having both our own .conf and the original default.conf will raise error, since the original has server{} too
COPY ./default.conf.template /etc/nginx/templates/
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./50x.html /etc/nginx/html/
COPY ./favicon.svg /etc/nginx/

EXPOSE 8080

#no CMD, let NGINX use its own entrypoint