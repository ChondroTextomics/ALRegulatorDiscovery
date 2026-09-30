# Script to just  train the model and save it, nothing else
# it is based on the al_loop script in which the PubMedBERT is trained, given pool BALD predictions, etc

## ---------------------------------------
## Packages
import time
total_start = time.perf_counter()
time_before_packages = time.perf_counter()

import pandas as pd
import numpy as np
import torch
import argparse
import sys
import os
from datasets import Dataset, DatasetDict
from transformers import TrainingArguments, AutoTokenizer, AutoModelForSequenceClassification, set_seed, Trainer
from sklearn.utils import class_weight

time_after_packages = time.perf_counter()

## ---------------------------------------
## Input
parser = argparse.ArgumentParser()
parser.add_argument("-train", help = "path to the trainig dataset", required = True)
parser.add_argument("-out", help = "directory that will hold all of the outputs (model, test predictions, pool predictions, ...)", required = True)
parser.add_argument("-seed", help = "random seed", default = 26, type = int)
parser.add_argument("-model", help = "path to the model folder", required = True)
parser.add_argument("-tokenizer", help = "path to the tokenizer folder", required = True)
parser.add_argument("-epoch", help = "epochs to do during training", type = int, default = 2)
parser.add_argument("-batch", help = "number of sampels per batch during training", type = int, required = True)
parser.add_argument("-lr", help = "learning rate during training", type = float, required = True)
parser.add_argument("-warmup", help = "ratio of steps that will be used as warmup (low learning rate) rate during training", type = float, required = True)
parser.add_argument("-weightDecay", help = "value of weight decay for values in nodes used during training", type = float, required = True)
parser.add_argument("-weightLossFunction", help = "establish if use or not a balancing weight loss function during training", choices = ["True", "False", "TRUE", "FALSE", "true", "false"], required = True)

args = parser.parse_args()

# Check all of the files are correct
time_before_argument_checking = time.perf_counter()
if not os.path.isfile(args.train):
    print(f"ERROR: file {args.train} cannot be found")
    sys.exit(1)
else:
    train = pd.read_csv(args.train)

    if any(column not in train.columns for column in ["text", "labels"]):
        print(f'ERROR: columns "text", "labels" need to be in file {args.train}')
        sys.exit(1)

# Check model and tokenizer directories exist
if not os.path.exists(args.model):
    print(f"Directory {args.model} cannot be found")
    sys.exit(1)

if not os.path.exists(args.tokenizer):
    print(f"Directory {args.tokenizer} cannot be found")
    sys.exit(1)

# Create the results directory
if not os.path.exists(args.out):
    os.makedirs(args.out)
    print(f"Directory {args.out} successfully created")

# New checks
# Check that the warmup is a fraction
if args.warmup < 0 or args.warmup > 1:
    print("The warmup argument needs to be a fraction (range [0, 1])")
    sys.exit(1)

# Check that none of the values are negatives
if args.lr < 0:
    print("The learning rate cannot be negative")
    sys.exit(1)

if args.epoch < 0:
    print("The epochs cannot be negative")
    sys.exit(1)

if args.weightDecay < 0:
    print("The weight decay cannot be negative")
    sys.exit(1)

if args.batch < 0:
    print("The value of the number of samples per batch cannot be negative")
    sys.exit(1)

# Change the weightLossFunction to boolean
if args.weightLossFunction in ["TRUE", "True", "true"]:
    args.weightLossFunction = True
else:
    args.weightLossFunction = False

time_after_checking_arguments = time.perf_counter()

## ---------------------------------------
## Functions

def tokenizer_function(sentence, tokenizer):
  """
  We are not going to do dynamic padding because we need to padd all of
  the batches with the same length so we can do the bald score at the end
  """
  # Tokenization function used to map the sentences with batches (optimizing resources)
  return(tokenizer(sentence["text"], padding = "max_length", max_length = 250, truncation = True))

def transform_logits(data, predictions):
    """
    In this function we get the data that has been predicted with the model
    and the logits that come from predict(), they are already the logits

    We transform all of them to get all the neccessary information to add and then we can calculate
    all of the performances

    This will be valid both for the test and the pool dataset, because we have same structure for
    both predictions
    """

    # Get the logits in columns
    logits_columns = pd.DataFrame(predictions, columns = ["logits_0", "logits_1"])

    # Get the label from the logits
    logits_columns["predicted_label"] = np.argmax(logits_columns[["logits_0", "logits_1"]].values, axis = 1)

    # Get the probabilities
    logits_torch = torch.tensor(predictions, dtype = torch.float32)
    probabilities_labels = torch.softmax(logits_torch, dim = -1).numpy()

    # Insert the probabilities
    logits_columns[["prob_0","prob_1"]] = probabilities_labels

    # Finally we concat the dataframes
    # This works because it has not been shuffle when predicted
    output = pd.concat([data, logits_columns], axis = 1)

    return output
    
def batch_indexes_generator(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# We can give a loss function to the Trainer
# we know this from https://huggingface.co/docs/transformers/main_classes/trainer#transformers.Trainer.compute_loss_func
# where we can see that we need to create a specific type of function but we can
# The original loss function is https://github.com/huggingface/transformers/blob/052e652d6d53c2b26ffde87e039b723949a53493/src/transformers/trainer.py#L3618
# this way we can base what we need to return and get in the function from this one
def create_weighted_loss(weights):
    # def my_weighted_loss(outputs, labels, return_outputs = False, num_items_in_batch = None):
    def my_weighted_loss(outputs, labels, return_outputs = False, num_items_in_batch = None): # The num_items_in_batch is neccessary to rewrite the loss function
        logits = outputs.logits
        loss_fct = torch.nn.CrossEntropyLoss(weight = weights.to(logits.device).float(), #  we need to put it as a float or it will give an error
                                             label_smoothing = 0.1) # this is to prevent overfitting
        loss = loss_fct(logits, labels)
        return (loss, outputs) if return_outputs else loss
    return my_weighted_loss

set_seed(args.seed)
## ---------------------------------------
## NLP Model and data-preprocessing
time_before_nlp_preprocesing = time.perf_counter()
load_start = time.perf_counter()
tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
model = AutoModelForSequenceClassification.from_pretrained(args.model,
                                                           num_labels = 2,
                                                           local_files_only = True)

# Add our special tokens
tokenizer.add_special_tokens({'additional_special_tokens': ['[GENE]', '[TARGET]', '[/TARGET]']})

# Resize the embedding space of our model
model.resize_token_embeddings(len(tokenizer))
load_time = time.perf_counter() - load_start

# Initialize the training arguments for the model
# https://huggingface.co/docs/transformers/v4.56.2/en/main_classes/trainer#transformers.TrainingArguments
# Change train_args in v3 to insert the new parameters
train_args = TrainingArguments(output_dir = os.path.join(args.out, f"final_model_out_dir"), # output directory, not sure for what
                               num_train_epochs = args.epoch, # epochs for the training, we are going to set it
                               per_device_train_batch_size = args.batch, # batch size of the training set
                               per_device_eval_batch_size = 4,
                               weight_decay = args.weightDecay, # strength of weight decay, I am not sure how much will this affect
                               report_to = [],  # disable all loggers, including wandb
                               seed = args.seed,
                               logging_steps = 1,
                               learning_rate = args.lr,
                               warmup_ratio = args.warmup)

# Transform the active learning dataset
train_dict = DatasetDict({"train": Dataset.from_pandas(train[["text", "labels"]])})
    
# Tokenize the data
train_token = train_dict.map(lambda sen: tokenizer_function(sen, tokenizer), batched = True)
    
# Remove not needed columns
if '__index_level_0__' in train_token["train"].features.keys():
    train_token = train_token.remove_columns(["text", "__index_level_0__"])
else:
    train_token = train_token.remove_columns(["text"])
    
# Set the correct format for the transformers training, in our case is torch
train_token.set_format("torch")

# Now everything related to the NLP is pre-processed
## ---------------------------------------

# Send the model to the gpu if available (faster)
if torch.cuda.is_available():
    model.cuda()

# Create the model trainer wrapper
# This trainer will behave exactly like the one in HuggingFace
# This is where the TrainingArguments come in place
# https://github.com/baal-org/baal/blob/master/baal/transformers_trainer_wrapper.py#L36 --> this is in the current version
# we know from this script that BaalTransformersTrainer is a subclass of Trainer

class_weights = class_weight.compute_class_weight(
                class_weight = 'balanced',
                classes = np.unique(train["labels"]), 
                y = train["labels"])

# Change for v3 to introduce the possibility of not using a class weighted loss
if args.weightLossFunction: # We do a weighted loss function
    trainer = Trainer(model = model,
                      args = train_args,
                      train_dataset = train_token["train"],
                      processing_class = tokenizer,
                      compute_loss_func = create_weighted_loss(torch.tensor(class_weights)))
else: # We do the default loss function
    trainer = Trainer(model = model,
                      args = train_args,
                      train_dataset = train_token["train"],
                      processing_class = tokenizer)
    
## ---------------------------------------
## Training Model
# Train the model
train_time_start = time.perf_counter()
trainer.train()
train_time = time.perf_counter() - train_time_start
# Save the model and tokenizer
trainer.model.save_pretrained(os.path.join(args.out, "trained_model/"))
tokenizer.save_pretrained(os.path.join(args.out, "trained_model/"))

# Total time of script
total_time = time.perf_counter() - total_start

# save the load_time and total_time in a text file
with open(os.path.join(args.out, "time_tracking.txt"), "w") as f:
    f.write(f"time packages: {(time_after_packages-time_before_packages):.2f}s\n")
    f.write(f"Model load time: {load_time:.2f}s\n")
    f.write(f"Total time: {total_time:.2f}s\n")
    f.write(f"Time to train the model: {train_time:.2f}s\n")
