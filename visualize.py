#
# Usage: python visualize.py --input <ta path> --output <output path (optional)>
#


import argparse

import re
from pyvis.network import Network


def visualize(input_file, output_file=None, color=None, highlight=None):
    regex = re.compile('^(\\S+) -> (\\S+) \\[label="(.*?)"\\]$')
    label_regex = re.compile(
        "^(\\S+) \\[(\\d+\\.\\d+), (\\d+\\.\\d+)\\](.*?)p=(\\d+\\.\\d+)$"
    )

    filename = input_file
    f = open(filename, "r")

    states = set()
    edges = set()
    for line in f.readlines():
        (src, dst, label) = [
            t(s) for t, s in zip((str, str, str), regex.search(line).groups())
        ]

        states.add(src)
        states.add(dst)
        edges.add((src, label, dst))

    net = Network(directed=True)
    net.add_nodes(states)
    event_id = 0
    for src, label, dst in edges:
        (ename, _, _, _, prob) = [
            t(s)
            for t, s in zip(
                (str, float, float, str, float), label_regex.search(label).groups()
            )
        ]

        if color:
            if prob > 0.5:
                color = "green"
            elif prob > 0.1:
                color = "yellow"
            else:
                color = "red"
        else:
            color = "black"

        if highlight is not None and ename in highlight:
            color = "red"

        label = label.replace("[", "\n[", 1)
        label_list = label.split("_AND_")
        if len(label_list) > 1:
            label = label_list[0]
            label_list = label_list[1:]
            line_len = len(label)
            while len(label_list) > 1:
                if line_len > 80:
                    label += "\n"
                    line_len = 0
                label += " ∧ " + label_list[0]
                line_len += len(label_list[0])
                label_list = label_list[1:]
            label += " ∧ " + label_list[0]

        event_name_dict = {}
        if label not in event_name_dict.keys():
            event_name_dict[label] = f"E{event_id}"
            event_id += 1
        net.add_edge(
            src,
            dst,
            label=event_name_dict[label],
            title=label,
            color=color,
            arrows="middle",
        )

    net.show_buttons()
    net.force_atlas_2based()
    if output_file is None:
        net.show(f"{input_file}.html", notebook=False)
    else:
        net.show(f"{output_file}_visual.html", notebook=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=False)
    parser.add_argument("--color", required=False, action="store_true")
    parser.add_argument("--highlight", required=False, nargs="+")
    args = parser.parse_args()

    visualize(args.input, args.output, args.color, args.highlight)
