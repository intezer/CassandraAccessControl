FROM python:3.8.12-slim-buster
RUN apt-get update && apt-get upgrade -y
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
