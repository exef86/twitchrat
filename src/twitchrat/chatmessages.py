# core
import datetime
import re

# local
from twitchrat.globals import logs_ivr_base_url

# 3rd party
import requests

def get_chat_messages_points(streamer:str) -> list:
    r = requests.get(url=f"{logs_ivr_base_url}/channel/{streamer}")
    lines = r.text.split('\n')
    i=0

    pattern = re.compile(r'^\[(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2}) (?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})] #quin69 (?P<username>\w+): (?P<message>.*)')
    data = []
    i = 0
    points = []
    for line in lines:
        m = pattern.match(line)
        if (m):
            data.append(m.groupdict())
            line = line.rstrip()

            groups = m.groupdict()
            dt = datetime.datetime(int(groups['year']), int(groups['month']), int(groups['day']), int(groups['hour']), int(groups['minute']), int(groups['second']))

            point = {
                'measurement': 'messages',
                'tags': {
                    'username': groups['username']
                },
                'fields': {
                    'message': groups['message']
                },
                'time': dt,
            }
            points.append(point)

    return points

