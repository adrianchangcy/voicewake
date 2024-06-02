#notes
#is COPY needed because the container is empty to begin with?

FROM python:3.12-slim-bullseye

RUN pip install --upgrade pip

#destination is "./" so that we guarantee it is added under "/"
COPY ./requirements.txt ./
RUN pip install -r requirements.txt

#source path is relative to docker-compose.yaml context path
COPY . .

ENTRYPOINT ["sh", "/docker-entrypoint.sh"]

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# activate virtual environment
ENV VIRTUAL_ENV=/.venv
ENV PATH="/.venv/bin:$PATH"

EXPOSE 5000

# /dev/shm is mapped to shared memory and should be used for gunicorn heartbeat
# this will improve performance and avoid random freezes
CMD ["gunicorn","-b", "0.0.0.0:5000", "-w", "4", "-k", "gevent", "--worker-tmp-dir", "/dev/shm", "app:app"]
