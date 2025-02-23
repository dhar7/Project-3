#include "automaton.h"

#define TIME_TOLERATION 0.1

struct event {
	char *event;
	float event_time;
};

struct tlist {
	int len;
	struct event *trace_list;
};

void add_trace(struct tlist *tlist, struct event t)
{
	if (tlist->len == 0)
		tlist->trace_list = malloc(sizeof(struct event));
	else
		tlist->trace_list =
			realloc(tlist->trace_list,
				(tlist->len + 1) * sizeof(struct event));

	tlist->trace_list[tlist->len] = t;
	tlist->len++;
}

void free_tlist(struct tlist *tlist)
{
	free(tlist->trace_list);
	tlist->trace_list = 0;
	tlist->len = 0;
}

char in_interval(double i_high, double i_low, double value)
{
	return (i_high >= value && i_low <= value);
}

struct state *mark_list[1000];
int mark_list_len;

void mark_state(struct state *state)
{
	mark_list[mark_list_len] = state;
	mark_list_len++;
}

char in_mark_list(struct state *state)
{
	for (int i = 0; i < mark_list_len; i++) {
		if (strcmp(mark_list[i]->label, state->label) == 0)
			return 1;
	}

	return 0;
}

void clear_mark_list()
{
	mark_list_len = 0;
}

int depth = 0;
struct state *next(struct state *start, struct event *event)
{
	depth++;
	for (int ei = 0; ei < start->num_edges_in; ei++) {
		double t_max = start->edges_in[ei]->t_max_local;
		double t_min = start->edges_in[ei]->t_min_local;
		printf("Depth:%d\t\tTrying match:\tEdge:(%s [%lf,%lf])\t\tEvent:(%s,%lf)\n",
		       depth, start->edges_in[ei]->event, t_min, t_min,
		       event->event, event->event_time);
		fflush(stdout);
		if (strcmp(start->edges_in[ei]->event, event->event) == 0 &&
		    in_interval(t_max * 1.25, t_min * 0.75, event->event_time))
			return start->edges_in[ei]->dst;
	}

	return NULL;
}

char check(struct state *start, struct tlist *tlist, int start_event_idx)
{
	if (start == NULL || in_mark_list(start))
		return 0;
	mark_state(start);

	printf("----------\n");
	fflush(stdout);

	struct state *curr = start;
	for (int ti = start_event_idx; ti < tlist->len; ti++) {
		curr = next(curr, &tlist->trace_list[ti]);

		if (curr == NULL) {
			for (int ei = 0; ei < start->num_edges_in; ei++) {
				depth = 0;
				if (check(start->edges_in[ei]->dst, tlist,
					  start_event_idx))
					return 1;
			}
			return 0;
		}
	}

	return 1;
}

void offline_checker(char *automaton_path, struct event *traces, int num_traces)
{
	struct automaton automaton;
	struct edge edges[1000];
	struct state states[1000];

	automaton.edges = edges;
	automaton.states = states;
	automaton.start_state = 0;
	automaton.num_edges = 0;
	automaton.num_states = 0;
	read_file(automaton_path, &automaton);

	struct tlist tlist;
	for (int i = 0; i < num_traces; i++)
		add_trace(&tlist, traces[i]);

	int skipped_count = 0;
	for (skipped_count = 0; skipped_count < num_traces; skipped_count++) {
		depth = 0;
		if (check(automaton.start_state, &tlist, skipped_count))
			break;
		clear_mark_list();
	}

	clear_mark_list();
	printf("Num skipped: %d\n", skipped_count);

	clear_mark_list();
	free_tlist(&tlist);
	fflush(stdout);
}
