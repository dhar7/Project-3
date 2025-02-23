all:
	gcc -g -fPIC -Wall -Werror -Wextra -pedantic digital_twin.c -I../automaton/ ../automaton/automaton.c -shared -o ta_checker.so
clean:
	rm -rf ta_checker.so
