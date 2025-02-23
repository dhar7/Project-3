from math import inf
import networkx as nx
import matplotlib.pyplot as plt
from .TAG.Automaton import Automaton


class Repairer:
    def __init__(self, automaton: Automaton, tss: list):
        self.tss = tss
        self.automaton = automaton
        self.automaton_nx = None  # self.__convert_to_nx(automaton)
        self.start_candid = []
        self.end_candid = []

    def __nx_from_ts(self, ts: list[str]) -> nx.MultiDiGraph:
        g = nx.MultiDiGraph()
        g.add_node(0, name="S0", initial=True, accepting=False)
        last_si = 0
        for i, s in enumerate(ts[:-1], 1):
            event, time = s.split(":")
            g.add_node(i, name=f"S{i}", initial=False, accepting=False)
            g.add_edge(i - 1, i, symbol=event, orig=False, t=float(time))
            last_si = i
        g.add_node(last_si + 1, name=f"S{last_si+1}", initial=False, accepting=True)
        event, time = ts[-1].split(":")
        g.add_edge(last_si, last_si + 1, symbol=event, orig=False, t=float(time))

        return g

    def __convert_to_nx(self, automaton: Automaton) -> nx.MultiDiGraph:
        g = nx.MultiDiGraph()

        s_nid_dict = {}
        for i, s in enumerate(automaton.states):
            g.add_node(i, name=s.name, initial=s.initial, accepting=s.accepting)
            s_nid_dict[s.name] = i

        for e in automaton.edges:
            g.add_edge(
                s_nid_dict[e.source.name],
                s_nid_dict[e.destination.name],
                symbol=e.symbol,
                orig=True,
                t=e.guard,
            )

        return g

    def show_nx(self, nx_graph: nx.MultiDiGraph):
        edge_labels = dict(
            [((n1, n2), f"{attr}") for n1, n2, attr in nx_graph.edges(data="symbol")]
        )

        pos = nx.spring_layout(nx_graph)
        nx.draw_networkx(nx_graph, pos)
        nx.draw_networkx_edge_labels(
            nx_graph, pos, edge_labels=edge_labels, font_size=5
        )
        plt.show()

    def edge_weight(self, s, e, a):
        min_cost = inf
        for attr in a.values():
            if isinstance(attr["symbol"], tuple):
                if attr["symbol"][0] == attr["symbol"][1]:
                    return 0
                else:
                    min_cost = 1
            elif not attr["orig"] and min_cost > 1:
                min_cost = 10
        return min_cost

    def score_time(self, product, path):
        num_viol = 0
        cost = 0
        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]
            edge = product[start][end]
            min_dist = inf
            past_match = False
            for attr in edge.values():
                if isinstance(attr["symbol"], tuple):
                    if attr["symbol"][0] == attr["symbol"][1]:
                        past_match = True

                        t = attr["t"][1]
                        int_low = min(attr["t"][0])
                        int_high = max(attr["t"][0])
                        if int_low <= t <= int_high:
                            dist = 0
                        elif int_low > t:
                            dist = int_low - t
                        elif t > int_high:
                            dist = t - int_high
                    else:
                        dist = attr["t"][1]
                elif not past_match:
                    dist = attr["t"]

                if min_dist > dist:
                    min_dist = dist

            cost += min_dist
            if min_dist > 0:
                num_viol += 1

        return cost, num_viol

    def __add_missing_edges(self, product: nx.MultiDiGraph, path):
        added_edges = 0
        gtime = 0
        tss_idx = len(self.automaton.tss) - 1
        for i in range(len(path) - 1):
            e_attr = product[path[i]][path[i + 1]]
            attr = list(e_attr.values())[0]
            w = self.edge_weight(path[i], path[i + 1], e_attr)
            src = product.nodes[path[i]]["name"][0]
            dst = product.nodes[path[i + 1]]["name"][0]
            if isinstance(attr["symbol"], tuple):
                ename = attr["symbol"][1]
                guard = attr["t"][0]
                t = attr["t"][1]
                gtime += t
                guard.append(t)
            else:
                ename = attr["symbol"]
                t = attr["t"]
                guard = [t]
                gtime += t

            if inf > w > 0:
                e = self.automaton.add_edge(src, dst, ename, guard)
                e.tss[tss_idx] = [(i, gtime)]
                added_edges += 1
            elif w == 0:
                src_state = self.automaton.search_state(src)
                next_edges = []
                for e in src_state.edges_out:
                    if e.destination.name == dst and e.symbol == ename:
                        next_edges.append((e, min(e.guard), max(e.guard)))
                dist = inf
                ne = next_edges[0]
                for e, int_low, int_high in next_edges:
                    if int_low <= t <= int_high:
                        ne = e
                        break
                    if int_low - t < dist:
                        ne = e
                        dist = int_low - t
                    elif t - int_high < dist:
                        ne = e
                        dist = t - int_high

                ne.guard.append(t)
                if tss_idx not in ne.tss.keys():
                    ne.tss[tss_idx] = [(i, gtime)]
                else:
                    ne.tss[tss_idx].append((i, gtime))

        return added_edges

    def __match(self, path, product):
        mismatch_edge_list = []
        for i in range(len(path) - 1):
            src = path[i]
            dst = path[i + 1]
            a = product[src][dst]
            mismatch = True
            for attr in a.values():
                if isinstance(attr["symbol"], tuple):
                    if attr["symbol"][0] == attr["symbol"][1]:
                        mismatch = False
                        guard = attr["t"][0]
                        t = attr["t"][1]
                        if min(guard) <= t <= max(guard):
                            time_mismatch = False
                        else:
                            time_mismatch = True
                        break

            if mismatch or time_mismatch:
                mismatch_edge_list.append(
                    (product.nodes[src]["name"], product.nodes[dst]["name"], a)
                )

        return mismatch_edge_list

    def repair(self, score_only=False, path_match=False):
        cost_len_list = []

        for ts in self.tss:
            if len(ts) == 0:
                continue

            self.automaton_nx = self.__convert_to_nx(self.automaton)
            start_candids = [(n, 0) for n in self.automaton_nx.nodes]

            self.ts_nx = self.__nx_from_ts(ts)
            end_candids = [
                (n, list(self.ts_nx.nodes)[-1]) for n in self.automaton_nx.nodes
            ]
            product = nx.strong_product(self.automaton_nx, self.ts_nx)

            paths = []
            for end in end_candids:
                try:
                    dist, path = nx.multi_source_dijkstra(
                        product,
                        start_candids,
                        end,
                        weight=self.edge_weight,
                    )
                except nx.NetworkXNoPath:
                    pass
                else:
                    paths.append((dist, path))
            if not paths:
                if not score_only and not path_match:
                    print(
                        "-------------------------- !!!!!! NO VALID PATH FOUND !!!!!! --------------------------"
                    )
                continue

            cost, min_path = min(paths, key=lambda i: i[0])
            print(
                f"Cost: {cost}/{len(ts)} = {cost / len(ts)}\tPath length:{len(min_path)}"
            )
            if len(min_path) - 1 != len(ts):
                print(
                    "-------------------------- !!!!!! MISSING EDGES !!!!!! --------------------------"
                )
            if not score_only and not path_match:
                self.automaton.tss.append(ts)
                added_edges = self.__add_missing_edges(product, min_path)
                print(f"Number of edges added: {added_edges}")
            elif not path_match:
                time_cost, num_viol = self.score_time(product, min_path)
                print(f"Time cost: {time_cost}\tNumber of time violations: {num_viol}")
                cost_len_list.append((cost, len(ts), (time_cost, num_viol)))

        if not score_only and not path_match:
            self.automaton.update_probas()

        if path_match:
            return self.automaton, self.__match(min_path, product)

        return self.automaton, cost_len_list
