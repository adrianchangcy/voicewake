#alpine is too slim, and had caused "could not build wheels" error
#there is also the opinion where upon using alpine, after a few installs for missing packages/wheels, it gets a lot bigger than other images
FROM python:bookworm

RUN pip install --upgrade pip

#destination is "./" so that we guarantee it is added under "/"
#for deployment, do not use cache to save storage space, since no one else will install the same packages
    #this fixes exit code 137 caused by out of RAM
#set "--default-timeout=100" to fix ReadTimeoutError
COPY ./requirements.txt ./

#for Linux, these packages are from packages installed on Windows, and are useless:
    #pywin32
    #twisted-iocpsupport
#using sed to remove from requirements.txt did not work, as Docker still uses the file before sed
#solution is to uninstall pywin32 from PC, freeze into requirements.txt again, and only run Python via container
# RUN sed --in-place '/pywin32/d' ./requirements.txt

#don't store packages in cache, as there will not be "reinstalls" in the container
#--verbose to track progress
#set "--default-timeout=100" to fix ReadTimeoutError
RUN pip install -r requirements.txt --no-cache-dir --verbose --default-timeout=100

#source path is relative to docker-compose.yaml context path
COPY . .

# ENTRYPOINT ["sh", "/docker-entrypoint.sh"]

#set non-zero value so python's stdout and stderr streams are sent straight to terminal in real time
#can be useful for logging in case of crash
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

#fix attempt for NewConnectionError during pip install
    #failed solution #1
        #Windows --> settings --> Network & Internet --> Proxy --> Automatically detect settings --> Off
    #failed solution #2
        #networks:
            #-host
        #networks:
            #host:
                #external: true
    #failed solution #3
        #'network_mode:"host"' and python:3.12-alpine instead of python:3.12-slim-bullseye
    #not sure if this helped
        #use 1.1.1.1 and 1.0.0.1 DNS at Docker-->settings-->DockerEngine-->config
    #may have helped
        #--default-timeout=100
        #python:3.12-bullseye
    #discouraged to edit ./etc/resolv.conf

ENTRYPOINT ["sh", "./voicewake/docker/entrypoint-gunicorn.sh"]