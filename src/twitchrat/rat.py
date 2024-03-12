#!/usr/local/bin/python3

# core
from datetime import datetime
import argparse
import logging
import time

# local
from twitchrat.chatevents import vod_url_get, chat_events_get
from twitchrat.chatmessages import get_chat_messages_points
from twitchrat.ratlogging import get_logger
from twitchrat.stream import stream_point_get, stream_for_event_get
from twitchrat.twitch import Twitch

# 3rd party
from influxdb import InfluxDBClient

def main():
    parser = argparse.ArgumentParser(description="Get stream information and store in InfluxDB")
    parser.add_argument("--debug", "-d", dest="loglevel", action="store_const",
                        const=logging.DEBUG, default=logging.INFO,
                        help="Enable deboug output")
    parser.add_argument("--streamer", "-s",    type=str, required=True,               help="Name of streamer to get stream for")
    parser.add_argument("--influxdb-database", type=str, required=True,               help="Name of InfluxDB database")
    parser.add_argument("--influxdb-host",     type=str, default="influxdb.influxdb", help="Hostname of InfluxDB service")
    parser.add_argument("--influxdb-port",     type=int, default=8086,                help="Port of InfluxDB service")
    args = parser.parse_args()
    streamer = args.streamer
    influxdb_host = args.influxdb_host
    influxdb_port = args.influxdb_port
    influxdb_database = args.influxdb_database

    logger = get_logger(name="twitchrat", level=args.loglevel)

    loop_interval = 300
    while 1:
        influx = InfluxDBClient(host=influxdb_host, port=influxdb_port, database=influxdb_database)
        twitch = Twitch()

        # Get all chat messages from the channel for the day
        message_points = get_chat_messages_points(streamer)
        number_of_messages = len(message_points)
        logger.info(f"Writing {number_of_messages} message points to InfluxDB")
        influx.write_points(message_points, batch_size=5000)
        logger.info(f"Done writing {number_of_messages} message points to InfluxDB")

        # Get current stream infromation and store it
        stream = stream_point_get(streamer, twitch)
        if stream:
            logger.info("Writing stream point")
            influx.write_points([stream])
            logger.info("Done writing stream point")

        # Get vods, used further down
        vods = twitch.vods_get(streamer)

        logger.info("Getting events...")
        # Gets number of chat messages within a certain period of time
        # which matches the regex and has >= number of them (ie. 40)
        events = {
            "failure": chat_events_get(influx, "/(?i)sobad|icant|deadge|lmao|believers|ez/", 40),
            "pog": chat_events_get(influx, "/(?i)pog|pagchamp/", 40),
            "bruh": chat_events_get(influx, "/(?i)bruh|last stream|vacation|victim|reported/", 40),
            "painchamp": chat_events_get(influx, "/(?i)painchamp|despair/", 40),
            "lolw": chat_events_get(influx, "/(?i)lolw/", 70),
            "2header": chat_events_get(influx, "/2Header/", 40)
        }
        points = []
        # Process all events, find associated vod at timestamp, along with category and title of stream
        # around that same time.
        for eventtype in events.keys():
            last_event_dt = None
            num_events = len(events[eventtype])
            logger.info(f"Processing {num_events} events.")
            for event in events[eventtype]:
                event_dt = datetime.fromisoformat(event["time"])
                stream = stream_for_event_get(influx, streamer, event_dt)

                difference = 0
                if last_event_dt:
                    difference = (event_dt - last_event_dt).total_seconds()
                    if difference < 60:
                        logger.info("Skipping event, too close to prevoius event.")
                        continue
                last_event_dt = event_dt

                url = vod_url_get(streamer, event_dt, vods)
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
                logger.info("Valid event, adding to points.")
                points.append(point)

        logger.info(f"Sleeping for {loop_interval} seconds")
        time.sleep(loop_interval)

if __name__ == "__main__":
    main()

