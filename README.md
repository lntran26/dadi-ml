# Machine Learning Applications for Diffusion Approximation of Demographic Inference

## Introduction
Diffusion Approximation of Demographic Inference ([dadi](https://dadi.readthedocs.io/en/latest/)) is a powerful software tool for simulating the joint frequency spectrum (FS) of genetic variation among multiple populations and employing the FS for population-genetic inference. Here we introduce machine learning-based tools for easier application of dadi's underlying demographic models. These machine learning models were trained on dadi-simulated data and can be used to make quick predictions on dadi demographic model parameters given FS input data from user and specified demographic model. The pipeline we used to train the machine learning models are also available here for users interested in using the same framework to train a new predictor for their customized demographic models.

## Requirements
1. [dadi](https://dadi.readthedocs.io/en/latest/) 2.1.1 
2. [scikit-learn](https://scikit-learn.org/0.24/) 0.24.1
3. [MAPIE](https://mapie.readthedocs.io/en/latest/) 0.3.1

## Usage


## References
1. [Gutenkunst et al., *PLoS Genet*, 2009.](https://journals.plos.org/plosgenetics/article?id=10.1371/journal.pgen.1000695)
2. 