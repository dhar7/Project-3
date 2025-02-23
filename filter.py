import os
import re
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--threshold", required=False, default=0.1, type=float)
    args = parser.parse_args()

    regex = re.compile('^(\\S+) -> (\\S+) \\[label="(.*?)"\\]$')
    label_regex = re.compile(
        "^(\\S+) \\[(\\d+\\.\\d+), (\\d+\\.\\d+)\\](.*?)p=(\\d+\\.\\d+)$"
    )

    infiles = sorted(os.listdir(args.path + "/tas/"))
    infiles = sorted(infiles, key=len)

    total_count, lp_count = 0, 0
    for filename in infiles:
        filename = args.path + "/tas/" + filename
        f = open(filename, "r")

        for line in f.readlines():
            (src, dst, label) = [
                t(s) for t, s in zip((str, str, str), regex.search(line).groups())
            ]
            (event, t_low, t_high, _, prob) = [
                t(s)
                for t, s in zip(
                    (str, float, float, str, float), label_regex.search(label).groups()
                )
            ]
            total_count += 1
            if prob < args.threshold:
                lp_count += 1
                print(f"LOW PROBABILITY EVENT FOUND: {event}")
                print(f"\tFile: {filename}\tProb: {prob}\tTime: ({t_low},{t_high})")
                print(f"\tCount: {lp_count}/{total_count}")

        f.close()
