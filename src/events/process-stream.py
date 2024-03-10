#!/usr/local/bin/python3

# core
from pprint import pprint
from datetime import datetime, timedelta
import json
import os
import re

# 3rd party
from influxdb import InfluxDBClient
import requests

def get_streamer_category(streamer:str) -> str:
    client_id = os.environ.get("CLIENT_ID")

    data = {
        "client_id": client_id,
        "client_secret": os.environ.get("CLIENT_SECRET"),
        "grant_type": "client_credentials"
    }
    r = requests.post("https://id.twitch.tv/oauth2/token", data=data)
    access_token = r.json()["access_token"]

    r = requests.get("https://api.twitch.tv/helix/users?login=quin69",
                     headers={"Authorization": f"Bearer {access_token}",
                              "Client-Id": client_id})
    quin69_id = r.json()["data"][0]["id"]

    r = requests.get(f"https://api.twitch.tv/helix/streams?user_id={quin69_id}",
                     headers={"Authorization": f"Bearer {access_token}",
                              "Client-Id": client_id})
    json = r.json()
    if "data" in json:
        if len(json['data']):
            return json['data'][0]
    return None

if __name__ == "__main__":
    stream = get_streamer_category(streamer="quin69")
    if stream:
        influx = InfluxDBClient(host="influxdb.influxdb", port=8086, database="quin69chat")
        point = {
           "measurement": "streams",
           "tags": {
               "game_name": stream['game_name'],
               "streamer": "quin69",
           },
           "fields": {
               "title": stream["title"],
               "viewer_count": stream['viewer_count'],
               "started_at": stream['started_at'],
           },
        }
        pprint(point)
        influx.write_points([point])

