FROM python:3.12-alpine

#test area
COPY ./test_requirements.txt ./

RUN sed --in-place '/pywin32/d' ./test_requirements.txt

#needs CMD, else container wouldn't run
CMD ["sleep", "3600"]