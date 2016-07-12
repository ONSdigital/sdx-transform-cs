#!/bin/bash

if [ -z ${PORT+x} ]; 
then 
    export PORT=5000; 
fi

if [ "$SDX_DEV_MODE" = true ]
then
    python3 server.py
else
    gunicorn -b 0.0.0.0:$PORT server:app
fi