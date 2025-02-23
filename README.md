# AutoGen

## Installing dependencies:
Install [pipenv](https://pipenv.pypa.io/en/latest/) and run:
```
pipenv install
```

## Usage:
To start the virtual environment run:
```
pipenv shell
```

### Evaluation
```
python eval.py --dataset <autotap,ft> --logfile <log dirname>
```

### Anomaly detection:
```
python detect.py --metric <metric pickle> --period <event periods pickle> --all-contexts <event contexts pickle> --ta <timed automaton> --trace <trace pickle> --context <event context> --search-view <optional>
```

Metric, period and all-contexts can be found in the `out/<log dirname>`.

To obtain the trace pickle, run:
```
python prep.py <autotap,ft> <path to raw trace> <output file>
```
