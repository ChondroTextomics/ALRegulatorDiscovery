# This python script is going to take a bunch of sentences
# and then convert them into the embeddings of BioSentenceBERT
# The objective is that these embeddings go to a core extraction
# method so we can get the initial batch of sentences to label

# We are using a sentence model because that one is already trained to
# distinghuish sentences semantically similar or dissimilar, which is
# what we want to do

# We are going to use the dataloader because without batches the GPU memory would not be enough

import argparse
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from transformers import AutoTokenizer, AutoModel
from datasets import Dataset
import torch
import pandas as pd
import sys



parser = argparse.ArgumentParser()
parser.add_argument("input", help="CSV file with dataframe (must contain pmid, number, text columns)")
parser.add_argument("output", help="Path to save the final CSV with embeddings")
parser.add_argument("-tokenizer", required=True, help="Path or name of the pretrained tokenizer")
parser.add_argument("-model", required=True, help="Path or name of the pretrained model")
parser.add_argument("-batch", type=int, default=100, help="Batch size for the dataloader (default: 100)")
parser.add_argument("-maxlength", type=int, default=512, help="Max sequence length for tokenization (default: 512)")
args = parser.parse_args()

# Checks
if not os.path.isfile(args.input):
    sys.exit(f"ERROR: file {args.input} cannot be found")

if os.path.exists(args.output):
    answer = input(f"The file '{args.output}' given for -out already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -out file already exists and was not replaced.")

if not os.path.exists(args.model):
    print(f"ERROR: folder {args.model} cannot be found")
    sys.exit(1)

if not os.path.exists(args.tokenizer):
    print(f"ERROR: folder {args.tokenizer} cannot be found")
    sys.exit(1)

## Functions
# Mean Pooling - Take attention mask into account for correct averaging
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def extracting_sentences(path):
    data = pd.read_csv(path)
    data_extracted = data[["pmid", "number", "text"]]
    return data_extracted

def tokenizer_function(sentence, tokenizer, max_length):
    # Tokenization function used to map the sentences with batches (optimizing resources)
    return tokenizer(sentence["text"], padding="max_length", truncation=True, max_length=max_length)

## Body of the script
tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
model = AutoModel.from_pretrained(args.model)

data_raw = extracting_sentences(args.input)
data = Dataset.from_pandas(data_raw)

# Tokenize our sentences
data_tokenized = data.map(lambda sen: tokenizer_function(sen, tokenizer, args.maxlength), batched=True)
# With the map we are adding to data input_ids and attention_mask columns

# We set the format to pytorch so the dataloader will receive tensors instead of lists
# this will make sure that data_tokenized is compatible with DataLoader
data_tokenized.set_format(type="torch", columns=["input_ids", "attention_mask"])

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model.to(device)

# Create an object that will create batches for gpu memory efficiency
dataloader = torch.utils.data.DataLoader(data_tokenized, batch_size=args.batch)

all_embeddings = []

# Compute token embeddings
with torch.no_grad():  # so nothing changes
    for batch in dataloader:
        # get the embeddings
        batch = {k: v.to(device) for k, v in batch.items()}
        model_output = model(**batch)

        # Perform pooling. In this case, mean pooling.
        sentence_embeddings = mean_pooling(model_output, batch["attention_mask"])

        all_embeddings.append(sentence_embeddings)

# Create a df with the embeddings
all_embeddings = torch.cat(all_embeddings, dim=0)  # concatenate all tensors returned by the model
embedding_df = pd.DataFrame(all_embeddings.cpu().numpy())

# Concat the 2 dataframes (original one with embedding one)
data_final = data_raw.join(embedding_df)  # We are joining the columns and indexes are going to be the same ones

# Lets save for now the results
data_final.to_csv(args.output, index = True)
embedding_df.to_csv(f"{os.path.splitext(args.output)[0]}_embeddings{os.path.splitext(args.output)[1]}")
