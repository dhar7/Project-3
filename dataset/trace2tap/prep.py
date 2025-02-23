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
        date_time = trace["timestamp"][:-6]
        if "." not in date_time:
            date_time += ".000000"
        sensor_id = f"{trace['device']}_{trace['device_id']}_{trace['cap_id']}"
        value = trace["value"]
        try:
            value = float(value)
        except:
            pass

        fstr = "%Y-%m-%d %H:%M:%S.%f"
        if not raw_sequence:
            base_time = datetime.strptime(date_time, fstr)
        raw_sequence.append(
            Event(
                int((datetime.strptime(date_time, fstr) - base_time).total_seconds()),
                sensor_id,
                value,
            )
        )

    return raw_sequence
