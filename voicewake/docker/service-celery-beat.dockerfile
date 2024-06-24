FROM python:3.12-bullseye

RUN pip install --upgrade pip

# activate virtual environment
ENV VIRTUAL_ENV=/.venv
ENV PATH="/.venv/bin:$PATH"

COPY ./requirements.txt ./

#don't store packages in cache, as there will not be reinstalls
#--verbose to track progress
#set "--default-timeout=100" to fix ReadTimeoutError
RUN pip install -r requirements.txt --no-cache-dir --verbose --default-timeout=100

#source path is relative to docker-compose.yaml context path
COPY . .

# ENTRYPOINT ["sh", "/docker-entrypoint.sh"]

#set non-zero value so python's stdout and stderr streams are sent straight to terminal in real time
#can be useful for logging in case of crash
ENV PYTHONUNBUFFERED=1

EXPOSE 8002

ENTRYPOINT ["sh", "./voicewake/docker/entrypoint-celery-beat.sh"]