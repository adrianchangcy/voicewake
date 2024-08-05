FROM redis:latest

#test area
COPY ./test_service_entrypoint.sh /test_service_entrypoint.sh
ENTRYPOINT ["sh", "/test_service_entrypoint.sh"]

EXPOSE 5000