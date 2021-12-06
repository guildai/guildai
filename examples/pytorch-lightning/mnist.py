import os
import argparse

import torch

from torch import nn
from torch.nn import functional as F
from torch.optim import Adam
from torch.utils.data import DataLoader, random_split

from torchvision import datasets, transforms
from torchvision.datasets import MNIST

from pytorch_lightning import Trainer
from pytorch_lightning.core.lightning import LightningModule


class LitMNIST(LightningModule):
    def __init__(self, args):
        super().__init__()

        self.args = args

        # mnist images are (1, 28, 28) (channels, height, width)
        self.layer_1 = nn.Linear(28 * 28, 128)
        self.layer_2 = nn.Linear(128, 256)
        self.layer_3 = nn.Linear(256, 10)

    def forward(self, x):
        batch_size, channels, height, width = x.size()

        # (b, 1, 28, 28) -> (b, 1*28*28)
        x = x.view(batch_size, -1)
        x = self.layer_1(x)
        x = F.relu(x)
        x = self.layer_2(x)
        x = F.relu(x)
        x = self.layer_3(x)

        x = F.log_softmax(x, dim=1)
        return x

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = F.nll_loss(logits, y)
        self.log(
            "my_loss", loss, on_step=True, on_epoch=True, prog_bar=True, logger=True
        )
        return loss

    def configure_optimizers(self):
        return Adam(self.parameters(), lr=self.args.lr)

    @staticmethod
    def add_model_specific_args(parent_parser):
        parser = parent_parser.add_argument_group("LitModel")
        parser.add_argument(
            "--lr",
            type=float,
            default=1e-3,
            help="Learning rate for the Adam optimizer",
        )
        return parent_parser


parser = LitMNIST.add_model_specific_args(argparse.ArgumentParser())
parser = Trainer.add_argparse_args(parser)
args = parser.parse_args()

transform = transforms.Compose(
    [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
)

mnist_train = MNIST(os.getcwd(), train=True, download=True, transform=transform)
mnist_train = DataLoader(mnist_train, batch_size=64)

model = LitMNIST(args)
trainer = Trainer.from_argparse_args(args)
trainer.fit(model, mnist_train)
