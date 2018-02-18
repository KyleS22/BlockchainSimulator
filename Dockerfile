FROM python:3-alpine3.7

RUN mkdir /blobchain
WORKDIR /blobchain

ADD *.py ./
ADD protos/*.py ./blobchain/
ADD requirements.txt ./

RUN pip install -r ./requirements.txt

ENTRYPOINT python ./