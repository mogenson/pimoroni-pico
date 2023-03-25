try:
    import urequests as requests
except ImportError:
    import requests

try:
    from micropython import const
except ImportError:
    const = lambda x: x

import re
import machine
import time

from galactic import GalacticUnicorn

graphics = None
white = None
black = None
yellow = None
cyan = None

rtc = machine.RTC()

URL = const("https://api-v3.mbta.com/predictions?filter[stop]={}&filter[route]={}")
ISO8601 = re.compile("^(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)")


def seconds_since_midnight(hour, minute, seconds):
    return (hour * 3600) + (minute * 60) + seconds


def timenow():
    datetime = rtc.datetime()
    return seconds_since_midnight(datetime[4], datetime[5], datetime[6])


class MBTA:
    def __init__(self, route: str, stop: str | int):
        self.route = route
        self.stop = stop
        self.arrival_times: list[int] = []
        self.update_time: int = timenow()

    def get_arrival_times(
        self,
    ) -> list[(int, int, int)]:  # list of hour, minute, seconds since midnight
        now = timenow()
        if now < self.update_time:
            return self.arrival_times, False  # cached results

        self.arrival_times = []
        res = requests.get(URL.format(self.stop, self.route))
        if res.status_code != 200:
            res.close()
            return self.arrival_times, False

        for data in res.json().get("data"):
            datetime = data.get("attributes").get("arrival_time")
            regex = ISO8601.match(datetime)
            hour = int(regex.group(4))
            minute = int(regex.group(5))
            seconds = seconds_since_midnight(hour, minute, int(regex.group(6)))
            self.arrival_times.append((hour, minute, seconds))

        res.close()
        if len(self.arrival_times):
            # update again halfway to the first arrive time, or 1 minute in the future
            self.update_time = now + max((self.arrival_times[0][2] - now) // 2, 60)

        return self.arrival_times, True  # fresh results


teele_sq_stop = const(2576)
bus_87 = MBTA("87", teele_sq_stop)
bus_88 = MBTA("88", teele_sq_stop)
previous = 0


def init():
    global white, black, yellow, cyan
    white = graphics.create_pen_hsv(0.0, 0.0, 1.0)  # create_pen(155, 155, 155)
    black = graphics.create_pen_hsv(0.0, 0.0, 0.0)
    yellow = graphics.create_pen_hsv(60 / 360, 1.0, 1.0)
    cyan = graphics.create_pen_hsv(180 / 360, 1.0, 1.0)
    graphics.set_font("bitmap6")
    graphics.set_pen(black)
    graphics.clear()


def draw():
    global previous
    global graphics
    now = timenow()
    if now > 80000:
        # after about 11 pm, sleep for about 2 hours and reset
        time.sleep(20000)
        now = timenow()
        previous = now
        bus_87.update_time = now
        bus_88.update_time = now
        return
    if now > previous:
        previous = now

        graphics.set_pen(black)
        graphics.clear()

        times, fresh = bus_87.get_arrival_times()
        y = -1
        x = 13
        wrap = -1
        scale = 1
        for t in times:
            hour = t[0]
            minute = t[1]
            seconds = t[2]
            delta = (seconds - now) // 60
            if delta <= 0:
                continue
            print(f"87 bus {hour}:{minute} in {delta} min")
            graphics.set_pen(yellow)
            graphics.text("87", 0, y, wrap, scale)
            graphics.set_pen(white)
            graphics.text(f"{hour}:{minute:02}", x, y, wrap, scale)
            graphics.set_pen(cyan)
            delta_text = f"{delta}m"
            width = graphics.measure_text(delta_text, scale)
            graphics.text(delta_text, 54 - width, y, wrap, scale)
            break

        times, fresh = bus_88.get_arrival_times()
        y = 5
        for t in times:
            hour = t[0]
            minute = t[1]
            seconds = t[2]
            delta = (seconds - now) // 60
            if delta <= 0:
                continue
            print(f"88 bus {hour}:{minute} in {delta} min")
            graphics.set_pen(yellow)
            graphics.text("88", 0, y, wrap, scale)
            graphics.set_pen(white)
            graphics.text(f"{hour}:{minute:02}", x, y, wrap, scale)
            graphics.set_pen(cyan)
            delta_text = f"{delta}m"
            width = graphics.measure_text(delta_text, scale)
            graphics.text(delta_text, 54 - width, y, wrap, scale)
            break
