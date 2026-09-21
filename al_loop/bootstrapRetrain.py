# Script to perform the bootstrappig of the selected model
# We are just going to add the resampling and maybe the calculation
# of the f1 or aucroc performance

## Packages
import pandas as pd
import numpy as np
import torch
import argparse
import sys
import os
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, set_seed

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-data", help = "path to the trainig dataset", required = True)
parser.add_argument("-out", help = "file name root where to save the predictions, example 'output_predictions_test'. Extension and iteration will be added", required = True)
parser.add_argument("-seed", help = "random seed", default = 26, type = int)
parser.add_argument("-model", help = "path to the model folder", required = True)
parser.add_argument("-tokenizer", help = "path to the tokenizer folder", required = True)
parser.add_argument("-batch", help = "number of sampels per batch during training", type = int, required = True)
parser.add_argument("-outFolder", help = "directory where all of the ouput files will be stored", required = True)
parser.add_argument("-iterations", help = "number of iterations of resampling for the bootraping", type = int, required = True)
parser.add_argument("-cluster", help = "if provided it will done cluster bootraping with the given columns", nargs = "+")
args = parser.parse_args()

# Check all of the files are correct
if not os.path.isfile(args.data):
    print(f"ERROR: file {args.data} cannot be found")
    sys.exit(1)
else:
    data = pd.read_csv(args.data)

    if any(column not in data.columns for column in [ "text", "labels"]):
        print(f'ERROR: columns "text", "labels" need to be in file {args.data}')
        sys.exit(1)
    

# Check model and tokenizer directories exist
if not os.path.exists(args.model):
    print(f"Directory {args.model} cannot be found")
    sys.exit(1)

if not os.path.exists(args.tokenizer):
    print(f"Directory {args.tokenizer} cannot be found")
    sys.exit(1)

if args.batch < 0:
    print("The value of the number of samples per batch cannot be negative")
    sys.exit(1)

if args.iterations <= 0:
    print("ERROR: the argument iterations needs to be greater than 0")
    sys.exit(1)

if args.cluster != None:
    if any(column not in data.columns for column in args.cluster):
        print(f"ERROR: one or more columns provided in the argument cluster, {args.cluster} are not in the file {args.data}")
        sys.exit(1)
    
    # Get the uniqe combinations for the clustering
    unique_sentences = data[args.cluster].drop_duplicates()

if not os.path.isdir(args.outFolder):
    os.makedirs(args.outFolder, exist_ok = True )

## Functions

def tokenizer_function(sentence):
    """
    We are not going to do dynamic padding because we need to padd all of
    the batches with the same length so we can do the bald score at the end
    """

    texts = [item["text"] for item in sentence]

    tokenized = tokenizer(
        texts,
        padding = "max_length",
        max_length = 250,
        truncation = True,
        return_tensors="pt")

    return tokenized

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


## NLP Model and data-preprocessing out of the bootstrapping iteration
set_seed(args.seed)
np.random.seed(args.seed)

tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
model = AutoModelForSequenceClassification.from_pretrained(args.model,
                                                           num_labels = 2,
                                                           local_files_only = True,
                                                           output_hidden_states = False)

# Send the model to the gpu if available (faster)
if torch.cuda.is_available():
    model.cuda()
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

for iter in range(args.iterations):
    print(f"Working in iteration {iter}")
    # Get the data that is going to be predicted
    unit_selected = unique_sentences.sample(frac = 1, replace = True)
    sample_data = data.merge(unit_selected, on = args.cluster, how = "right")

    # Transform the active learning dataset
    data_dict = DatasetDict({"data": Dataset.from_pandas(sample_data[["text"]])})
    dataloader = torch.utils.data.DataLoader(data_dict["data"],
                                            batch_size = args.batch,
                                            collate_fn = tokenizer_function,
                                            shuffle = False)
    all_outputs = []

    for batch in dataloader:
        batch = {k: v.to(device) for k, v in batch.items()}

        with torch.no_grad():
            outputs = model(**batch)

        all_outputs.append(outputs.logits.cpu())


    all_outputs = torch.cat(all_outputs, dim = 0)

    # Lets do a deepcopy of the test dataset so we can work on it
    output_test = sample_data.copy(deep = True)

    # Lets transform the logits and then have a dataframe with all the information
    output_test = transform_logits(output_test, all_outputs)

    output_test.to_csv(os.path.join(args.outFolder, f"{args.out}_{iter}.csv"), index = False)
