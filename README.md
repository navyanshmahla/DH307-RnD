# RnD Project
The project is supervised by Prof. Kshitij Jadhav and Prof. Ganesh Ramakrishnan in DH307 offered by the KCDH dept. at IIT-Bombay. Details about the project are listed below:

## Diffusion Models for medical data Augmentation in Federated learning setting for preserving privacy
### Abstract:
Diffusion models can be utilized for medical data augmentation in a federated learning
setting to preserve privacy. Federated learning allows training machine learning models across
multiple institutions without directly sharing sensitive patient data. Here's an overview of the
approach
1. Data Privacy and Federated Learning: In a federated learning setting, data remains
decentralized and resides within different medical institutions or devices. Privacy is maintained
by keeping the data local and performing model training and updates on the local data without
exchanging the raw data itself.
2. Diffusion Models: Diffusion models, such as generative models like Variational Autoencoders
(VAEs) or Generative Adversarial Networks (GANs), can be employed for medical data
augmentation. These models learn the underlying distribution of the medical data and generate
new synthetic samples that preserve the statistical properties of the original data.
3. Local Data Augmentation: At each local medical institution or device participating in the
federated learning framework, diffusion models can be trained on the local data. These local
models learn the local data distribution

### Dataset
Link to the preprocessed dataset: https://drive.google.com/drive/u/0/folders/1gxOiEOzuxtfKkC1oslO9likQY2l_ysBh
Code to pre-process the data will soon be pushed to this repo

Link to the raw dataset: https://drive.google.com/file/d/1LHxvqJaD23CEF4QBCTmV9qYo-FDusnJn/view


### How to run?

First of all, clone the popular <a href="https://github.com/martinarjovsky/WassersteinGAN/blob/master/main.py">wGAN repo</a> as:
```bash
git clone https://github.com/martinarjovsky/WassersteinGAN/blob/master/main.py
```
Add the image dataset folder to this and run the following command, to know more about the flags, see the ```generate.py``` file!

**Old** Command to run:
```bash
python3 main.py --dataset folder --dataroot Dataset --cuda --workers 20 --niter 10000
```
**New** Command to run:
```bash
python3 main.py --datasetA folder --datasetB folder --datarootA Dataset-A --datarootB Dataset-B --cuda --workers 20 --imageSize 128 --niter1 4000 --niter2 10000 --lrD 1e-5 --lrG 1e-5 --num_classes 2 --num_clients 2 --adam 2>&1 | tee training_log.txt

```
