# Pool predictions with batches
# This will be the script to run in CPU with eadch one of the batches

# This will generate the batches prediction with the model given

# This script still will work for 1 batch/dataset if it is small enough but it is prepared to be run in parallel

import argparse
import os
import sys
import pandas as pd
import numpy as np
from datasets import Dataset, DatasetDict
from transformers import  AutoTokenizer, AutoModelForSequenceClassification
import torch
from torch.utils.data import DataLoader
import time

## Arguments for file
parser = argparse.ArgumentParser()
parser.add_argument("-batch", help = "name of the file that is going to be read and predicted", required = True)
parser.add_argument("-model", help = "path to the model already fine tunned", required = True)
parser.add_argument("-tokenizer", help = "path to the tokenizer", required = True)
parser.add_argument("-batchNumber", help = "number of the batch that is being predicted, for name purposes", required = True, type = int)
parser.add_argument("-prefix", help = "prefix of the file name to the number of batch and extension", required = True)
parser.add_argument("-prefixEmbeddings", help = "prefix of the file name for the CLS embeddings to the number of batch and extension", required = True)
parser.add_argument("-out", help = "folder where the batches will be saved", required = True) # Needs to be pre-done so running 1 batch will not influence th eother
args = parser.parse_args()

# Checks
if os.path.isfile(args.batch):
    pool = pd.read_csv(args.batch)

    if "text" not in pool.columns:
        print(f'ERROR: column "text" needs to be in file {args.batch}')
        sys.exit(1)
    
    if "labels" in pool.columns:
        pool.drop(columns = ["labels"])

    output_pool = pool.copy(deep = True)
else:
    print(f"ERROR: file {args.batch} cannot be found")
    sys.exit(1)

if not os.path.exists(args.out):
    print(f"ERROR: folder {args.out} cannot be found, create it before running this script")
    sys.exit(1)

if not os.path.exists(args.model):
    print(f"ERROR: folder {args.model} cannot be found")
    sys.exit(1)

if not os.path.exists(args.tokenizer):
    print(f"ERROR: folder {args.tokenizer} cannot be found")
    sys.exit(1)

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

## Body of script
## ---------------------------------------
## NLP Model and data-preprocessing
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

time_before_nlp_preprocesing = time.perf_counter()
tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
model = AutoModelForSequenceClassification.from_pretrained(args.model,
                                                           local_files_only = True,
                                                           output_hidden_states = True) # We are going to store as well the CLS embeddings

model.eval()

# Transform the pool
pool_dict = DatasetDict({"pool": Dataset.from_pandas(pool[["text"]])})
    
# Tokenize the data
pool_token = pool_dict.map(lambda sen: tokenizer_function(sen, tokenizer), batched = True)
    
# Remove not needed columns
if '__index_level_0__' in pool_token["pool"].features.keys():
    pool_token = pool_token.remove_columns(["text", "__index_level_0__"])
else:
    pool_token = pool_token.remove_columns(["text"])
    
# Set the correct format for the transformers training, in our case is torch
pool_token.set_format("torch")

# Create the loader
loader = DataLoader(pool_token["pool"],
                    batch_size = 24)

## ---------------------------------------
## Prediction of the labels
all_logits = []
all_cls = []

for batch in loader:
    batch = {k: v.to(device) for k, v in batch.items()}
    with torch.no_grad():
        output = model(**batch)
        # Get the logits of the batch
        logits = output.logits
        all_logits.extend(logits.cpu().numpy())
        # Get the CLS embedding of the batch
        cls_embeddings = output.hidden_states[-1][:, 0, :]
        all_cls.extend(cls_embeddings.cpu().numpy())

## Add the predicted labels column
output_pool = transform_logits(output_pool, all_logits)

## Extract the CLS embeddings of this batch for the future clustering
#cls_embeddings = output.hidden_states[-1][:,0,:]
output_embeddings = pd.DataFrame(all_cls) # I need to look how this works

## Save both dataframes
output_pool.to_csv(os.path.join(args.out, f"{args.prefix}_{args.batchNumber}.csv"), index = False)
output_embeddings.to_csv(os.path.join(args.out, f"{args.prefixEmbeddings}_{args.batchNumber}.csv"), index = False)