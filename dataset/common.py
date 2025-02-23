# if __name__ == "__main__":
#    parser = argparse.ArgumentParser()
#    parser.add_argument("--input", nargs="*", required=True)
#    parser.add_argument("--output", required=True)
#    parser.add_argument("--ignore", required=False)
#    parser.add_argument("--test", required=True)
#    parser.add_argument("--serialize", required=False)
#    args = parser.parse_args()
#
#    tslist = extract(
#        read_file, args.input, args.test, args.ignore, naive=True, merge_diff=True
#    )  # "Unknown_motion"
#
#    outfile = open(args.output, "w")
#    outfile.write("\n".join(filter(None, tslist)))

from dataclasses import dataclass


@dataclass(frozen=False)
class Event:
    event_time: int  # Relative to the beginning
    sensor_id: str | list
    value: str | float | list
