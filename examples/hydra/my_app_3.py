import shlex
import sys

from omegaconf import DictConfig, OmegaConf
import hydra


@hydra.main(version_base=None, config_path="conf")
def my_app(cfg):
    print(OmegaConf.to_yaml(cfg))


if __name__ == "__main__":
    # Apply two args: db and db config (shlex encoded) to sys.argv to
    # be handled by Hydra
    db, db_config = sys.argv[1:]
    sys.argv[1:] = [f"+db={db}"] + shlex.split(db_config)
    my_app()
