# core
from datetime import datetime, timedelta
import re

# local

# 3rd party
from influxdb import InfluxDBClient

def chat_events_get(influx:InfluxDBClient, influx_regex:str, intensity_min:int) -> list:
    query = f"""
    SELECT "intensity"
    FROM (
        SELECT count("message") AS "intensity"
        FROM "messages"
        WHERE "message"::field =~ {influx_regex} AND
              time >= now() - 30d
        GROUP BY time(15s)
    ) WHERE "intensity" > {intensity_min}
    """
    results = list(influx.query(query))
    # array of array
    try:
        return results[0]
    except IndexError:
        return []

def vod_url_get(streamer: str, event_time:datetime, vods:list) -> str:
    for vod in vods:
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

