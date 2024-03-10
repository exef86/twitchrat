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

def get_events(influx:InfluxDBClient, influx_regex:str, intensity_min:int) -> list:
    query = f"""
    SELECT "intensity"
    FROM (
        SELECT count("message") AS "intensity"
        FROM "messages"
        WHERE "message"::field =~ {influx_regex} AND
              time >= now() - 1d
        GROUP BY time(15s)
    ) WHERE "intensity" > {intensity_min}
    """
    results = list(influx.query(query))
    # array of array
    try:
        return results[0]
    except IndexError:
        return []

def get_stream_for_event(influx:InfluxDBClient, streamer:str, event_dt: datetime) -> list:
    event_epoch_ns = event_dt.timestamp() * 1000000000
    event_epoch_ns = int(event_epoch_ns) # do not want Eulers number in format
    query = f"""
    SELECT "game_name", "started_at", "title", "viewer_count"
    FROM "streams"
    WHERE "streamer"::tag = '{streamer}' AND
          {event_epoch_ns} >= time
    ORDER BY time ASC
    LIMIT 1
    """
    results = list(influx.query(query))
    # array of array
    try:
        return results[0][0]
    except IndexError:
        return []

def get_vod_url(streamer:str, event_time:datetime) -> str:
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

    r = requests.get(f"https://api.twitch.tv/helix/videos?user_id={quin69_id}",
                     headers={"Authorization": f"Bearer {access_token}",
                              "Client-Id": client_id})
    found_vod = {}
    for vod in r.json()["data"]:
        vod_started = datetime.fromisoformat(vod["created_at"])
        duration_r = re.compile(r"(?P<hours>[0-9]+)h(?P<minutes>[0-9]+)m(?P<seconds>[0-9]+)s")
        match = duration_r.match(vod["duration"])
        if not match:
            duration_r = re.compile(r"(?P<minutes>[0-9]+)m(?P<seconds>[0-9]+)s")
            match = duration_r.match(vod["duration"])

        duration = match.groupdict()

        if "hours" not in duration:
            duration["hours"] = 0
        else:
            duration["hours"] = int(duration["hours"])

        duration["minutes"] = int(duration["minutes"])
        duration["seconds"] = int(duration["seconds"])
        delta = timedelta(hours=duration["hours"], minutes=duration["minutes"], seconds=duration["seconds"])
        vod_ended = vod_started + delta

        if vod_started <= event_time < vod_ended:
            marker = event_time - vod_started
            # Events grouped by 15s, subtract 15s for offset
            total_seconds = marker.total_seconds() - 15
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            vod_url = vod["url"]

            return f"{vod_url}?t={hours}h{minutes}m{seconds}s"


if __name__ == "__main__":
    influx = InfluxDBClient(host="influxdb.influxdb", port=8086, database="quin69chat")
    events = {
        "failure": get_events(influx, "/(?i)sobad|icant|deadge|lmao|believers|ez/", 40),
        "pog": get_events(influx, "/(?i)pog|pagchamp/", 40),
        "bruh": get_events(influx, "/(?i)bruh|last stream|vacation|victim|reported/", 40),
        "painchamp": get_events(influx, "/(?i)painchamp|despair/", 40),
        "lolw": get_events(influx, "/(?i)lolw/", 70),
        "2header": get_events(influx, "/2Header/", 40)
    }
    points = []
    for eventtype in events.keys():
        last_event_dt = None
        for event in events[eventtype]:
            print(f"IN FOR FOR {eventtype}")
            event_dt = datetime.fromisoformat(event["time"])

            # Get stream information for event
            stream = get_stream_for_event(influx=influx, streamer="quin69", event_dt=event_dt)

            difference = 0
            if last_event_dt is not None:
                difference = (event_dt - last_event_dt).total_seconds()
                if difference < 60:
                    print(f"Too close: {difference}s")
                    continue
            last_event_dt = event_dt

            print(f"Far enough apart: {difference}s")

            print(f"Getting VOD URL for {eventtype} at {event['time']}")

            url = get_vod_url("quin69", event_dt)
            point = {
                "measurement": "events",
                "tags": {
                    "type": eventtype
                },
                "fields": {
                    "vod_url": url,
                    "level" : int(event["intensity"])
                },
                "time": event_dt
            }
            if stream:
                point["tags"]["category"] = stream["game_name"]
                point["fields"]["title"] = stream["title"]
                # TODO: Scale "intensity" level off of stream["viewer_count"]

            points.append(point)

    pprint(points)
    influx.write_points(points)
