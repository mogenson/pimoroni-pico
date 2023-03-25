import time

try:
    import urequests as requests
except ImportError:
    import requests


import utelnetserver
import network
import machine
import re


# connect to wifi
nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect(.....................................................)
while not nic.isconnected():
    time.sleep(1)
print(nic.ifconfig()[0])

# set time and convert to local timezone
result = requests.get("http://worldtimeapi.org/api/timezone/America/New_York")
if result.status_code == 200:
    json = result.json()
    datetime = json.get("datetime")
    print(datetime)
    ISO8601 = re.compile("^(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)")
    regex = ISO8601.match(datetime)
    year, month, day, hour, minute, second = tuple(
        int(regex.group(i)) for i in range(1, 7)
    )
    weekday = int(json.get("day_of_week")) + 1  # RTC weekday is 1-7
    machine.RTC().datetime((year, month, day, weekday, hour, minute, second, 0))
result.close()

# start telnet server
utelnetserver.start()
