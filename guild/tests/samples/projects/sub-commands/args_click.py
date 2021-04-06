import click


@click.group()
@click.option("--base-foo", default=4, type=int)
def cli(base_foo):
    print("base-foo=%i" % base_foo)


@cli.command()
@click.option("--a-foo", default=5, type=int)
def a(a_foo):
    print("a-foo=%i" % a_foo)


@cli.group()
@click.option("--b-foo", default=6, type=int)
def b(b_foo):
    print("b-foo=%i" % b_foo)


@b.command()
@click.option("--b-sub-foo", default=7, type=int)
def b_sub(b_sub_foo):
    print("b-sub-f=%i" % b_sub_foo)


cli()
