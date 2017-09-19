FROM onsdigital/flask-crypto-queue

RUN apt-get update && apt-get install -y poppler-utils

COPY server.py /app/server.py
COPY transform /app/transform
COPY startup.sh /app/startup.sh
COPY requirements.txt /app/requirements.txt
COPY Makefile /app/Makefile

RUN mkdir -p /app/tmp
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -yq git gcc make build-essential python3-dev python3-reportlab

# set working directory to /app/
WORKDIR /app/

RUN apt-get install build-essential libssl-dev libffi-dev -y
RUN make build

EXPOSE 5000

ENTRYPOINT ./startup.sh
