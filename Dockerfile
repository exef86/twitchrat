FROM python:3.12.2-bookworm

RUN mkdir /app

WORKDIR /app

ENV PYTHONPATH="/app"

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

COPY src/ /app

ENTRYPOINT [ "twitchrat/rat.py" ]
