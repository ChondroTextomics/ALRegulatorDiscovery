## Overview

![AL Loop](ALLoop_figure.png)

This folder contains the resources required to do part of a loop in the active learning framework using a Hugging Face model. A whole loop is the combination of the pipeline in this folder and the one in `labelling`.

Requirements for running this pipeline are provided in the `envs` folder.

This folder takes as input the results of the folder `labelling`, and the output is the input of the same folder

Pipeline stages:
 1. Create the dataset that will be the training set for the Hugging Face model
 2. Train the model and provide the predictions of the validation dataset and pool
 3. Select the samples to label from the pool predictions

---
## Files
