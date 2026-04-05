#for dev, see ./nginx/readme to create SSL for HTTPS with Vite
#for prod, see ./nginx/readme on how to use cloudflare/others for prod nginx SSL
FROM nginx:bookworm

#name our files as "default" to replace files with "default" name, and prevent conflict from "*.conf" wildcard
#create /etc/nginx/templates/default.conf.template, throw everything in there
#create /etc/nginx/nginx.conf, put root-level configs in there
#NGINX entrypoint will do envsubst with /etc/nginx/templates/default.conf.template to create /etc/nginx/conf.d/default.conf
#do "include /etc/nginx/conf.d/*.conf;" at /etc/nginx/nginx.conf
#don't include entrypoint.sh nor CMD, since NGINX's own entrypoint is quite complex, or you can find it at github and modify it
COPY ./nginx/default.conf.template /etc/nginx/templates/
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./nginx/50x.html /etc/nginx/html/

EXPOSE 8080

#to verify that nginx container's built-in envsubst is successful via compose's env_file on default.conf.template:
    #cat /etc/nginx/conf.d/default.conf

#for normal NGINX, skip CMD, let NGINX use its own entrypoint
#for debug, use CMD below, and specify "...error.log debug;" at nginx.conf
# CMD ["nginx-debug", "-g", "daemon off;"]

#if using command at docker compose:
    #command: nginx-debug -g 'daemon off;'

#on file change, manually reload at container's exec bash (no straightforward hot reload available):
    #nginx -s reload

#to tail logs, enter nginx container and use "tail":
    #sudo docker exec -it vw-nginx-1 bash
    #sudo tail -f /var/log/nginx/*.log