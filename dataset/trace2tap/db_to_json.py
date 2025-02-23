import psycopg2
import json
import copy

conn = psycopg2.connect(host='localhost', database='t2t',
                        user='brk', password='2001')
curr = conn.cursor()

get_devices_query = "SELECT * FROM backend_device;"
curr.execute(get_devices_query)

devices = {}
device = curr.fetchone()
while device:
    devices[device[0]] = device[3].replace(" ", "")
    device = curr.fetchone()

get_logs_query = "SELECT * FROM backend_statelog;"
curr.execute(get_logs_query)

logs = {}
log = curr.fetchone()
while log:
    curr_date = str(log[1])[:10]
    if curr_date not in logs.keys():
        logs[curr_date] = []
    logs[curr_date].append({"timestamp": log[1],
                            "device_id": log[7],
                            "device": devices[log[7]],
                            "cap_id": log[6],
                            "value": log[3].replace(" ", "")})

    log = curr.fetchone()

for date, l in logs.items():
    l = sorted(l, key=lambda i: i["timestamp"])
    f = open(
        f"raw_traces/{date}.json", "w")
    json.dump(l, f, default=str, indent=4)
    f.close()
