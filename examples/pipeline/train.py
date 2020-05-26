# License: BSD
# Author: Sasank Chilamkurthy
# Ref: https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html

import copy
import time

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt

import torch
import torch.nn as nn

import torch.optim as optim
from torch.optim import lr_scheduler

from torchvision import models

from util import imshow

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
dataloaders = {x: torch.load("%s.pth" % x) for x in ['train', 'val']}
dataset_sizes = {x: len(dataloaders[x].dataset) for x in ['train', 'val']}
class_names = dataloaders['train'].dataset.classes

# Hyperparameters
train_epochs = 25
freeze_layers = False
lr = 0.001
momentum = 0.9
lr_decay_epochs = 7
lr_decay_gamma = 0.1


def train_model(model, criterion, optimizer, scheduler, num_epochs=25):
    since = time.time()

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()  # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            if phase == 'train':
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

        print()

    time_elapsed = time.time() - since
    print(
        'Training complete in {:.0f}m {:.0f}s'.format(
            time_elapsed // 60, time_elapsed % 60
        )
    )
    print('Best val Acc: {:4f}'.format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model


def visualize_model(model, num_images=6):
    was_training = model.training
    model.eval()
    images_so_far = 0
    fig = plt.figure()

    with torch.no_grad():
        for i, (inputs, labels) in enumerate(dataloaders['val']):
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            for j in range(inputs.size()[0]):
                images_so_far += 1
                ax = plt.subplot(num_images // 2, 2, images_so_far)
                ax.axis('off')
                ax.set_title('predicted: {}'.format(class_names[preds[j]]))
                imshow(inputs.cpu().data[j])
                if images_so_far == num_images:
                    model.train(mode=was_training)
                    return
        model.train(mode=was_training)


model = models.resnet18(pretrained=True)
if freeze_layers:
    for param in model.parameters():
        param.requires_grad = False
num_ftrs = model.fc.in_features
# Here the size of each output sample is set to 2.
# Alternatively, it can be generalized to nn.Linear(num_ftrs, len(class_names)).
model.fc = nn.Linear(num_ftrs, 2)

model = model.to(device)

criterion = nn.CrossEntropyLoss()

# Observe that all parameters are being optimized
if freeze_layers:
    params = model.fc.parameters()
else:
    params = model.parameters()
optimizer = optim.SGD(params, lr=lr, momentum=momentum)

# Decay LR by a factor of lr_decay_gamma every lr_decay_epochs
exp_lr_scheduler = lr_scheduler.StepLR(
    optimizer, step_size=lr_decay_epochs, gamma=lr_decay_gamma
)

model = train_model(
    model, criterion, optimizer, exp_lr_scheduler, num_epochs=train_epochs
)

print("Saving trained model model.pth")
torch.save(model.state_dict(), "model.pth")

print("Saving sample images predict-samples.png")
visualize_model(model)
plt.savefig("predict-samples.png")
