#ifndef __AUTOMATON__
#define __AUTOMATON__
#define _GNU_SOURCE

#include <string.h>
#include <stdlib.h>
#include <stdio.h>

struct automaton {
	struct state *start_state;

	int num_states;
	struct state *states;

	int num_edges;
	struct edge *edges;
};

struct state {
	int num_edges_out;
	struct edge **edges_out;

	int num_edges_in;
	struct edge **edges_in;

	char is_start;
	char is_term;

	char label[16];
	char in_rare_path;
};

struct edge {
	struct state *src;
	struct state *dst;

	double t_min_local;
	double t_max_local;

	double t_min_global;
	double t_max_global;

	double prob;
	char event[1024];
};

void read_file(char *filename, struct automaton *automaton);

#endif
