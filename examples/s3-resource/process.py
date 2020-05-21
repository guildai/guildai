import os

import click
import pandas


@click.command()
@click.option(
    "--input-dir", metavar="DIR", default=".", help="Path to scan for raw data."
)
@click.option(
    "--output-dir",
    metavar="DIR",
    default=".",
    help="Path under which to save processed data.",
)
def process(input_dir, output_dir):
    for root, _dirs, names in os.walk(input_dir, followlinks=True):
        for name in names:
            if name.endswith(".csv"):
                input_path = os.path.join(root, name)
                df = pandas.read_csv(input_path)
                output_name = name + ".pkl"
                output_path = os.path.join(output_dir, output_name)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                print("Converting %s to %s" % (input_path, output_path))
                df.to_pickle(output_path)


if __name__ == "__main__":
    process()
