import sys
import argparse
from ctypes import *


class event(Structure):
    _fields_ = [("event", c_char_p),
                ("event_time", c_float)]


def new_event(eventname, time):
    e = event()
    c_eventname = create_string_buffer(bytes(eventname, encoding="utf-8"))
    e.event = cast(c_eventname, c_char_p)
    e.event_time = float(time)
    return e


def run_checker(traces, ta_path):
    c_arr_tlist = cast((event * len(traces))(), POINTER(event))
    for i in range(len(traces)):
        c_arr_tlist[i] = traces[i]
    lib.offline_checker(ta_path, c_arr_tlist, c_int(len(t)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ta", nargs="*", required=True)
    parser.add_argument("--traces", required=True)
    parser.add_argument("--libpath", required=True)
    args = parser.parse_args()

    lib = cdll.LoadLibrary(args.libpath)
    lib.offline_checker.argtypes = [c_char_p, POINTER(event), c_int]

    ta_path = str(args.ta[0])
    f = open(args.traces)
    trace_list = []
    for l in f.readlines():
        trace_list.append(
            list(map(lambda i: new_event(i.split(":")[0], i.split(":")[1]), l[:-1].split())))
    f.close()

    c_ta_path = cast(create_string_buffer(
        bytes(ta_path, encoding="utf-8")), c_char_p)

    for ti, t in enumerate(trace_list):
        print(f"-------------------- Testing trace {ti} --------------------")
        print(f"Num of events: {len(t)}")
        sys.stdout.flush()
        run_checker(t, c_ta_path)
