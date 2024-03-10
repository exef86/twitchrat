FROM python:3.12.2-bookworm

RUN mkdir /app

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY src/ /app

ENTRYPOINT [ "./docker-entrypoint.sh" ]
