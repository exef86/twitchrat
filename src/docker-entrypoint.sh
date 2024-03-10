#!/bin/bash

while [ 1 ]
do
    events/get-chat-logs.py
    events/process-stream.py
    events/process-events.py
    sleep 300
done

