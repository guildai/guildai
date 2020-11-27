import argparse


def main():
    args = _init_args()
    print(args)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "data-csv",
        metavar="DATA_DIR",
        help="Directory containing data to generate stats for.",
    )
    return p.parse_args()


if __name__ == "__main__":
    main()
