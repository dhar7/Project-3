import json
from datetime import datetime
from ..common import Event
import os

path = os.path.dirname(os.path.realpath(__file__))


def read_file(filename):
    f = open(filename)
    traces = json.load(f)
    f.close()

    raw_sequence = []

    for trace in traces:
        date_time = trace["time"]
        sensor_id = "_".join((trace["device_name"] + " " + trace["attribute"]).split())
        value = "_".join(trace["current_value"].split())
        try:
            value = float(value)
        except:
            pass

        fstr = "%Y-%m-%d %H:%M:%S"
        if not raw_sequence:
            base_time = datetime.strptime(date_time, fstr)
        raw_sequence.append(
            Event(
                (datetime.strptime(date_time, fstr) - base_time).total_seconds(),
                sensor_id,
                value,
            )
        )

    return sorted(raw_sequence, key=lambda i: i.event_time)
