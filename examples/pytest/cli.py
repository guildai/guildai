import pickle
import click
import demo

@click.group()
def cli():
    pass

@cli.command()
@click.option("--data-path", default="data.pkl")
@click.option("--random-state", type=click.INT, default=0)
def prepare_data(data_path, random_state):
    click.echo("Preparing data with random state %i" % random_state, err=True)
    data = demo.prepare_data(random_state)
    click.echo("Saving prepared data to %s" % data_path, err=True)
    pickle.dump(data, open(data_path, "wb"))

@cli.command()
@click.option("--data-path", default="data.pkl")
@click.option("--transformed-path", default="transformed.pkl")
@click.option("--random-state", type=click.INT, default=0)
def transform(data_path, transformed_path, random_state):
    click.echo("Loading prepared data from %s" % data_path, err=True)
    train, test, _, _ = pickle.load(open(data_path, "rb"))
    click.echo("Transforming data with random state %i" % random_state)
    transformed = demo.transform(train, test, random_state)
    click.echo("Saving transformed data to %s" % transformed_path)
    pickle.dump(transformed, open(transformed_path, "wb"))

if __name__ == "__main__":
    cli()
