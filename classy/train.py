# -*- coding: utf-8 -*-
from __future__ import print_function

import argparse
import matplotlib
from matplotlib import pyplot as plt
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable

from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import torch.optim.lr_scheduler as sch
import torch.nn.functional as F

import os, sys
from skimage import io

from PIL import Image
import time

from models import ResNet18_pretrained, ResNet50_pretrained, ResNet152_pretrained, ResNeXt101_pretrained, wide_resnet101_pretrained, inception_v3_pretrained, AlexNet_pretrained, SqueezeNet_pretrained, VGGNet_pretrained, DenseNet_pretrained, efficientnet_b7_pretrained, regnet_x_32gf_pretrained
from dataset import read_dataset
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--network',
    choices=['resnet18', 'resnet50', 'resnet152', 'resnext101', 'wide_resnet101', 'inception_v3', 'alexnet', 'squeezenet', 'vggnet', 'densenet', 'efficientnet_b7', 'regnet_x_32gf'], default='resnet18',
    help='Choose which neural network to use')
args = parser.parse_args()
network = args.network

## TRAIN PARAMS
n_classes = 2
L2_weight_decay = 1e-5
batch_size = 5  # use 10 if enough memory
num_epochs = 10
lr = 0.001
momentum = 0.9

results_dir = 'results'
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

############ training ############
## LOG
weight_out_dir = (args.network + '_weights')
use_gpu = torch.cuda.is_available()

class_weights = None
if use_gpu and class_weights is not None:
    class_weights = class_weights.cuda().float()


def main():
    # model
    if args.network == 'resnet18':
        model = ResNet18_pretrained(n_classes, freeze=False)
        print('model is resnet18')
    elif args.network == 'resnet50':
        model = ResNet50_pretrained(n_classes, freeze=False)
        print('model is resnet50')
    elif args.network == 'resnet152':
        model = ResNet152_pretrained(n_classes, freeze=False)
        print('model is resnet152')
    elif args.network == 'resnext101':
        model = ResNeXt101_pretrained(n_classes, freeze=False)
        print('model is resnext101')
    elif args.network == 'wide_resnet101':
        model = wide_resnet101_pretrained(n_classes, freeze=False)
        print('model is wide_resnet101')
    elif args.network == 'inception_v3':
        model = inception_v3_pretrained(n_classes, freeze=False)
        print('model is inception_v3')
    elif args.network == 'alexnet':
        model = AlexNet_pretrained(n_classes, freeze=False)
        print('model is alexnet')
    elif args.network == 'squeezenet':
        model = SqueezeNet_pretrained(n_classes, freeze=False)
        print('model is squeezenet')
    elif args.network == 'vggnet':
        model = VGGNet_pretrained(n_classes, freeze=False)
        print('model is vggnet')
    elif args.network == 'densenet':
        model = DenseNet_pretrained(n_classes, freeze=False)
        print('model is densenet')
    elif args.network == 'efficientnet_b7':
        model = efficientnet_b7_pretrained(n_classes, freeze=False)
        print('model is efficientnet_b7')
    elif args.network == 'regnet_x_32gf':
        model = regnet_x_32gf_pretrained(n_classes, freeze=False)
        print('model is regnet_x_32gf')

    ## LOSS PARAMETER
    criterion = nn.CrossEntropyLoss(weight=class_weights) # equivalent to NLL Loss + softmax = cross entropy
    print("Starting!")
    if use_gpu:
        print("Using " + str(torch.cuda.device_count()) + " GPU(s)")
        if torch.cuda.device_count() > 1:
            gpu_ids = list(range(torch.cuda.device_count()))
            model = nn.DataParallel(model, device_ids=gpu_ids).cuda()
        else:
            model = model.cuda()
        criterion = criterion.cuda()
    sys.stdout.flush()

    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=momentum, weight_decay=L2_weight_decay)
    # optimizer = torch.optim.SGD(model.fc.parameters(), lr=lr, momentum=momentum, weight_decay=L2_weight_decay)
    # optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=L2_weight_decay)
    # optimizer = torch.optim.Adam(model.fc.parameters(),lr=lr,weight_decay=L2_weight_decay)
    # optimizer = torch.optim.Adam(model.classifier.parameters(), lr=lr, weight_decay=L2_weight_decay)
    exp_lr_scheduler = sch.StepLR(optimizer, step_size=50, gamma=0.1)

    model = train_model(model, criterion, optimizer, exp_lr_scheduler, network, num_epochs=num_epochs)


def train_model(model, criterion, optimizer, scheduler, network, num_epochs=num_epochs):
    if args.network == 'resnet18' or args.network == 'resnet50'or args.network == 'resnet152' or args.network == 'resnext101' or args.network == 'wide_resnet101' or args.network == 'alexnet' or args.network == 'squeezenet' or args.network == 'vggnet' or args.network == 'densenet' or args.network == 'efficientnet_b7' or args.network == 'regnet_x_32gf':
        train_data_transform = transforms.Compose([
            transforms.ToPILImage(),
            # transforms.Resize((256, 256)),
            transforms.Resize((224, 224)),
            transforms.RandomRotation((-5, +5)),
            # transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(),
            # transforms.RandomVerticalFlip(),
            transforms.ColorJitter(brightness=0.25),
            transforms.ToTensor(),
            # transforms.Normalize(mean=[0.485, 0.456, 0.406],
            #                      std=[0.229, 0.224, 0.225]),
            # transforms.Normalize(mean=[0.4059296, 0.40955055, 0.412535],
            #                      std=[0.21329397, 0.215493, 0.21677108]),
        ])
        val_data_transform = transforms.Compose([
            transforms.ToPILImage(),
            #transforms.Resize((256, 256)),
            transforms.Resize((224, 224)),
            #transforms.CenterCrop(224),
            transforms.ToTensor(),
            # transforms.Normalize(mean=[0.485, 0.456, 0.406],
            #                      std=[0.229, 0.224, 0.225]),
            # transforms.Normalize(mean=[0.4059296, 0.40955055, 0.412535],
            #                      std=[0.21329397, 0.215493, 0.21677108]),
        ])
    elif args.network == 'inception_v3':
        train_data_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((300, 300)),
            transforms.RandomRotation((-5, +5)),
            # transforms.RandomCrop(299),
            transforms.RandomHorizontalFlip(),
            # transforms.RandomVerticalFlip(),
            transforms.ColorJitter(brightness=0.25),
            transforms.ToTensor(),
            # transforms.Normalize(mean=[0.485, 0.456, 0.406],
            #                      std=[0.229, 0.224, 0.225]),
            # transforms.Normalize(mean=[0.4059296, 0.40955055, 0.412535],
            #                      std=[0.21329397, 0.215493, 0.21677108]),
        ])
        val_data_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((300, 300)),
            # transforms.CenterCrop(299),
            transforms.ToTensor(),
            # transforms.Normalize(mean=[0.485, 0.456, 0.406],
            #                      std=[0.229, 0.224, 0.225]),
            # transforms.Normalize(mean=[0.4059296, 0.40955055, 0.412535],
            #                      std=[0.21329397, 0.215493, 0.21677108]),
        ])

    radio_train = read_dataset(mode='train', transform=train_data_transform)
    radio_val = read_dataset(mode='val', transform=val_data_transform)

    dataloaders = {
        'train': DataLoader(radio_train, batch_size=batch_size, shuffle=True, num_workers=2),
        'val': DataLoader(radio_val, batch_size=batch_size, shuffle=True, num_workers=2)
    }

    ##### TRAIN ROUTINE
    output = open(os.path.join(results_dir, network + '_train_result.txt'), 'w')
    since = time.time()
    best_model_wts = model.state_dict()
    best_acc = 0.0

    if not os.path.exists('weights/' + weight_out_dir):
        os.makedirs('weights/' + weight_out_dir)
    LOG_FILE = open('weights/' + weight_out_dir + '/LOG.txt', 'w')

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)
        output.write('Epoch {}/{}'.format(epoch, num_epochs - 1) + "\n")
        output.write('-' * 10 + "\n")

        epoch_info = [0] * 4
        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train(True)  # Set model to training mode
            else:
                model.train(False)  # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            count = 0
            dataset_size = len(dataloaders[phase])

            for data in dataloaders[phase]:
                # get the inputs
                inputs, labels, filenames = data
                if use_gpu:
                    inputs = Variable(inputs.cuda()).float()
                    labels = Variable(labels.cuda()).long()
                else:
                    inputs = Variable(inputs).float()
                    labels = Variable(labels).long()

                # increment the count
                count += 1

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                outputs = model(inputs)

                # for nets that have multiple outputs such as inception
                if isinstance(outputs, tuple):
                    _, preds = torch.max(outputs[0].data, 1)
                    loss = sum((criterion(o, labels) for o in outputs))
                else:
                    _, preds = torch.max(outputs.data, 1)
                    loss = criterion(outputs, labels)

                # backward + optimize only if in training phase
                if phase == 'train':
                    loss.backward()
                    optimizer.step()

                # statistics
                running_loss += loss.data.item()  # Added tensor.item to convert to Python scalar
                running_corrects += torch.sum(preds == labels.data)

                print('{:d}/{:d}:  {:s}_loss: {:.3f}, {:s}_acc: {:.3f} \r'.format(batch_size * count,
                                                                                  batch_size * dataset_size,
                                                                                  phase,
                                                                                  running_loss / count,
                                                                                  phase,
                                                                                  torch.div(running_corrects, count*batch_size, rounding_mode='floor')),
                      end='\r')
                output.write('{:d}/{:d}:  {:s}_loss: {:.3f}, {:s}_acc: {:.3f} \r'.format(batch_size * count,
                                                                                  batch_size * dataset_size,
                                                                                  phase,
                                                                                  running_loss / count,
                                                                                  phase,
                                                                                  torch.div(running_corrects, count*batch_size, rounding_mode='floor'))
                             )
                sys.stdout.flush()

            # scheduler used to be before model.train(True) at beginning of this for loop. moved here for pytorch 1.1.0 (put after optimizer)
            if phase == 'train':
                scheduler.step()
            
            epoch_loss = running_loss / dataset_size
            epoch_acc = float(running_corrects) / (count * batch_size)

            print('---------  {} Loss: {:.4f} Acc: {:.4f} -----------'.format(phase, epoch_loss, epoch_acc))
            output.write('---------  {} Loss: {:.4f} Acc: {:.4f} -----------'.format(phase, epoch_loss, epoch_acc) + "\n")

            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = model.state_dict()
                torch.save(best_model_wts, 'weights/' + weight_out_dir + '/{:03d}_{:.3f}.pkl'.format(epoch, epoch_acc))
            if phase == 'train':
                epoch_info[0] = epoch_loss
                epoch_info[1] = epoch_acc
            else:
                epoch_info[2] = epoch_loss
                epoch_info[3] = epoch_acc
        LOG_FILE.write(str(epoch_info[0]) + ' ' + str(epoch_info[1]) + ' ' + str(epoch_info[2])
                       + ' ' + str(epoch_info[3]) + '\n')
        print()
    LOG_FILE.close()
    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))
    output.write('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    output.write('Best val Acc: {:4f}'.format(best_acc))
    output.close()

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model


if __name__ == '__main__':
    main()
