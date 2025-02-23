import dill as pickle
import argparse

from modelgen.TAG.Automaton import Automaton
from modelgen import event_extractor
from modelgen import repairer


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", required=True)
    parser.add_argument("--period", required=True)
    parser.add_argument("--all-contexts", required=True)
    parser.add_argument("--ta", required=True)
    parser.add_argument("--trace", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--search-view", required=False, default=0.2)
    args = parser.parse_args()

    with open(args.metric, "rb") as f:
        metric_dict = pickle.load(f)
    with open(args.period, "rb") as f:
        avg_period_dict = pickle.load(f)
    with open(args.all_contexts, "rb") as f:
        event_contexts = pickle.load(f)
    with open(args.trace, "rb") as f:
        raw_sequence = [pickle.load(f)]

    disc_seq_list = event_extractor.discretize(raw_sequence, metric_dict)
    event_list, event_type_set = event_extractor.extract_events(disc_seq_list)

    contextualized_event_seq = event_extractor.separate_context(
        event_list,
        event_type_set,
        avg_period_dict,
        event_contexts,
        args.search_view,
    )

    contextualized_tslist = {}
    for context, event_seq in contextualized_event_seq.items():
        final_seq = event_extractor.merge_events(event_seq, 0)

        tslist = []
        for events in final_seq:
            seq_str = event_extractor.sequence_to_string(events).split()
            tslist.append(seq_str)

        contextualized_tslist[context] = tslist

    ta = Automaton()
    ta.import_from_dot(args.ta)
    try:
        event_seq = contextualized_tslist[args.context]
    except KeyError:
        print("Cannot find the context in the trace.")
        print(f"Possible entries are:")
        print(list(contextualized_tslist.keys()))
    r = repairer.Repairer(ta, event_seq)
    ta, mismatch_edge_list = r.repair(path_match=True)
    for i, (src, dst, a) in enumerate(mismatch_edge_list):
        print(f"ANOMALY {i}:")
        for attr in a.values():
            if isinstance(attr["symbol"], tuple):
                if attr["symbol"][0] == attr["symbol"][1]:
                    guard = attr["t"][0]
                    t = attr["t"][1]
                    if not (min(guard) <= t <= max(guard)):
                        print(f"\tTIME MISMATCH: guard={guard} t={t}")
                        ename = attr["symbol"]
                    break
            else:
                ename = attr["symbol"]
                t = attr["t"]
        print(f"\tNOT MATCHED: {src} --- {ename} ---> {dst}")
