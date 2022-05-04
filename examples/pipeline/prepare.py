# License: BSD
# Author: Sasank Chilamkurthy
# Ref: https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html

import os

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

import torch

import torchvision
from torchvision import datasets, transforms

from util import imshow

# Data augmentation and normalization for training
# Just normalization for validation
data_transforms = {
    'train': transforms.Compose(
        [
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
    'val': transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
}

data_dir = 'data/hymenoptera_data'
image_datasets = {
    x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x])
    for x in ['train', 'val']
}
dataloaders = {
    x: torch.utils.data.DataLoader(
        image_datasets[x], batch_size=4, shuffle=True, num_workers=4
    )
    for x in ['train', 'val']
}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
class_names = image_datasets['train'].classes

# Get a batch of training data
inputs, classes = next(iter(dataloaders['train']))

# Make a grid from batch
out = torchvision.utils.make_grid(inputs)

print("Saving sample images prepare-samples.png")
imshow(out, title=[class_names[x] for x in classes])
plt.savefig("prepare-samples.png")

for name, dataloader in dataloaders.items():
    print("Saving data %s.pth" % name)
    torch.save(dataloader, '%s.pth' % name)
