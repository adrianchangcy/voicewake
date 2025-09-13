FROM python:bookworm

RUN pip install --upgrade pip

COPY ./requirements.txt ./

#don't store packages in cache, as there will not be reinstalls
#--verbose to track progress
#set "--default-timeout=100" to fix ReadTimeoutError
#to fix "DECRYPTION_FAILED_OR_BAD_RECORD_MAC", turn off and on your Airplane Mode to reset WiFi
RUN pip install -r requirements.txt --no-cache-dir --verbose --default-timeout=100

#source path is relative to docker-compose.yaml context path
COPY . .

ENTRYPOINT ["sh", "./voicewake/docker/entrypoint-django-runserver.sh"]

#set non-zero value so python's stdout and stderr streams are sent straight to terminal in real time
#can be useful for logging in case of crash
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

#having CMD here for django_runserver.py is unnecessary
    #using CMD '["python", "django_runserver.py"]' is just appended to ENTRYPOINT's commands as args, and is ignored