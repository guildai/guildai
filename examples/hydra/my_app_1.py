from omegaconf import DictConfig, OmegaConf
import hydra


@hydra.main()
def my_app(cfg):
    print(OmegaConf.to_yaml(cfg))


if __name__ == "__main__":
    my_app()
