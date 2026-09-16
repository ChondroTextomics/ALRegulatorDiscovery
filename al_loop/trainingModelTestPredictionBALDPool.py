# Script to train with the AL batch the PubMedBERT for entity clasification
# We will do the train, pediction of test and BALD scores of pool
# All of these processes will be done in GPU an that is why
# they are groupped together

## ---------------------------------------
## Packages
import pandas as pd
import numpy as np
import torch
import argparse
import sys
import os
from datasets import Dataset, DatasetDict
from transformers import TrainingArguments, AutoTokenizer, AutoModelForSequenceClassification, set_seed
from baal import ActiveLearningDataset
from baal.bayesian.dropout import patch_module
from baal.active import get_heuristic
from baal.active.heuristics import BALD
from baal.transformers_trainer_wrapper import BaalTransformersTrainer
from torch.utils.data import Subset
import psutil # it is for memory tracking
import gc
from sklearn.utils import class_weight

## ---------------------------------------
## Input
parser = argparse.ArgumentParser()
parser.add_argument("-train", help = "path to the trainig dataset", required = True)
parser.add_argument("-test", help = "path to the test dataset", required = True)
parser.add_argument("-pool", help = "path to the pool dataset (unlabelled samples)", required = True)
parser.add_argument("-out", help = "directory that will hold all of the outputs (model, test predictions, pool predictions, ...)", required = True)
parser.add_argument("-seed", help = "random seed", default = 26, type = int)
parser.add_argument("-model", help = "path to the model folder", required = True)
parser.add_argument("-tokenizer", help = "path to the tokenizer folder", required = True)
parser.add_argument("-iterMC", help = "iteration to do the MC dropout, how many of them", type = int, required = True)
parser.add_argument("-epoch", help = "epochs to do during training", type = int, default = 2)
parser.add_argument("-iteration", help = "loop iteration, for labelling the results", required = True, type = int)
parser.add_argument("-batch", help = "number of sampels per batch during training", type = int, required = True)
parser.add_argument("-lr", help = "learning rate during training", type = float, required = True)
parser.add_argument("-warmup", help = "ratio of steps that will be used as warmup (low learning rate) rate during training", type = float, required = True)
parser.add_argument("-weightDecay", help = "value of weight decay for values in nodes used during training", type = float, required = True)
parser.add_argument("-weightLossFunction", help = "establish if use or not a balancing weight loss function during training", choices = ["True", "False", "TRUE", "FALSE", "true", "false"], required = True)

args = parser.parse_args()

# Check all of the files are correct
if not os.path.isfile(args.train):
    print(f"ERROR: file {args.train} cannot be found")
    sys.exit(1)
else:
    train = pd.read_csv(args.train)

    if any(column not in train.columns for column in ["text", "labels"]):
        print(f'ERROR: columns "text", "labels" need to be in file {args.train}')
        sys.exit(1)

if not os.path.isfile(args.test):
    print(f"ERROR: file {args.test} cannot be found")
    sys.exit(1)
else:
    test = pd.read_csv(args.test)

    if any(column not in test.columns for column in ["text", "labels"]):
        print(f'ERROR: columns "text", "labels" need to be in file {args.test}')
        sys.exit(1)

if not os.path.isfile(args.pool):
    print(f"ERROR: file {args.pool} cannot be found")
    sys.exit(1)
else:
    pool = pd.read_csv(args.pool)

    if any(column not in pool.columns for column in ["text", "labels"]):
        print(f'ERROR: columns "text", "labels" need to be in file {args.pool}')
        sys.exit(1)

    output_pool = pool.copy(deep = True)
    # We need to give a provisional label to the pool so the BAAL program works
    pool["labels"] = 0

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
        print(num_items_in_batch)
        logits = outputs.logits
        loss_fct = torch.nn.CrossEntropyLoss(weight = weights.to(logits.device).float(), #  we need to put it as a float or it will give an error
                                             label_smoothing = 0.1) # this is to prevent overfitting
        loss = loss_fct(logits, labels)
        return (loss, outputs) if return_outputs else loss
    return my_weighted_loss

set_seed(args.seed)
## ---------------------------------------
## NLP Model and data-preprocessing
tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
model = AutoModelForSequenceClassification.from_pretrained(args.model,
                                                           num_labels = 2,
                                                           local_files_only = True,
                                                           output_hidden_states = True)

# Add our special tokens
tokenizer.add_special_tokens({'additional_special_tokens': ['[GENE]', '[TARGET]', '[/TARGET]']})

# Resize the embedding space of our model
model.resize_token_embeddings(len(tokenizer))

# Active Learning Dataset
# Create the active learning dataset (train + pool)
activeLearningDataset = pd.concat([train, pool], ignore_index = True)

# Initialize the training arguments for the model
# https://huggingface.co/docs/transformers/v4.56.2/en/main_classes/trainer#transformers.TrainingArguments
# Change train_args in v3 to insert the new parameters
train_args = TrainingArguments(output_dir = os.path.join(args.out, f"iteration_{args.iteration}"), # output directory, not sure for what
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
train_dict = DatasetDict({"train": Dataset.from_pandas(activeLearningDataset[["text", "labels"]])})
    
# Tokenize the data
train_token = train_dict.map(lambda sen: tokenizer_function(sen, tokenizer), batched = True)
    
# Remove not needed columns
if '__index_level_0__' in train_token["train"].features.keys():
    train_token = train_token.remove_columns(["text", "__index_level_0__"])
else:
    train_token = train_token.remove_columns(["text"])
    
# Set the correct format for the transformers training, in our case is torch
train_token.set_format("torch")
    
# Create the AL dataset in the necccessary format for it to work
# https://github.com/baal-org/baal/blob/master/baal/active/dataset/pytorch_dataset.py#L36
active_set = ActiveLearningDataset(dataset = train_token["train"])
# Now we tell the active set which ones are labelled
active_set.label(list(range(len(train))))
# They are the first ones because when we do concat train was the 1st element

# Test Dataset
# This dataset doesnt need to be converted to AL because it wont be used like that
# Transform Dataframe to DatasetDict
test_dict = DatasetDict({"test": Dataset.from_pandas(test[["text", "labels"]])})
# Tokenize the data
test_token = test_dict.map(lambda sen: tokenizer_function(sen, tokenizer), batched = True)
# Remove not needed columns
if '__index_level_0__' in test_token["test"].features.keys():
    test_token = test_token.remove_columns(["text", "__index_level_0__"])
else:
    test_token = test_token.remove_columns(["text"])
# Set correct format
test_token.set_format("torch")

# Now everything related to the NLP is pre-processed
## ---------------------------------------
## BAAL model preparation (MC Dropout)
# Set the heuristic that we are going to work with
# We get the function used to score the unlabelled pool
# in our case, lets use bald for now
heuristic = get_heuristic('bald')

# This is the neccessary step to turn the model into a bayesian one
model = patch_module(model)

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
    trainer = BaalTransformersTrainer(model = model,
                                    args = train_args,
                                    train_dataset = active_set,
                                    processing_class = tokenizer,
                                    compute_loss_func = create_weighted_loss(torch.tensor(class_weights)))
else: # We do the default loss function
    trainer = BaalTransformersTrainer(model = model,
                                  args = train_args,
                                  train_dataset = active_set,
                                  processing_class = tokenizer)

# We dont have to change anyhthing else
# we dont need to chnage the class of the trainer
# that is something old and they inserted the compute_loss_func

## ---------------------------------------
## Training Model
# Train the model
trainer.train()

# Save the model and tokenizer
trainer.model.save_pretrained(os.path.join(args.out, "trained_model/"))
tokenizer.save_pretrained(os.path.join(args.out, "trained_model/"))

## ---------------------------------------
## Test Predictions
# Get the prediction from the model
test_preds = trainer.predict(test_token["test"]) # This will have the logits, hidden states and original labels
torch.cuda.empty_cache()

# Lets do a deepcopy of the test dataset so we can work on it
output_test = test.copy(deep = True)

# Lets transform the logits and then have a dataframe with all the information
output_test = transform_logits(output_test, test_preds[0][0])

# Save the test predictions
output_test.to_csv(os.path.join(args.out, f"{args.seed}_testPredictions_iter{args.iteration}.csv"), index = False)

# For memory saving we will eliminate the test_preds
del test_preds
gc.collect()

## ---------------------------------------
## Pool Uncertainty
# Get the predictions of the pool with the BALD score
# We need to disconnect the model hidden layers for predict_on_dataset to work correctly because it
# doesnt expect the hidden layers that we will be using
model.config.output_hidden_states = False

# The same way that we needed to do batches for the pool prediction we need to do batches for this process
all_bald_preds_batch = []

for batch in batch_indexes_generator(list(range(len(pool))), max(1, len(pool)//1000)):
  bald_preds = trainer.predict_on_dataset(Subset(active_set.pool, batch), iterations = args.iterMC)
  all_bald_preds_batch.append(bald_preds)
  del bald_preds
  gc.collect()
  torch.cuda.empty_cache()

# Now we need to fuse the results
pool_mcd_prediction = np.concatenate(all_bald_preds_batch, axis = 0)
del all_bald_preds_batch
gc.collect()

# We enable them again
model.config.output_hidden_states = True
# The pool_mcd_prediction is [number_samples, number_classes, num_iterations]
# For the bald scores what we want is the first element, the rest is the hidden layers
bald_pool = heuristic.get_uncertainties(pool_mcd_prediction)

# Lets add the uncertainty for each sample
output_pool["BALD"] = bald_pool

## ---------------------------------------
## Save the results

# Lets save now the predictions and selection of this iteration from the pool
output_pool.to_csv(os.path.join(args.out, f"{args.seed}_poolBALD_iter{args.iteration}.csv"), index = False)
