from datetime import datetime
import csv
from ..common import Event

import os

path = os.path.dirname(os.path.realpath(__file__))


def check_balanced(str):
    balance = 0
    for c in str:
        if c == "[":
            balance += 1
        elif c == "]":
            balance -= 1
            if balance < 0:
                return False
    return balance == 0


def balance(src, i):
    j = 0
    str = src[i]
    while not check_balanced(str):
        j += 1
        str += src[i + j]
    return str, j


def read_file(filename):
    file = open(filename)
    reader = csv.reader(file)

    raw_traces = []
    for row in reader:
        raw_traces.append(row)
    file.close()

    raw_sequence = []

    traces = {}
    i = 0
    while len(traces.keys()) < len(raw_traces[2]):
        # Fix inconsistent commas that are in square brackets
        label, j = balance(raw_traces[0], i)
        traces[label] = list(map(lambda l: l[len(traces.keys())], raw_traces[1:]))
        i += j + 1

    # Use one time value as reference
    time_ref = traces["gtyp_Interface_Dashboard.Subscribe.PosPanTiltUnit.ldt_ts"][1:]
    fstr = "%Y-%m-%d %H:%M:%S.%f"

    if not raw_sequence:
        base_time = datetime.strptime(time_ref[0], fstr)

    for sensor_id, values in traces.items():
        if values[0] != "Float" and "Int" not in values[0] and values[0] != "Boolean":
            continue

        if (
            sensor_id
            == "gtyp_Interface_TXT_Controler.Subscribe.State_NFC_Device.History[19].i_code"
        ):
            continue

        for i, value in enumerate(values[1:]):
            if values[0] == "Float" or "Int" in values[0]:
                if sensor_id != "IW_SSC_ColorSensor_A1":
                    value = float(value)

            raw_sequence.append(
                Event(
                    (datetime.strptime(time_ref[i], fstr) - base_time).total_seconds(),
                    sensor_id,
                    value,
                )
            )

    return sorted(raw_sequence, key=lambda i: i.event_time)
