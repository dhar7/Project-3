import json
import sys
from datetime import datetime

f = open(sys.argv[1])
traces = json.load(f)
f.close()

dd = {}
for trace in traces:
    if trace["time"].split()[0] not in dd.keys():
        dd[trace["time"].split()[0]] = []
    dd[trace["time"].split()[0]].append(trace)

for date, l in dd.items():
    try:
        f = open(date + ".json", "x")
        json.dump(l, f, indent=4)
    except:
        f = open(date + ".json", "r")
        t = json.load(f)
        f.close()
        f = open(date + ".json", "w")
        new_l = t + l
        new_l.sort(key=lambda ll: datetime.strptime(ll["time"], "%Y-%m-%d %H:%M:%S"))
        json.dump(new_l, f, indent=4)
    f.close()
