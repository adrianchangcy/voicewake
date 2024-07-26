FROM postgres:latest

#test area
COPY ./test_service_entrypoint.sh /test_service_entrypoint.sh
ENTRYPOINT ./test_service_entrypoint.sh

EXPOSE 8888