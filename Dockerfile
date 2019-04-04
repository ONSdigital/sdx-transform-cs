FROM onsdigital/flask-crypto-queue

RUN sed -i '/jessie-updates/d' /etc/apt/sources.list
RUN apt-get update && apt-get install -y poppler-utils

COPY server.py /app/server.py
COPY transform /app/transform
COPY startup.sh /app/startup.sh
COPY requirements.txt /app/requirements.txt
COPY Makefile /app/Makefile

RUN mkdir -p /app/tmp

# set working directory to /app/
WORKDIR /app/

RUN make build

EXPOSE 5000

ENTRYPOINT ./startup.sh
