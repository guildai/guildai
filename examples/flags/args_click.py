from __future__ import print_function

import click

prefix = "Flags:"


@click.command()
@click.option("--i", type=int, default=1, help="sample int")
@click.option("--f", type=float, default=1.1, help="sample float")
@click.option("--b", is_flag=True, help="sample flag")
@click.option("--s", default="hello", help="sample string")
@click.option(
    "--c",
    "color",
    "-c",
    default="red",
    type=click.Choice(["red", "blue", "green"]),
    help="sample choices",
)
def main(i, f, b, s, color):
    print(prefix, i, f, b, s, color)


if __name__ == '__main__':
    main()
