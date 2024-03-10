#!/usr/local/bin/python3
import datetime
import requests
import re
import statistics
from influxdb import InfluxDBClient

influx = InfluxDBClient(host="influxdb.influxdb", port=8086, database='quin69chat')

#r = requests.get(url='https://logs.ivr.fi/channel/quin69', data={"from": "2024-02-01 00:00:00", "to": "2024-0201 23:59:59"})
r = requests.get(url='https://logs.ivr.fi/channel/quin69')
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
        d = datetime.datetime(int(groups['year']), int(groups['month']), int(groups['day']), int(groups['hour']), int(groups['minute']), int(groups['second']))
        epoch_ns = int(d.timestamp()) * 1000000000

        point = {
            'measurement': 'messages',
            'tags': {
                'username': groups['username']
            },
            'fields': {
                'message': groups['message']
            },
            'time': epoch_ns
        }
        points.append(point)
count = len(points)
print(f"Writing {count} points")
influx.write_points(points, batch_size=5000)

