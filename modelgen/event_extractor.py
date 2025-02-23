import math
import copy
from dataclasses import dataclass
from efficient_apriori import apriori


@dataclass(frozen=False)
class Event:
    event_time: int  # Relative to the beginning
    sensor_id: str | list
    value: str | float | list


def get_event_string(event):
    if not isinstance(event.value, list):
        return f"{event.sensor_id}_{event.value}".lower()
    else:
        s = ""
        l = list(zip(event.sensor_id, event.value))
        for sensor, value in sorted(l, key=lambda i: i[0]):
            s += f"{sensor}_{value}".lower() + "_AND_"

        return s[:-5]


def extract_events(seq_list):
    event_list = []
    event_type_set = set()
    for raw_sequence in seq_list:
        last_val = {}
        sequence = []
        for event in raw_sequence:
            if (
                event.sensor_id in last_val.keys()
                and last_val[event.sensor_id] == event.value
            ):
                continue
            event_type_set.add(event.sensor_id)
            sequence.append(copy.deepcopy(event))
            last_val[event.sensor_id] = event.value

        event_list.append(sequence)

    return event_list, sorted(list(event_type_set))


def generate_metric(seq_list, scale=1):
    sensor_reading_vals = {}
    for raw_sequence in seq_list:
        for event in raw_sequence:
            if event.sensor_id not in sensor_reading_vals.keys():
                sensor_reading_vals[event.sensor_id] = [event.value]
            else:
                sensor_reading_vals[event.sensor_id].append(event.value)

    metric_dict = {}
    for event, l in sensor_reading_vals.items():
        if not isinstance(l[0], float):
            metric_dict[event] = lambda x: x
            continue
        max_val = max(l)
        min_val = min(l)
        # class_interval = math.ceil(
        #     (max_val - min_val) / (1 + 3.222 * math.log2(len(l)))
        # )  # Cite Sturge's rule
        class_interval = (max_val - min_val) / math.ceil((len(l) ** (1 / 3))) * scale

        if class_interval == 0:
            metric_dict[event] = lambda x: f"B{int(x)}"
        else:
            metric_dict[event] = (
                lambda x, min_val=min_val, class_interval=class_interval: (
                    f"B{math.floor((x - min_val) / class_interval)}"
                )
            )

    return metric_dict


def discretize(seq_list, metric_dict):
    disc_seq_list = []
    for raw_sequence in seq_list:
        sequence = []
        for raw_event in raw_sequence:
            event = raw_event
            event.value = metric_dict[event.sensor_id](event.value)
            sequence.append(copy.deepcopy(event))

        disc_seq_list.append(sequence)

    return disc_seq_list


def calculate_periods(event_list, check_as_event=False):
    period_dict = {}
    for event_l in event_list:
        for event in event_l:
            if check_as_event:
                estr = get_event_string(event)
            else:
                estr = event.sensor_id

            if estr not in period_dict.keys():
                period_dict[estr] = [event.event_time]
            else:
                period_dict[estr].append(event.event_time - period_dict[estr][0])
                period_dict[estr][0] = event.event_time

    for event, time_diffs in period_dict.items():
        if len(time_diffs) == 1:
            period_dict[event] = 0
            continue
        sum_list = list(map(abs, time_diffs[1:]))
        period_dict[event] = sum(sum_list) / len(time_diffs[1:])

    return period_dict


def event_relative_frequencies(
    event_list, avg_period_dict, search_view, check_as_event=False
):
    event_types = list(avg_period_dict.keys())

    freq_dict = {}
    for t in event_types:
        freq_dict[t] = {tt: fq for tt, fq in zip(event_types, [0] * len(event_types))}

    for event_l in event_list:
        for event_type in event_types:
            last_t = -1
            occured_list = []
            for event in event_l:
                if check_as_event:
                    estr = get_event_string(event)
                else:
                    estr = event.sensor_id

                if estr == event_type:
                    last_t = event.event_time
                    freq_dict[event_type][estr] += 1
                    occured_list = []
                    continue

                # Handle already occured events in one interval, count them as one
                if estr in occured_list:
                    continue

                if (
                    last_t > 0
                    and abs(last_t - event.event_time)
                    < avg_period_dict[event_type] * search_view
                ):
                    occured_list.append(estr)
                    freq_dict[event_type][estr] += 1

    return freq_dict


def maxN(d, N):
    sd = sorted(d.items(), key=lambda i: i[1], reverse=True)
    v_old = None
    i = 0
    l = []
    for k, v in sd:
        if i == N:
            break

        if v != v_old:
            i += 1
        l.append(k)
        v_old = v

    return l


def separate_context(
    event_list,
    event_type_set,
    avg_period_dict,
    event_contexts,
    search_view=0.5,
    check_as_event=False,
):
    contextualized_event_seq = {}
    for test_event in event_type_set:
        if test_event not in event_contexts.keys():
            continue

        event_seq_col = []
        for event_l in event_list:
            n_seq = []
            last_t = -1
            for event in event_l:
                if check_as_event:
                    estr = get_event_string(event)
                else:
                    estr = event.sensor_id

                if estr == test_event:
                    last_t = event.event_time
                    n_seq.append(copy.deepcopy(event))
                    continue

                if (
                    last_t > 0
                    and estr in event_contexts[test_event]
                    and abs(last_t - event.event_time)
                    < avg_period_dict[test_event] * search_view
                ):
                    n_seq.append(copy.deepcopy(event))

            event_seq_col.append(copy.deepcopy(n_seq))

        contextualized_event_seq[test_event] = event_seq_col

    return contextualized_event_seq


def apriori_separation(
    event_list,
    event_type_set,
    search_view=0.5,
    context_num_max=5,
    min_support=0.4,
    min_confidence=0.4,
    check_as_event=False,
):
    avg_period_dict = calculate_periods(event_list, check_as_event)
    freq_dict = event_relative_frequencies(
        event_list, avg_period_dict, search_view, check_as_event
    )
    print(freq_dict)

    relation_list = []
    for freqs in freq_dict.values():
        relation_list.append(maxN(freqs, context_num_max))

    _, rules = apriori(
        relation_list, min_support=min_support, min_confidence=min_confidence
    )

    event_contexts = {}
    for event in freq_dict.keys():
        event_contexts[event] = set()

    for rule in rules:
        for r in rule.lhs:
            for l in rule.rhs:
                event_contexts[r].add(l)
                event_contexts[l].add(r)

    contextualized_event_seq = {}
    for test_event in event_type_set:
        event_seq_col = []
        for event_l in event_list:
            n_seq = []
            for event in event_l:
                if check_as_event:
                    estr = get_event_string(event)
                else:
                    estr = event.sensor_id

                if estr == test_event:
                    n_seq.append(copy.deepcopy(event))
                    continue

                if estr in event_contexts[test_event]:
                    n_seq.append(copy.deepcopy(event))

            event_seq_col.append(n_seq)

        contextualized_event_seq[test_event] = event_seq_col

    return contextualized_event_seq


def ignore_filter(ignfile, seq_list):
    f = open(ignfile)
    ign_list = map(lambda x: x[:-1], list(f.readlines()))
    filtered_seq = []
    for events in seq_list:
        filtered_list = []
        for event in events:
            if event.sensor_id in ign_list:
                continue
            filtered_list.append(copy.deepcopy(event))
        filtered_seq.append(filtered_list)
    return filtered_seq


def merge_events(seq_list, time_diff=0):
    merged_seq_list = []
    for events in seq_list:
        if not events:
            continue

        merged_events = []
        last_event = copy.deepcopy(events[0])
        for event in events[1:]:
            if abs(last_event.event_time - event.event_time) <= time_diff:
                if not isinstance(last_event.sensor_id, list):
                    last_event.sensor_id = [last_event.sensor_id]
                    last_event.value = [last_event.value]

                last_event.sensor_id.append(event.sensor_id)
                last_event.value.append(event.value)
            else:
                merged_events.append(last_event)
                last_event = copy.deepcopy(event)

        merged_events.append(last_event)
        merged_seq_list.append(merged_events)

    return merged_seq_list


def sequence_to_string(sequence):
    if sequence == []:
        return ""

    s = []
    ltime = sequence[0].event_time
    for event in sequence:
        s.append(f"{get_event_string(event)}:{event.event_time - ltime}")
        ltime = event.event_time

    return " ".join(s)


def events_in_tolerance(event, freqs, context_tolerance):
    l = []
    for e, f in freqs.items():
        if f == 0:
            continue
        if abs(f / freqs[event] - 1) < context_tolerance:
            l.append(e)
    return l


def extract(
    seq_list,
    ignore=[],
    search_view=0.1,
    context_tolerance=0.3,
    metric_scale=1,
    naive=False,
    min_support=0.4,
    min_confidence=0.4,
    check_as_event=False,
    merge_diff=False,
    time_diff_to_merge=0,
):

    metric_dict = generate_metric(seq_list, metric_scale)
    print("Metrics generated. Progress: 1/6 Tasks")

    disc_seq_list = discretize(seq_list, metric_dict)
    print("Discretization done. Progress: 2/6 Tasks")

    event_list, event_type_set = extract_events(disc_seq_list)
    print("Events extracted. Progress: 3/6 Tasks")

    if naive:
        avg_period_dict = calculate_periods(event_list, check_as_event)
        freq_dict = event_relative_frequencies(
            event_list, avg_period_dict, search_view, check_as_event
        )

        event_contexts = {}
        for event, freqs in freq_dict.items():
            event_contexts[event] = events_in_tolerance(event, freqs, context_tolerance)

        contextualized_event_seq = separate_context(
            event_list,
            event_type_set,
            avg_period_dict,
            event_contexts,
            search_view,
            check_as_event,
        )
    else:
        raise AssertionError("This method is not complete")
        contextualized_event_seq = apriori_separation(
            event_list,
            event_type_set,
            search_view=search_view,
            context_num_max=context_num_max,
            check_as_event=check_as_event,
            min_support=min_support,
            min_confidence=min_confidence,
        )
    print("Context separation done. Progress: 4/6 Tasks")

    contextualized_tslist = {}
    for i, (context, event_seq) in enumerate(contextualized_event_seq.items()):
        filtered_seq = event_seq
        if ignore:
            filtered_seq = ignore_filter(ignore, filtered_seq)
            print(
                f"Ignored event filtering done. Progress: 5.{i}/6.{len(contextualized_event_seq.values()) - 1} Tasks"
            )

        if merge_diff:
            final_seq = merge_events(filtered_seq, time_diff_to_merge)
        else:
            final_seq = filtered_seq

        print(
            f"Zero-timed events merged, writing to file. Progress: 6.{i}/6.{len(contextualized_event_seq.values()) - 1} Tasks"
        )

        tslist = []
        for events in final_seq:
            seq_str = sequence_to_string(events)
            tslist.append(seq_str)

        contextualized_tslist[context] = tslist

    return contextualized_tslist, (metric_dict, avg_period_dict, event_contexts)
