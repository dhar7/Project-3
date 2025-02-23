import sys
import dill as pickle

if sys.argv[1] == "ft":
    from dataset.fischertechnik.prep import read_file
elif sys.argv[1] == "autotap":
    from dataset.autotap.prep import read_file

if __name__ == "__main__":
    filename = sys.argv[2]
    raw_sequence = read_file(filename)
    with open(sys.argv[3], "wb+") as f:
        pickle.dump(raw_sequence, f)
