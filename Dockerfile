FROM python:3-alpine3.7

RUN mkdir /blobchain
WORKDIR /blobchain

ADD *.py ./
ADD protos/*.py ./protos/
ADD requirements.txt ./

RUN pip install -r ./requirements.txt

EXPOSE 9999
EXPOSE 10000

ENTRYPOINT python ./