FROM python:3.5

RUN apt-get update && apt-get install -y poppler-utils

COPY requirements.txt /app/requirements.txt

COPY server.py /app/server.py
COPY transform /app/transform
COPY startup.sh /app/startup.sh

RUN mkdir -p /app/tmp
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -yq git gcc make build-essential python3-dev python3-reportlab
RUN git clone https://github.com/ONSdigital/sdx-common.git
RUN pip3 install ./sdx-common

# set working directory to /app/
WORKDIR /app/

EXPOSE 5000

RUN pip3 install --no-cache-dir -U -r /app/requirements.txt

ENTRYPOINT ./startup.sh
