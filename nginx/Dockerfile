#we use Dockerfile to simply COPY instead of mounting
#use bookworm to have "openrc" package already installed, so we can use "service" command for healthcheck
    #alpine has roughly 13.61MB + 47MB (openrc)
    #bookworm has roughly 41.850MB
FROM nginx:bookworm

#name our files as "default" to replace files with "default" name, and prevent conflict from "*.conf" wildcard
#create /etc/nginx/templates/default.conf.template, throw everything in there
#create /etc/nginx/nginx.conf, put root-level configs in there
#let NGINX do envsubst to templates, which in this case, NGINX will create /etc/nginx/conf.d/default.conf
#do "include /etc/nginx/conf.d/*.conf;" at /etc/nginx/nginx.conf
#don't include entrypoint.sh nor CMD, so NGINX uses its own default command, which will also do envsubst

COPY ./default.conf.template /etc/nginx/templates/
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./50x.html /etc/nginx/html/
COPY ./favicon.svg /etc/nginx/

EXPOSE 8080

#no CMD, let NGINX use its own entrypoint