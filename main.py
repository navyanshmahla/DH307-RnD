# -*- coding: utf-8 -*-
"""main.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BrpyKhVAwWCSMFiHq8ijMFd9-8pUO2vV
"""

# Commented out IPython magic to ensure Python compatibility.
from __future__ import print_function
import argparse
import random
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.optim as optim
import torch.utils.data
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils
from torch.autograd import Variable
import os
import json
import numpy as np
import models.dcgan as dcgan
import models.mlp as mlp

def avg_feature_rep(i,gen_models,num_classes=2,k=20):
  total_logits = torch.zeros((num_classes,int(imageSize/2),int(imageSize/2))).cuda()
  #count = torch.zeros(num_classes, device=device)
  for j,model in enumerate(gen_models):
    if(j!=i):
      for label in range(num_classes):
        z=Variable(torch.randn(k, nz,1,1)).cuda()
        fake_labels=Variable(torch.LongTensor(k,1,1,1).fill_(label)).cuda()
        logits = torch.mean(model.forward(z,fake_labels),dim=-1)
        total_logits[label] = torch.mean(logits,dim=0)
  return total_logits

if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--datasetA', required=True, help='cifar10 | lsun | imagenet | folder | lfw ')
    parser.add_argument('--datasetB', required=True, help='cifar10 | lsun | imagenet | folder | lfw ')
    parser.add_argument('--datarootA', required=True, help='path to dataset A')
    parser.add_argument('--datarootB', required=True, help='path to dataset B')
    parser.add_argument('--workers', type=int, help='number of data loading workers', default=8)
    parser.add_argument('--batchSize', type=int, default=128, help='input batch size')
    parser.add_argument('--imageSize', type=int, default=64, help='the height / width of the input image to network')
    parser.add_argument('--nc', type=int, default=3, help='input image channels')
    parser.add_argument('--nz', type=int, default=100, help='size of the latent z vector')
    parser.add_argument('--ngf', type=int, default=64)
    parser.add_argument('--ndf', type=int, default=64)
    parser.add_argument('--niter1', type=int, default=25, help='number of epochs to train for burnout')
    parser.add_argument('--niter2', type=int, default=25, help='number of epochs to train for codistillation')
    parser.add_argument('--num_classes', type=int, default=25, help='number of classes in data')
    parser.add_argument('--num_clients', type=int, default=25, help='number of clients')
    parser.add_argument('--lrD', type=float, default=0.00005, help='learning rate for Critic, default=0.00005')
    parser.add_argument('--lrG', type=float, default=0.00005, help='learning rate for Generator, default=0.00005')
    parser.add_argument('--beta1', type=float, default=0.5, help='beta1 for adam. default=0.5')
    parser.add_argument('--cuda'  , action='store_true', help='enables cuda')
    parser.add_argument('--ngpu'  , type=int, default=1, help='number of GPUs to use')
    parser.add_argument('--netG', default='', help="path to netG (to continue training)")
    parser.add_argument('--netD', default='', help="path to netD (to continue training)")
    parser.add_argument('--clamp_lower', type=float, default=-0.01)
    parser.add_argument('--clamp_upper', type=float, default=0.01)
    parser.add_argument('--Diters', type=int, default=5, help='number of D iters per each G iter')
    parser.add_argument('--noBN', action='store_true', help='use batchnorm or not (only for DCGAN)')
    parser.add_argument('--mlp_G', action='store_true', help='use MLP for G')
    parser.add_argument('--mlp_D', action='store_true', help='use MLP for D')
    parser.add_argument('--n_extra_layers', type=int, default=0, help='Number of extra layers on gen and disc')
    parser.add_argument('--experiment', default=None, help='Where to store samples and models')
    parser.add_argument('--adam', action='store_true', help='Whether to use adam (default is rmsprop)')
    opt = parser.parse_args()
    print(opt)

    if opt.experiment is None:
        opt.experiment = 'samples'
    os.system('mkdir {0}'.format(opt.experiment+"0"))
    os.system('mkdir {0}'.format(opt.experiment+"1"))
    opt.manualSeed = random.randint(1, 10000) # fix seed
    print("Random Seed: ", opt.manualSeed)
    random.seed(opt.manualSeed)
    torch.manual_seed(opt.manualSeed)

    cudnn.benchmark = True

    if torch.cuda.is_available() and not opt.cuda:
        print("WARNING: You have a CUDA device, so you should probably run with --cuda")

    if opt.datasetA in ['imagenet', 'folder', 'lfw']:
        # folder dataset
        datasetA = dset.ImageFolder(root=opt.datarootA,
                                transform=transforms.Compose([
                                    transforms.Resize(opt.imageSize),
                                    transforms.CenterCrop(opt.imageSize),
                                    transforms.ToTensor(),
                                    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                                ]))
        assert datasetA
	
    elif opt.datasetA == 'lsun':
        datasetA = dset.LSUN(db_path=opt.datarootA, classes=['bedroom_train'],
                            transform=transforms.Compose([
                                transforms.Resize(opt.imageSize),
                                transforms.CenterCrop(opt.imageSize),
                                transforms.ToTensor(),
                                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                            ]))
        assert datasetA
    elif opt.datasetA == 'cifar10':
        datasetA = dset.CIFAR10(root=opt.datarootA, download=True,
                            transform=transforms.Compose([
                                transforms.Resize(opt.imageSize),
                                transforms.ToTensor(),
                                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                            ])
        )
        assert datasetA
    
    dataloaderA = torch.utils.data.DataLoader(datasetA, batch_size=opt.batchSize,
                                            shuffle=True, num_workers=int(opt.workers))



    if opt.datasetB in ['imagenet', 'folder', 'lfw']:
        # folder dataset
        datasetB = dset.ImageFolder(root=opt.datarootB,
                                transform=transforms.Compose([
                                    transforms.Resize(opt.imageSize),
                                    transforms.CenterCrop(opt.imageSize),
                                    transforms.ToTensor(),
                                    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                                ]))
        assert datasetB
    elif opt.datasetB == 'lsun':
        datasetB = dset.LSUN(db_path=opt.datarootB, classes=['bedroom_train'],
                            transform=transforms.Compose([
                                transforms.Resize(opt.imageSize),
                                transforms.CenterCrop(opt.imageSize),
                                transforms.ToTensor(),
                                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                            ]))
        assert datasetB
    elif opt.datasetB == 'cifar10':
        datasetB = dset.CIFAR10(root=opt.datarootB, download=True,
                            transform=transforms.Compose([
                                transforms.Resize(opt.imageSize),
                                transforms.ToTensor(),
                                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                            ])
        )
        assert datasetB
    
    dataloaderB = torch.utils.data.DataLoader(datasetB, batch_size=opt.batchSize,
                                            shuffle=True, num_workers=int(opt.workers))
    dataloaders=[dataloaderA,dataloaderB]
    ngpu = int(opt.ngpu)
    nz = int(opt.nz)
    ngf = int(opt.ngf)
    ndf = int(opt.ndf)
    nc = int(opt.nc)
    imageSize=int(opt.imageSize)
    batchSize=int(opt.batchSize)
    n_extra_layers = int(opt.n_extra_layers)
    num_clients=int(opt.num_clients)
    num_classes=int(opt.num_classes)
    # write out generator config to generate images together wth training checkpoints (.pth)
    # generator_config = {"imageSize": opt.imageSize, "nz": nz,"num_classes":num_classes, "nc": nc, "ngf": ngf, "ngpu": ngpu, "n_extra_layers": n_extra_layers, "noBN": opt.noBN, "mlp_G": opt.mlp_G}
    # with open(os.path.join(opt.experiment, "generator_config.json"), 'w') as gcfg:
    #     gcfg.write(json.dumps(generator_config)+"\n")

    # custom weights initialization called on netG and netD
    def weights_init(m):
        classname = m.__class__.__name__
        if classname.find('Conv') != -1:
            m.weight.data.normal_(0.0, 0.02)
        elif classname.find('BatchNorm') != -1:
            m.weight.data.normal_(1.0, 0.02)
            m.bias.data.fill_(0)

    if opt.noBN:
        gen_models=[dcgan.DCGAN_G(imageSize, nz, num_classes,nc, ngf, ngpu, n_extra_layers) for i in range(num_clients)]

    elif opt.mlp_G:
        gen_models=[mlp.MLP_G(opt.imageSize, nz, nc, ngf, ngpu) for i in range(num_clients)]

    else:
        gen_models=[dcgan.DCGAN_G(imageSize, nz, num_classes,nc, ngf, ngpu, n_extra_layers) for i in range(num_clients)]


    # write out generator config to generate images together wth training checkpoints (.pth)
    # generator_config = {"imageSize": opt.imageSize, "nz": nz,"num_classes":num_classes, "nc": nc, "ngf": ngf, "ngpu": ngpu, "n_extra_layers": n_extra_layers, "noBN": opt.noBN, "mlp_G": opt.mlp_G}
    # with open(os.path.join(opt.experiment, "generator_config.json"), 'w') as gcfg:
    #     gcfg.write(json.dumps(generator_config)+"\n")

    for netG in gen_models:
        netG.apply(weights_init)
        # if opt.netG != '': # load checkpoint if needed
        #     netG.load_state_dict(torch.load(opt.netG))
        print(netG)

    if opt.mlp_D:
        disc_models= [mlp.MLP_D(opt.imageSize, nz, nc, ndf, ngpu) for i in range(num_clients)]
    else:
        disc_models= [dcgan.DCGAN_D(imageSize, nz,num_classes, nc, ndf, ngpu, n_extra_layers) for i in range(num_clients)]

    for netD in disc_models:
        netD.apply(weights_init)
        # if opt.netD != '':
        #     netD.load_state_dict(torch.load(opt.netD))

    input = torch.FloatTensor(batchSize, 3, imageSize, imageSize)
    noise = torch.FloatTensor(batchSize, nz, 1, 1)
    fixed_noise = torch.FloatTensor(batchSize, nz, 1, 1).normal_(0, 1)
    one = torch.FloatTensor([1])
    mone = one * -1




    if opt.cuda:
        for netD in disc_models:
            netD.cuda()
        for netG in gen_models:
            netG.cuda()
        input = input.cuda()
        one, mone = one.cuda(), mone.cuda()
        noise, fixed_noise = noise.cuda(), fixed_noise.cuda()

    # setup optimizer
    if opt.adam:
        disc_optimizers = [optim.Adam(model.parameters(), lr=opt.lrD, betas=(opt.beta1, 0.999)) for model in disc_models]
        optimizerG = [optim.Adam(model.parameters(), lr=opt.lrG, betas=(opt.beta1, 0.999)) for model in gen_models ]
    else:
        disc_optimizers = [optim.RMSprop(model.parameters(), lr = opt.lrD) for model in disc_models]
        gen_optimizers = [optim.RMSprop(model.parameters(), lr = opt.lrG) for model in gen_models]


    #burnout
    gen_iterations=0
    for epoch in range(opt.niter1):
        for i in range(num_clients):
            data_iter = iter(dataloaders[i])
            count = 0
            netD=disc_models[i]
            netG=gen_models[i]
            optimizerD=disc_optimizers[i]
            optimizerG=gen_optimizers[i]
            while count < len(dataloaders[i]):
                ############################
                # (1) Update D network
                ###########################
                for p in netD.parameters(): # reset requires_grad
                    p.requires_grad = True # they are set to False below in netG update

                # train the discriminator Diters times
                if gen_iterations < 25 or gen_iterations % 500 == 0:
                    Diters = 100
                else:
                    Diters = opt.Diters
                j = 0
                while j < Diters and count < len(dataloaders[i]):
                    j += 1

                    # clamp parameters to a cube
                    for p in netD.parameters():
                        p.data.clamp_(opt.clamp_lower, opt.clamp_upper)

                    # data = data_iter.next()
                    data = next(data_iter)
                    count += 1

                    # train with real
                    real_cpu, _ = data
                    netD.zero_grad()
                    batch_size = real_cpu.size(0)


                    real_cpu = real_cpu.cuda()
                    _=_.cuda()
                    input.resize_as_(real_cpu).copy_(real_cpu)
                    inputv = Variable(input)

                    errD_real = netD(inputv, _)
                    errD_real.backward(one)

                    # train with fake
                    noise.resize_(batchSize, nz, 1, 1).normal_(0, 1)
                    noisev = Variable(noise, volatile = True) # totally freeze netG
                    fake_labels=Variable(torch.LongTensor(np.random.randint(0, num_classes, batchSize))).cuda()
                    fake = Variable(netG.main(netG.forward(noisev,fake_labels)).data)
                    inputv = fake
                    #print("Shape of fake tensor is: ",fake.shape)
                    errD_fake = netD(inputv,fake_labels)
                    errD_fake.backward(mone)
                    errD = errD_real - errD_fake
                    optimizerD.step()

                ############################
                # (2) Update G network
                ###########################
                # for p in netD.parameters():
                #     p.requires_grad = False # to avoid computation
                netG.zero_grad()
                # in case our last batch was the tail batch of the dataloader,
                # make sure we feed a full batch of noise
                noise.resize_(batchSize, nz, 1, 1).normal_(0, 1)
                noisev = Variable(noise)
                fake_labels=Variable(torch.LongTensor(np.random.randint(0, num_classes, batchSize))).cuda()
                fake = Variable(netG.main(netG.forward(noisev,fake_labels)).data)
                errG = netD(fake,fake_labels)
                errG.backward(one)
                optimizerG.step()
                gen_iterations += 1

                print('[%d/%d][%d/%d][%d] Loss_D: %f Loss_G: %f Loss_D_real: %f Loss_D_fake %f' % (epoch, opt.niter1, i, len(dataloaders[i]), gen_iterations, errD.data[0], errG.data[0], errD_real.data[0], errD_fake.data[0]))

                if gen_iterations % 100 == 0:
                    real_cpu = real_cpu.mul(0.5).add(0.5)
                    vutils.save_image(real_cpu, f'{opt.experiment+str(i)}/real_samples.png')
                    fake = netG.main(netG(Variable(fixed_noise, volatile=True),fake_labels))
                    fake.data = fake.data.mul(0.5).add(0.5)
                    vutils.save_image(fake.data, f'{opt.experiment+str(i)}/fake_samples_{gen_iterations}.png')

            # Saving generator and discriminator model at every 50 epochs
            if epoch % 1000 == 0:
                # do checkpointing
                torch.save(netG.state_dict(), f'{opt.experiment+str(i)}/netG_epoch_{epoch}.pth')
                torch.save(netD.state_dict(), f'{opt.experiment+str(i)}/netD_epoch_{epoch}.pth')

#codistillation
    avg_features_list=[avg_feature_rep(j, gen_models, 2,10) for j in range(num_clients)]
    gen_iterations = 0
    
    for epoch in range(opt.niter2):
        for i in range(num_clients):
            data_iter = iter(dataloaders[i])
            count = 0
            netD=disc_models[i]
            netG=gen_models[i]
            optimizerD=disc_optimizers[i]
            optimizerG=gen_optimizers[i]
            while count < len(dataloaders[i]):
                ############################
                # (1) Update D network
                ###########################
                for p in netD.parameters(): # reset requires_grad
                    p.requires_grad = True # they are set to False below in netG update

                # train the discriminator Diters times
                if gen_iterations < 25 or gen_iterations % 500 == 0:
                    Diters = 100
                else:
                    Diters = opt.Diters
                j = 0
                while j < Diters and count < len(dataloaders[i]):
                    j += 1

                    # clamp parameters to a cube
                    for p in netD.parameters():
                        p.data.clamp_(opt.clamp_lower, opt.clamp_upper)

                    # data = data_iter.next()
                    data = next(data_iter)
                    count += 1

                    # train with real
                    real_cpu, _ = data
                    netD.zero_grad()
                    batch_size = real_cpu.size(0)


                    real_cpu = real_cpu.cuda()
                    _=_.cuda()
                    input.resize_as_(real_cpu).copy_(real_cpu)
                    inputv = Variable(input)

                    errD_real = netD(inputv, _)
                    errD_real.backward(one)

                    # train with fake
                    noise.resize_(batchSize, nz, 1, 1).normal_(0, 1)
                    noisev = Variable(noise, volatile = True) # totally freeze netG
                    fake_labels=Variable(torch.LongTensor(np.random.randint(0, num_classes, batchSize))).cuda()
                    fake = Variable(netG.main(netG.forward(noisev,fake_labels)).data)
                    inputv = fake
                    errD_fake = netD(inputv,fake_labels)
                    errD_fake.backward(mone)
                    errD = errD_real - errD_fake
                    optimizerD.step()

                ############################
                # (2) Update G network
                ###########################
                # for p in netD.parameters():
                #     p.requires_grad = False # to avoid computation
                netG.zero_grad()
                # in case our last batch was the tail batch of the dataloader,
                # make sure we feed a full batch of noise
                noise.resize_(batchSize, nz, 1, 1).normal_(0, 1)
                noisev = Variable(noise)
                fake_labels=Variable(torch.LongTensor(np.random.randint(0, num_classes, batchSize))).cuda()
                features=netG.forward(noisev,fake_labels)
                fake = Variable(netG.main(features).data)
                errG = netD(fake,fake_labels)

                errG+= torch.mean(torch.square(torch.mean(features,dim=-1)-torch.stack([avg_features_list[i][label.item()]
                                                                                      for label in fake_labels])))
                errG.backward(one, retain_graph=True)
                optimizerG.step()
                gen_iterations += 1

                print('[%d/%d][%d/%d][%d] Loss_D: %f Loss_G: %f Loss_D_real: %f Loss_D_fake %f' % (epoch, opt.niter2, i, len(dataloaders[i]), gen_iterations, errD.data[0], errG.data[0], errD_real.data[0], errD_fake.data[0]))

                if gen_iterations % 100 == 0:
                    real_cpu = real_cpu.mul(0.5).add(0.5)
                    vutils.save_image(real_cpu, f'{opt.experiment+str(i)}/real_samples.png')
                    fake = netG.main(netG(Variable(fixed_noise, volatile=True),fake_labels))
                    fake.data = fake.data.mul(0.5).add(0.5)
                    vutils.save_image(fake.data, f'{opt.experiment+str(i)}/fake_samples_{gen_iterations}.png')

            # Saving generator and discriminator model at every 50 epochs
            if epoch % 1000 == 0:
                # do checkpointing
                torch.save(netG.state_dict(), f'{opt.experiment+str(i)}/netG_epoch_{epoch}.pth')
                torch.save(netD.state_dict(), f'{opt.experiment+str(i)}/netD_epoch_{epoch}.pth')
        avg_features_list=[avg_feature_rep(j,gen_models,2,10) for j in range(num_clients)]
