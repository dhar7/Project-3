#include "automaton.h"
#define PROB_RARE_LIMIT 0.80

struct formula {
	char *src_event;
	char *dst_event;

	double t_min;
	double t_max;

	char is_rare;
	double prob;

	struct state *src_state;
};

struct flist {
	int num_entries;
	struct formula *formula_list;
};

char interval_overlap(double t_min1, double t_max1, double t_min2,
		      double t_max2)
{
	if (t_min1 > t_max2 || t_min2 > t_max1)
		return 0;

	return 1;
}

char is_ambiguous(struct formula *formula, struct flist *flist)
{
	for (int i = 0; i < flist->num_entries; i++)
		if (strcmp(formula->src_event,
			   flist->formula_list[i].src_event) == 0 &&
		    strcmp(formula->dst_event,
			   flist->formula_list[i].dst_event) == 0 &&
		    interval_overlap(formula->t_min, formula->t_max,
				     flist->formula_list[i].t_min,
				     flist->formula_list[i].t_max))
			return 1;

	return 0;
}

void add_formula(struct formula *formula, struct flist *flist);

struct state *mark_list[100];
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

char disambiguate(struct formula *formula, struct flist *flist)
{
	if (!is_ambiguous(formula, flist) || formula->src_state == 0 ||
	    formula->src_state->num_edges_in == 0)
		return 1;

	struct formula new_formula;
	asprintf(&new_formula.dst_event, "G((%s) -> (F[%lf,%lf](%s)))",
		 formula->src_event, formula->t_min, formula->t_max,
		 formula->dst_event);
	new_formula.prob = formula->prob;
	new_formula.is_rare = formula->is_rare;

	for (int i = 0; i < formula->src_state->num_edges_in; i++) {
		asprintf(&new_formula.src_event, "%s",
			 formula->src_state->edges_in[i]->event);
		new_formula.src_state = formula->src_state->edges_in[i]->src;

		if (in_mark_list(new_formula.src_state))
			continue;
		mark_state(new_formula.src_state);

		new_formula.t_min =
			formula->src_state->edges_in[i]->t_min_local;
		new_formula.t_max =
			formula->src_state->edges_in[i]->t_max_local;
		new_formula.prob *= formula->src_state->edges_in[i]->prob;
		if (new_formula.prob < PROB_RARE_LIMIT)
			new_formula.is_rare = 1;

		add_formula(&new_formula, flist);
	}

	return 0;
}

void add_formula(struct formula *formula, struct flist *flist)
{
	if (!disambiguate(formula, flist))
		return;

	flist->formula_list =
		realloc(flist->formula_list,
			sizeof(struct formula) * (flist->num_entries + 1));

	memcpy(&flist->formula_list[flist->num_entries], formula,
	       sizeof(struct formula));
	asprintf(&flist->formula_list[flist->num_entries].src_event, "%s",
		 formula->src_event);
	asprintf(&flist->formula_list[flist->num_entries].dst_event, "%s",
		 formula->dst_event);

	flist->num_entries++;
	clear_mark_list();
}

void generate_mtl(struct automaton *automaton, struct flist *flist)
{
	for (int i = 0; i < automaton->num_edges; i++) {
		struct formula formula;
		asprintf(&formula.src_event, "%s", automaton->edges[i].event);
		formula.src_state = automaton->edges[i].src;

		for (int j = 0; j < automaton->edges[i].dst->num_edges_out;
		     j++) {
			asprintf(&formula.dst_event, "%s",
				 automaton->edges[i].dst->edges_out[j]->event);
			formula.t_min = automaton->edges[i]
						.dst->edges_out[j]
						->t_min_local;
			formula.t_max = automaton->edges[i]
						.dst->edges_out[j]
						->t_max_local;
			formula.prob =
				automaton->edges[i].dst->edges_out[j]->prob;
			if (formula.prob < PROB_RARE_LIMIT ||
			    automaton->edges[i].dst->in_rare_path) {
				formula.is_rare = 1;
				if (automaton->edges[i]
					    .dst->edges_out[j]
					    ->dst->num_edges_in == 1)
					automaton->edges[i]
						.dst->edges_out[j]
						->dst->in_rare_path = 1;
			} else {
				formula.is_rare = 0;
			}
			add_formula(&formula, flist);
		}
	}
}

void update_rarity(struct automaton *automaton, struct state *state)
{
	if (!automaton || !state)
		return;

	for (int i = 0; i < state->num_edges_in; i++) {
		if (state->edges_in[i]->src->in_rare_path ||
		    state->edges_in[i]->prob < PROB_RARE_LIMIT)
			state->in_rare_path = 1;
	}

	for (int i = 0; i < state->num_edges_out; i++)
		update_rarity(automaton, state->edges_out[i]->dst);
}

void print_flist(struct flist *flist)
{
	int rare_num = 0;
	for (int i = 0; i < flist->num_entries; i++) {
		printf("G((%s) -> (F[%lf,%lf](%s)))\tP: %lf Rare: %d\n",
		       flist->formula_list[i].src_event,
		       flist->formula_list[i].t_min,
		       flist->formula_list[i].t_max,
		       flist->formula_list[i].dst_event,
		       flist->formula_list[i].prob,
		       flist->formula_list[i].is_rare);
		if (flist->formula_list[i].is_rare)
			rare_num++;
	}

	printf("Total number of policies: %d\nTotal number of rare policies: %d",
	       flist->num_entries, rare_num);
}

void print_automaton(struct automaton *automaton)
{
	for (int i = 0; i < automaton->num_edges; i++) {
		printf("SRC: %s EVENT: %s START:%d\n",
		       automaton->edges[i].src->label,
		       automaton->edges[i].event,
		       automaton->edges[i].src->num_edges_in);
	}
}

int main(int argc, char *argv[])
{
	struct automaton automaton;
	struct edge edges[1000];
	struct state states[1000];

	automaton.edges = edges;
	automaton.states = states;
	automaton.start_state = 0;
	automaton.num_edges = 0;
	automaton.num_states = 0;
	read_file(argv[1], &automaton);

	struct flist flist;
	flist.formula_list = 0;
	flist.num_entries = 0;
	update_rarity(&automaton, automaton.start_state);
	generate_mtl(&automaton, &flist);
	print_flist(&flist);
	//print_automaton(&automaton);
}
