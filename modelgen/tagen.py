import sys
from copy import deepcopy
from .repairer import Repairer
from .TAG.TALearner import TALearner
from .TAG.Automaton import Automaton


def parse_tss(tss_file):
    f = open(tss_file)
    tss = []
    for tss_str in f.readlines():
        tss.append(tss_str.split())

    return tss


def generate_ta(
    train_tss: str, test_tss: str, output: str, no_repair: bool
) -> Automaton:
    l = TALearner(train_tss)

    if no_repair:
        print("Skipping repair")
        ta = l.ta
    else:
        r = Repairer(deepcopy(l.ta), parse_tss(test_tss))
        ta, _ = r.repair()

    ta.export_ta(output + ".ta")

    print("TA Statistics:")
    print(f"\tStates: {len(ta.states)}\tEdges: {len(ta.edges)}")

    return ta


def score_ta(ta, test_tss: str) -> list[tuple[float, float]]:
    r = Repairer(ta, parse_tss(test_tss))
    _, costs = r.repair(score_only=True)
    if not costs:
        return 0.0
    return costs


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Missing argument")
        sys.exit(1)

    ta = generate_ta(sys.argv[1], sys.argv[2], sys.argv[1])

    print("Num states:", len(ta.states))
    print("Num edges:", len(ta.edges))
    print("Num symbols:", len(ta.symbols))
