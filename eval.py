import os
import sys
import argparse
import math
import matplotlib.pyplot as plt
import dill as pickle

from modelgen import tagen
from modelgen import event_extractor
import dataset.autotap.prep as autotap
import dataset.trace2tap.prep as trace2tap
import dataset.fischertechnik.prep as ft

# Evaluation:
# RQ1: What is the accuracy of \pcfgs?
# RQ2: How does the accuracy of \pcfgs change without any model validation and repair?
# RQ3: What is \system's model generation performance overhead?
# RQ4: How useful are \pcfgs in anomaly detection?
# RQ4: How useful are \pcfgs in forensic analysis?

path = os.path.dirname(os.path.realpath(__file__))


def it_or_empty(k, d):
    if k in d.keys():
        return d[k]
    else:
        return None


def combine_dict(d1, d2, d3):
    return {
        k: (it_or_empty(k, d1), it_or_empty(k, d2), it_or_empty(k, d3))
        for k in set(d1.keys()) | set(d2.keys()) | set(d3.keys())
    }


def divide_dict(d, train_perc, test_perc):
    d_train, d_test, d_valid = {}, {}, {}

    for key, all_val in d.items():
        value = sorted(list(set(all_val)))

        train_idx = int(len(value) * train_perc)
        test_idx = train_idx + math.ceil(len(value) * test_perc)

        if train_idx < 1 or test_idx < 1 or len(value) - test_idx < 1:
            print(f"Ignoring {key}: train_idx: {train_idx}, test_idx: {test_idx}")
            continue

        d_train[key] = value[:train_idx]
        d_test[key] = value[train_idx:test_idx]
        d_valid[key] = value[test_idx:]

    return d_train, d_test, d_valid


def prep_phase(ds, out_path, train_set_perc, test_set_perc, search_view, context_perc):
    infiles = sorted(os.listdir(ds.path + "/raw_traces/"))
    infiles = sorted(infiles, key=len)
    seq_list = []
    event_set = set()
    for filename in infiles:
        print(f"Parsing file {filename}")
        raw_sequence = ds.read_file(ds.path + "/raw_traces/" + filename)
        seq_list.append(raw_sequence)
        for event in raw_sequence:
            event_set.add(event.sensor_id)

    tslist, (metric_dict, avg_period_dict, event_contexts) = event_extractor.extract(
        seq_list=seq_list,
        ignore=None,
        naive=True,
        search_view=search_view,
        context_tolerance=context_perc,
        merge_diff=True,
    )

    train_tslist, test_tslist, valid_tslist = divide_dict(
        tslist, train_set_perc, test_set_perc
    )

    train_filelist = {}
    for context, event_seq in train_tslist.items():
        train_outpath = f"{path}/{out_path}/traces/train_{context}.trace"
        train_filelist[context] = train_outpath
        with open(train_outpath, "w+") as outfile:
            outfile.write("\n".join(filter(None, event_seq)))

    test_filelist = {}
    for context, event_seq in test_tslist.items():
        test_outpath = f"{path}/{out_path}/traces/test_{context}.trace"
        test_filelist[context] = test_outpath
        with open(test_outpath, "w+") as outfile:
            outfile.write("\n".join(filter(None, event_seq)))

    valid_filelist = {}
    for context, event_seq in valid_tslist.items():
        valid_outpath = f"{path}/{out_path}/traces/valid_{context}.trace"
        valid_filelist[context] = valid_outpath
        with open(valid_outpath, "w+") as outfile:
            outfile.write("\n".join(filter(None, event_seq)))

    with open(f"{path}/{out_path}/metric.pkl", "wb+") as outfile:
        pickle.dump(metric_dict, outfile, pickle.HIGHEST_PROTOCOL)
    with open(f"{path}/{out_path}/period.pkl", "wb+") as outfile:
        pickle.dump(avg_period_dict, outfile, pickle.HIGHEST_PROTOCOL)
    with open(f"{path}/{out_path}/context.pkl", "wb+") as outfile:
        pickle.dump(event_contexts, outfile, pickle.HIGHEST_PROTOCOL)

    fpdict = combine_dict(train_filelist, test_filelist, valid_filelist)

    return fpdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["autotap", "trace2tap", "ft"])
    parser.add_argument("--train-set-perc", required=False, default=0.6)
    parser.add_argument("--test-set-perc", required=False, default=0.3)
    parser.add_argument("--context-perc", required=False, default=0.3)
    parser.add_argument("--search-view", required=False, default=0.2)
    parser.add_argument("--no-repair", required=False, action="store_true")
    parser.add_argument("--logfile", required=True)
    parser.add_argument("--output", required=False)
    args = parser.parse_args()

    ### Data Source Selection ###
    if args.dataset == "ft":
        ds = ft
    elif args.dataset == "trace2tap":
        ds = trace2tap
    else:
        ds = autotap

    os.makedirs(f"./out/{args.logfile}/tas", exist_ok=True)
    os.makedirs(f"./out/{args.logfile}/traces", exist_ok=True)
    os.makedirs(f"./out/{args.logfile}/logs", exist_ok=True)
    filename = f"{path}/out/{args.logfile}/logs/autogen_log"
    sys.stdout = open(filename, "w+")

    ### Preparation Phase ###
    print("========== PREPARATION PHASE STARTED ==========")
    fplist = prep_phase(
        ds,
        f"./out/{args.logfile}",
        float(args.train_set_perc),
        float(args.test_set_perc),
        float(args.search_view),
        float(args.context_perc),
    )
    fplist = dict(sorted(fplist.items()))
    print("========== PREPARATION PHASE ENDED ==========")

    i = 0
    score_hist = []
    all_cost, all_len, all_time_cost, all_num_viol = 0, 0, 0, 0
    for context, (train_tss, test_tss, valid_tss) in fplist.items():
        if not (train_tss and test_tss and valid_tss):
            continue

        ### Training Phase ###
        print(f"========== TA {i} / Context: {context} GENERATION STARTED ==========")
        ta = tagen.generate_ta(
            train_tss,
            test_tss,
            f"out/{args.logfile}/tas/ta_{context}_{i}",
            args.no_repair,
        )
        if ta is None:
            print(
                f"========== TA {i} / Context: {context} GENERATION FAILED =========="
            )
            continue

        print(f"\tTA {i} / Context: {context} GENERATION ENDED")

        ### Evaluation Phase ###
        print(f"\tTA {i} / Context: {context} SCORING STARTED")
        costs = tagen.score_ta(ta, valid_tss)
        total_cost = sum([c[0] for c in costs])
        total_len = sum([c[1] for c in costs])
        total_time_cost = sum([c[2][0] for c in costs])
        total_num_viol = sum([c[2][1] for c in costs])
        score = 1 - (total_cost / total_len)
        if score < 0:
            score = 0
        all_cost += total_cost
        all_len += total_len
        all_time_cost += total_time_cost
        all_num_viol += total_num_viol
        score_hist.append(score)
        print(
            f"\t ACCURACY SCORE: {score}\tTIME SKEW: {total_time_cost} NUMBER OF VIOLATIONS: {total_num_viol}"
        )
        print(f"========== TA {i} / Context: {context} SCORING ENDED ==========")

        i += 1

    print("AUTOGEN FINISHED")
    print(f"TOTAL NUMBER OF EVENTS: {all_len}\tNUMBER OF VIOLATIONS: {all_num_viol}")
    print(f"AVERAGE SCORE: {1 - (all_cost / all_len)}")
    print(f"\tHistogram:\n{score_hist}")
    plt.title("Distribution of Accuracy Values")
    plt.xlabel("Accuracy")
    plt.ylabel("Number of event contexts")
    plt.hist(score_hist, bins=10)
    png_name = f"./out/{args.logfile}/logs/hist.png"
    plt.savefig(png_name, bbox_inches="tight")
