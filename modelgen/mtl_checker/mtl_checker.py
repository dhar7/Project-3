from dataclasses import dataclass
import sys
import mtl

sys.path.append("/home/brk/development/pursec/mtlmine/miner/event_extractor")
from event_extractor import generate_metric, discretize, extract_events, merge_events, get_event_string, Event  # noqa: E402


@dataclass
class Formula:
    formula: str
    prob: float
    rare: bool


@dataclass
class TimeSeriesItem:
    types: set
    series: list[tuple[str, bool]]


def read_events(reader, file_list, metric_scale=1):
    print("Starting.")
    seq_list = []
    for filename in file_list:
        raw_sequence = reader(filename)
        seq_list.append(raw_sequence)

    metric_dict = generate_metric(seq_list, metric_scale)
    disc_seq_list = discretize(seq_list, metric_dict)
    event_list = extract_events(disc_seq_list)

    return event_list


def read_formula(filename):
    flist = []
    with open(filename) as f:
        for line in f.readlines()[:-2]:
            formula, prs = line.split("\t")
            formula = formula.replace("_AND_", " & ")

            prob = float(prs[3:11])
            rare = bool(int(prs[18:]))

            flist.append(Formula(formula, prob, rare))

    return flist


def get_formula_preds(formula):
    f = formula.replace("->", " ")
    f = f.replace("G", " ")
    f = f.replace("F", " ")
    f = f.replace("(", " ")
    f = f.replace(")", " ")

    f = f.split()
    pred_set = set()
    for s in f:
        s = s.split("&")
        for ss in s:
            if "." in ss or not ss:
                continue
            pred_set.add(ss)

    return list(pred_set)


def get_sensor_val_from_str(event_str):
    sp_event = event_str.split("_")
    sensor_id = "_".join(sp_event[:-1])
    value = sp_event[-1]

    return sensor_id, value


def check_one(formula, time_series):
    preds = get_formula_preds(formula.formula)
    phi = mtl.parse(formula.formula)

    return phi(time_series)


def check(event_reader, event_filelist, formula_filelist):
    events_list = read_events(event_reader, event_filelist)
    # events_list = merge_events(events_list)

    formulas_list = []
    for formula_list in formula_filelist:
        formula_list = read_formula(formula_list)
        formulas_list.append(formula_list)

    time_series = []
    all_pred_set = set()
    for events in events_list:
        ts = {}
        for event in events:
            all_pred_set.add(get_event_string(event))
            if event.sensor_id not in ts.keys():
                ts[event.sensor_id] = TimeSeriesItem(set(), [])
            ts[event.sensor_id].types.add(get_event_string(event))
            ts[event.sensor_id].series.append(
                (get_event_string(event), event.event_time))
        time_series.append(ts)

    time_series_flat = []
    for ts in time_series:
        ts_flat = {k: [(0, False)] for k in all_pred_set}
        for _, l in ts.items():
            for step in l.series:
                for pred in l.types:
                    if step[0] == pred:
                        if not ts_flat[pred][-1][1]:
                            ts_flat[pred].append((step[1], True))
                    else:
                        if ts_flat[pred][-1][1]:
                            ts_flat[pred].append((step[1], False))

        time_series_flat.append(ts_flat)

    num_v = 0
    violations_list = []
    for flist in formulas_list:
        for i, formula in enumerate(flist):
            if not formula.rare:
                vlist = []
                for ts in time_series_flat:
                    v = check_one(formula, ts)
                    if not v:
                        print(
                            f"Found violation of policy {i}, {formula.formula}, P: {formula.prob}")
                        vlist.append((formula))
                        num_v += 1
                violations_list.append(vlist)

    print(f"Num of violations: {num_v}")
    return events_list
