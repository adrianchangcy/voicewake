FROM python:bookworm

COPY ./requirements.txt ./

#keep container alive
CMD ["sh", "-c", "echo 'Container is running...'; sleep infinity"]

#commands to run:
#pip install pip-check-updates
#pcu
#pcu -u


#==================================================================================
#commands part 1, in container:
    #pip install npm-check-updates
    #pcu
    #pcu -u
    #pip install -r requirements.txt --dry-run --verbose
    #pip install -r requirements.txt --verbose

#commands part 2, at host machine project root, cmd:
    #docker cp vw_dev-update_pip-1:/requirements.txt ./requirements.txt

#commands part 3, at your individual containers' .dockerfile:
    #RUN pip install -r requirements.txt --no-cache-dir --verbose --default-timeout=100
#==================================================================================