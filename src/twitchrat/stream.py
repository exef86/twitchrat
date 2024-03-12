# core
from datetime import datetime

# local
from twitchrat.twitch import Twitch

# 3rd party
from influxdb import InfluxDBClient

def stream_point_get(streamer:str, twitch:Twitch) -> list:
    stream = twitch.stream_get(streamer)
    if stream:
        return {
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

def stream_for_event_get(influx:InfluxDBClient, streamer:str, event_dt: datetime) -> list:
    event_epoch_ns = event_dt.timestamp() * 1000000000
    event_epoch_ns = int(event_epoch_ns) # do not want Eulers number in format
    query = f"""
    SELECT "game_name", "started_at", "title", "viewer_count"
    FROM "streams"
    WHERE "streamer"::tag = '{streamer}' AND
          time <= {event_epoch_ns}
    ORDER BY time DESC
    LIMIT 1
    """
    results = list(influx.query(query))
    # array of array
    try:
        return results[0][0]
    except IndexError:
        return []

