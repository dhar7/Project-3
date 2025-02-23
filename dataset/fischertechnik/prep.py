import csv
from datetime import datetime
from ..common import Event
import os

path = os.path.dirname(os.path.realpath(__file__))


def typecast(str):
    try:
        val = float(str)
    except:
        val = str.replace(":", ";")
    return val


def read_file(filename):
    file = open(filename)
    reader = csv.DictReader(file)
    traces = [row for row in reader]
    file.close()

    # Use one time value as reference
    time_event = "LogTime"
    time_ref = traces[0][time_event]
    while not time_ref:
        traces = traces[1:]
        time_ref = traces[0][time_event]

    fstr = "%H:%M:%S"
    base_time = datetime.strptime(time_ref, fstr)

    exclude_list = ["ldt_ts", "s_id", "i_code", "LogTime", "SSC", "Publish", "Label"]

    raw_sequence = []
    for row in traces:
        for sensor_id, value in row.items():
            for item in exclude_list:
                if item in sensor_id:
                    value = None
                    break

            if not value:
                continue

            sensor_id.replace(":", ";")

            time_ref = row[time_event]
            if not time_ref:
                continue
            curr_time = datetime.strptime(time_ref, fstr)
            raw_sequence.append(
                Event(
                    (curr_time - base_time).total_seconds(),
                    sensor_id,
                    typecast(value),
                )
            )

    return sorted(raw_sequence, key=lambda i: i.event_time)
