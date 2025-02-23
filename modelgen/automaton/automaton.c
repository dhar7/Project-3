#include "automaton.h"

struct state *state_exists(char *label, struct automaton *automaton)
{
	if (!automaton || !label || automaton->num_states == 0 ||
	    !automaton->states)
		return 0;

	for (int i = 0; i < automaton->num_states; i++)
		if (strcmp(label, automaton->states[i].label) == 0)
			return &automaton->states[i];

	return 0;
}

struct state *add_state(char *label, struct automaton *automaton)
{
	struct state *state = NULL;
	if (!automaton || !label ||
	    (state = state_exists(label, automaton)) != 0)
		return state;

	automaton->start_state = &automaton->states[0];
	automaton->start_state->is_start = 1;

	automaton->states[automaton->num_states].num_edges_in = 0;
	automaton->states[automaton->num_states].edges_in = 0;
	automaton->states[automaton->num_states].num_edges_out = 0;
	automaton->states[automaton->num_states].edges_out = 0;
	strcpy(automaton->states[automaton->num_states].label, label);
	automaton->num_states++;

	return &automaton->states[automaton->num_states - 1];
}

void add_edge_to_state_list(struct edge *edge, struct state *state, char inout)
{
	if (!inout) {
		state->edges_in = realloc(state->edges_in,
					  sizeof(struct edge *) *
						  (state->num_edges_in + 1));

		state->edges_in[state->num_edges_in] = edge;
		state->num_edges_in++;
	} else {
		state->edges_out = realloc(state->edges_out,
					   sizeof(struct edge *) *
						   (state->num_edges_out + 1));

		state->edges_out[state->num_edges_out] = edge;
		state->num_edges_out++;
	}
}

void add_edge(char *src_label, char *dst_label, char *event, double t_min_local,
	      double t_max_local, double t_min_global, double t_max_global,
	      double prob, struct automaton *automaton)
{
	struct state *src = add_state(src_label, automaton);
	struct state *dst = add_state(dst_label, automaton);

	automaton->edges[automaton->num_edges].src = src;
	automaton->edges[automaton->num_edges].dst = dst;
	automaton->edges[automaton->num_edges].t_min_local = t_min_local;
	automaton->edges[automaton->num_edges].t_max_local = t_max_local;
	automaton->edges[automaton->num_edges].t_min_global = t_min_global;
	automaton->edges[automaton->num_edges].t_max_global = t_max_global;
	automaton->edges[automaton->num_edges].prob = prob;
	strcpy(automaton->edges[automaton->num_edges].event, event);
	add_edge_to_state_list(&automaton->edges[automaton->num_edges], src, 0);
	add_edge_to_state_list(&automaton->edges[automaton->num_edges], dst, 1);

	automaton->num_edges++;
}

void read_file(char *filename, struct automaton *automaton)
{
	FILE *fp;
	if ((fp = fopen(filename, "r")) == NULL) {
		fprintf(stderr, "Error: Cannot read file\n");
		return;
	}

	while (!feof(fp)) {
		char src_label[10];
		char dst_label[10];
		char event[1024];
		double t_min_local;
		double t_max_local;
		double t_min_global;
		double t_max_global;
		double prob;
		fscanf(fp,
		       "%s -> %s [label=\"%s [%lf, %lf] t[%lf, %lf] p=%lf\"]",
		       src_label, dst_label, event, &t_min_local, &t_max_local,
		       &t_min_global, &t_max_global, &prob);

		//printf("SRC: %s\nDST: %s\nEVENT: %s\nLOCAL_T: (%lf, %lf)\nGLOBAL_T:(%lf, %lf)\nPROB: %lf\n",
		//       src_label, dst_label, event, t_min_local, t_max_local,
		//       t_min_global, t_max_global, prob);

		add_edge(src_label, dst_label, event, t_min_local, t_max_local,
			 t_min_global, t_max_global, prob, automaton);
	}
}
