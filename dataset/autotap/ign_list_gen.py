import sys
import parse


def find_events(mtl):
    events = []
    l = parse.parse(
        "{id}:\t{start} -> <>[{c1},{c2}]({subformula}) P: {prob} Rare: {rare}", mtl).named
    rare = l["rare"][:-1]
    while l:
        events.append(l["start"])
        l = parse.parse(
            "{start} -> <>[{c1},{c2}]({subformula})", l["subformula"])

    return events[1:], rare


f = open(sys.argv[1])
mtl_list = list(f.readlines())
events_to_remove = {}
for mtl in mtl_list:
    events, rare = find_events(mtl)
    for event in events:
        if event not in events_to_remove.keys():
            events_to_remove[event] = [0, 1]
        if rare == "1":
            events_to_remove[event][0] += 1
        events_to_remove[event][1] += 1

for event, stat in events_to_remove.items():
    if stat[0] / stat[1] < 0.8:
        print(event)
