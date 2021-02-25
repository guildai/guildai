from omegaconf import DictConfig, OmegaConf
import hydra

@hydra.main(config_path='conf')
def my_app(cfg):
    print(OmegaConf.to_yaml(cfg))

def _apply_argparse_cli():
    import argparse, sys
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="mysql")
    p.add_argument("--db-config", nargs="*", default=[])
    args = p.parse_args()
    sys.argv[1:] = ["+db=%s" % args.db] + args.db_config

if __name__ == "__main__":
    _apply_argparse_cli()
    my_app()
