from dataclasses import dataclass
import sys
import rtamt

sys.path.append("/home/brk/development/pursec/mtlmine/miner/event_extractor")
from event_extractor import generate_metric, discretize, extract_events, merge_events, get_event_string, Event  # noqa: E402


@dataclass
class Formula:
    formula: str
    prob: float
    rare: bool


@dataclass
class Violation:
    formula: Formula
    event: Event
    time: int


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
            formula = formula.replace("_AND_", " and ")

            prob = float(prs[3:11])
            rare = bool(int(prs[18:]))

            flist.append(Formula(formula, prob, rare))

    return flist


def get_formula_preds(formula):
    f = formula.replace("implies", " ")
    f = f.replace("always", " ")
    f = f.replace("finally", " ")
    f = f.replace("(", " ")
    f = f.replace(")", " ")

    f = f.split()
    pred_set = set()
    for s in f:
        s = s.split("and")
        for ss in s:
            if "." in ss or not ss:
                continue
            pred_set.add(ss)

    return list(pred_set)


def get_updates(event, pred_vals):
    u = False
    events_str = get_event_string(event).split("_AND_")
    for event_str in events_str:
        if event_str in pred_vals.keys():
            if pred_vals[event_str] != 1:
                pred_vals[event_str] = 1
                u = True
        else:
            for pred in pred_vals.keys():
                if event.sensor_id == get_sensor_val_from_str(pred)[0]:
                    if pred_vals[pred] != 0:
                        pred_vals[pred] = 0
                        u = True

    return pred_vals, u


def get_stl_rule(formula, preds):
    f = formula
    for pred in preds:
        f = f.replace(pred, f"({pred}==1)")

    return f


def get_sensor_val_from_str(event_str):
    sp_event = event_str.split("_")
    sensor_id = "_".join(sp_event[:-1])
    value = sp_event[-1]

    return sensor_id, value


def check_one(formula, event_list):
    event_list = merge_events(event_list)
    spec = rtamt.StlDiscreteTimeSpecification()
    preds = get_formula_preds(formula.formula)
    for pred in preds:
        spec.declare_var(pred, "int")
    spec.spec = get_stl_rule(formula.formula, preds)
    print(spec.spec)

    try:
        spec.parse()
        spec.pastify()

        violation_list = []
        for events in event_list:
            pred_vals = {k: 0 for k in preds}
            for event in events:
                pred_vals, is_upd = get_updates(event, pred_vals)
                if not is_upd:
                    continue

                pred_vals = {'Unknown_temperature_B2': 0,
                             'Unknown_temperature_B0': 1}
                print(pred_vals, event.event_time)
                rob = spec.update(event.event_time, [
                                  (k, v) for k, v in pred_vals.items()])
                print(f"robustness: {rob}")

                if rob < 0:
                    print(f"Found violation of {formula} at event {event}")
                    violation_list.append(
                        Violation(formula, event, event.event_time))

            print("-------------")

    except rtamt.RTAMTException as err:
        print('RTAMT Exception: {}'.format(err))
        sys.exit()

    return violation_list


def check(event_reader, event_filelist, formula_filelist):
    events_list = read_events(event_reader, event_filelist)

    formulas_list = []
    for formula_list in formula_filelist:
        formula_list = read_formula(formula_list)
        formulas_list.append(formula_list)

    violations_list = []
    for flist in formulas_list:
        for formula in flist:
            if not formula.rare:
                violation_list = check_one(formula, events_list)
                violations_list.append(violation_list)
    print(violations_list)
    return events_list
