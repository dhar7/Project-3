import csv
import sys
import os


def str_part_in_list(input, l):
    for s in l:
        if s in input:
            return True

    return False


def filter_fields(trace, filter):
    ret = {}
    for k, v in trace.items():
        if not str_part_in_list(k, filter):
            ret[k] = v

    return ret


filenames = sorted(sys.argv[1:], key=lambda s: int(os.path.basename(s)[3:-4]))
i = 0
for filename in filenames:
    file = open(filename)
    reader = csv.DictReader(file)
    traces = [row for row in reader]
    file.close()

    os.remove(filename)

    if not traces:
        continue

    fieldnames = []
    filter = ["SSC", "Publish"]
    if reader.fieldnames is None:
        sys.exit(1)

    for field in reader.fieldnames:
        if str_part_in_list(field, filter):
            continue
        fieldnames.append(field)

    old_mode = (
        traces[0]["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]
        == "WAITING_FOR_ORDER"
    )
    while not traces[0]["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]:
        traces = traces[1:]
        old_mode = (
            traces[0]["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]
            == "WAITING_FOR_ORDER"
        )

    order_mode_traces = []
    delivery_mode_traces = []
    for trace in traces:
        if not trace["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]:
            continue

        trace = filter_fields(trace, filter)

        if (
            trace["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]
            == "WAITING_FOR_ORDER"
        ):
            delivery_mode_traces.append(trace)
        else:
            order_mode_traces.append(trace)

        if old_mode != (
            trace["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]
            == "WAITING_FOR_ORDER"
        ):
            name = (
                "delivery"
                if trace["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]
                == "WAITING_FOR_ORDER"
                else "order"
            )
            dirname = os.path.dirname(filename)
            fname = os.path.basename(filename)
            file = open(f"./{dirname}/{name}_part{i:04}_{fname[:-4]}.csv", "w+")
            writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            if old_mode:
                writer.writerows(order_mode_traces)
                order_mode_traces = []
            else:
                writer.writerows(delivery_mode_traces)
                delivery_mode_traces = []
            file.close()

            old_mode = (
                trace["gtyp_Interface_Dashboard.Subscribe.State_Order.s_state"]
                == "WAITING_FOR_ORDER"
            )
            i += 1

    if order_mode_traces or delivery_mode_traces:
        name = "delivery" if delivery_mode_traces else "order"
        dirname = os.path.dirname(filename)
        fname = os.path.basename(filename)
        file = open(f"./{dirname}/{name}_part{i:04}_{fname[:-4]}.csv", "w+")
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        if not old_mode:
            writer.writerows(order_mode_traces)
        else:
            writer.writerows(delivery_mode_traces)
        file.close()
