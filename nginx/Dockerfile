#ssl
    #prerequisite
        #ensure your dev machine is using static IP, configured at WiFi
        #declare NGINX_SSL_FILE_NAME at .env and default.conf.template
        #bind mount .crt and .key at dev and prod compose.yaml
    #command to ensure copying to host machine works (COPY --from alone does not copy to host)
        #docker build --file ./nginx/Dockerfile --no-cache --target=export-ssl-stage . --build-arg DOCKER_BUILDKIT=1 --build-arg NGINX_DEV_MACHINE_STATIC_LAN_IP=192.168.1.200
            #the "." is WORKDIR, i.e. root of this project
            #needs DOCKER_BUILDKIT=1 to enable multistage
            #NGINX_DEV_MACHINE_STATIC_LAN_IP is so you can test via HTTPS in LAN from different device
FROM alpine:latest AS create-ssl-stage

RUN apk update && apk add openssl

#only for dev
#for live + cloudflare, get from cloudflare > SSL/TLS > origin server > create certificate > create your own .crt .key and paste in > paste files to S3
RUN openssl req -newkey rsa:4096 \
    -x509 \
    -sha256 \
    -days 3650 \
    -nodes \
    -out "dev-nginx-ssl.crt" \
    -keyout "dev-nginx-ssl.key" \
    -subj "/C=MY/ST=Sarawak/L=Kuching/O=Security/OU=ITDepartment/CN=${NGINX_DEV_MACHINE_STATIC_LAN_IP}"
    #-newkey, rsa2048 is recommended to be ok until the year 2030, and should upgrade
    #-x509, is type of cert
    #-days, can use any positive integer, 36500 is 10 years
    #-nodes, creates key without passphrase
    #-out, specify any filename for created .crt
    #-keyout, specify any filename for created .key
    #-subj
        #C=, two-letter ISO abbreviation
        #ST=, state/province
        #L=, city
        #O=, name of organisation
        #OU=, organisational unit
        #CN=, full domain, can use wildcard if placed at leftmost but only once
            #e.g. "*.example.com" is valid, will also cover "xx.yy.example.com", while "*.*.example.com" is invalid



FROM scratch AS export-ssl-stage

COPY --from=create-ssl-stage /dev-nginx-ssl.crt ./nginx/
COPY --from=create-ssl-stage /dev-nginx-ssl.key ./nginx/



#with multistage via DOCKER_BUILDKIT=1, multiple "FROM" are allowed
    #but for final container, it will use the final "FORM"
#we use Dockerfile to simply COPY instead of mounting
#use bookworm to have "openrc" package already installed, so we can use "service" command for healthcheck
    #alpine has roughly 13.61MB + 47MB (openrc)
    #bookworm has roughly 41.850MB
FROM nginx:bookworm AS final-stage

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