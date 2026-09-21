# Training and results of a dataset with a logistic regression with NLP model embeddings
# It is going to do the logistic regression with both CLS and pool embeddings
# that come from embeddings of a huggingface model

import pandas as pd
import numpy as np
import torch
import argparse
import sys
import os
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModel, set_seed
from sklearn.linear_model import LogisticRegression

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-training", help = "path to th efile that will have the training data", required = True)
parser.add_argument("-test", help = "path to the file with the sentences to predict with model", required = True)
parser.add_argument("-out", help = "path for the output file with classification of test file with attached probabilities", required = True)
parser.add_argument("-seed", help = "seed for the random state of the logistic regression", type = int, default = 24)
parser.add_argument("-model", help = "path to the huggingface model", required = True)
parser.add_argument("-tokenizer", help = "path to the huggingface tokenizer", required = True)
parser.add_argument("-batch", help = "number of samples per batch to train LR model", required = True, type = int)
args = parser.parse_args()

# Argument checker
# Check that the files and directories exist
if os.path.exists(args.out):
    answer = input(f"The file '{args.out}' given for -output already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -out file already exists and was not replaced.")

if os.path.isfile(args.training):
    train = pd.read_csv(args.training)

    if any(column not in train.columns for column in ["text", "labels"]):
        print(f"ERROR: columns 'text' and 'labels' needs to be in file {args.training}")
        sys.exit(1)
else:
    print(f"ERROR: file {args.training} cannot be found")
    sys.exit(1)

if os.path.isfile(args.test):
    test = pd.read_csv(args.test)

    if any(column not in test.columns for column in ["text", "labels"]):
        print(f"ERROR: columns 'text' and 'labels' needs to be in file {args.test}")
        sys.exit(1)
else:
    print(f"ERROR: file {args.test} cannot be found")
    sys.exit(1)

if not os.path.exists(args.model):
    print(f"ERROR: directory {args.model} cannot be found")
    sys.exit(1)

if not os.path.exists(args.tokenizer):
    print(f"ERROR: directory {args.tokenizer} cannot be found")
    sys.exit(1)

if args.batch <= 0:
    print("ERROR: batch number needs to be greater than 0")
    sys.exit(1)

## Functions
def tokenizer_function(sentence, tokenizer):
  """
  We are not going to do dynamic padding because we need to padd all of
  the batches with the same length so we can do the bald score at the end
  """
  # Tokenization function used to map the sentences with batches (optimizing resources)
  return(tokenizer(sentence["text"], padding = "max_length", max_length = 250, truncation = True))

def cls_pooling(model_output):
  return model_output.last_hidden_state[:, 0]

def mean_pooling(last_hidden_state, attention_mask):
    """
    Perform mean pooling on the last hidden state.

    Parameters:
    model_output (torch.Tensor): The last hidden layer of the model (shape: [batch_size, seq_len, hidden_size]).
    attention_mask (torch.Tensor): Attention mask indicating the valid tokens (shape: [batch_size, seq_len]).

    We require the attention mask so we can take in account which ones are padded tokens and that way the mean measure (final
    embeeded vector) has more meaning, it doesnt get diluted by the padding tokens. As well, by the time the padding
    tokens reach the last layer, they have some noise (they are not zeros)

    Returns:
    torch.Tensor: The mean pooled embeddings (shape: [batch_size, hidden_size]).
    """
    
    # What we do is get for each token of the text the attention and create a
    # vector of the hiddne layer size to we can multiply that layer (every value associated to the token)
    # for their attention, this way the vector associated to padding tokens are not taken in account
    # for the embedding --> we are doing this extension so we can do element-wise multiplication
    # We are turning [batch size, #tokens text] to [batch size, #tokens text, #nodes last hidden layer]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    # Count the number of valid tokens for each sequence (the non-padding ones)
    # We clamp to a tiny value (1e-9) to avoid division by zero errors
    num_tokens = torch.clamp(input_mask_expanded.sum(dim = 1), min = 1e-9)

    # Apply attention mask to get the sum of the embeddings and the count of the valid tokens
    sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, 1)
    # We are multiplying to the attention mask because that way the padding tokens doenst count
    # This function call sums the result of the element-wise multiplication across dimension 1, which corresponds to the sequence length (or number of tokens)

    # Calculate the mean embeddings
    mean_pooled = sum_embeddings / num_tokens
    
    return mean_pooled

def get_pooled_embeddings(text, device, batch_size):
    # Initialise the returning lists
    all_mean  = []
    all_cls = []

    for i in range(0, len(text), batch_size):
        # Get the batch
        batch = text[i:i + batch_size]

        # Get the inputs and model to the same device
        encoded_input = {k: v.to(device) for k, v in batch.items()}

        # Get the outputs
        model_output = model(**encoded_input)
        
        # Get mean embeddings (with the last hidden layer)
        mean_pool = mean_pooling(model_output.last_hidden_state, encoded_input['attention_mask'])

        # Get the CLS embedding
        cls_pool = cls_pooling(model_output)

        # Add them to the all lists
        all_mean.append(mean_pool.detach().cpu().numpy())
        all_cls.append(cls_pool.detach().cpu().numpy())

        # Clean the gpu
        torch.cuda.empty_cache()

    return (np.vstack(all_mean), np.vstack(all_cls))

## Body of the script
set_seed(args.seed)

# Create the embeddings of the data
## NLP Model and data-preprocessing
tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
model = AutoModel.from_pretrained(args.model,
                                  local_files_only = True,
                                  output_hidden_states = True)
# Add our special tokens
tokenizer.add_special_tokens({'additional_special_tokens': ['[GENE]', '[TARGET]', '[/TARGET]']})

# Resize the embedding space of our model
model.resize_token_embeddings(len(tokenizer))

# Prepare the data
data_dict = DatasetDict({"train": Dataset.from_pandas(train[["text", "labels"]]),
                         "test": Dataset.from_pandas(test[["text", "labels"]])})

# Tokenize the data
data_token = data_dict.map(lambda sen: tokenizer_function(sen, tokenizer), batched = True)

# Remove not needed columns
for name_element, element in data_token.items():
    if '__index_level_0__' in element.features.keys():
        data_token[name_element] = element.remove_columns(["text", "__index_level_0__","labels"]) # We remove labels because we are using a base model, not one for classification
    else:
        data_token[name_element] = element.remove_columns(["text", "labels"]) # We remove labels because we are using a base model, not one for classification

# Set the correct format for the transformers training, in our case is torch
data_token.set_format("torch")

# Send the model to the gpu if available (faster)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Now that we have treated the datasets lets get the embeddings
mean_pool_embeddings_train, cls_embeddings_train = get_pooled_embeddings(data_token["train"],
                                                                         device,
                                                                         batch_size = args.batch)

mean_pool_embeddings_test, cls_embeddings_test = get_pooled_embeddings(data_token["test"],
                                                                       device,
                                                                       batch_size = args.batch)

# We have now the embeddings for the logistic regression model so we can do the
# logistic regression model
logregmodel_mean = LogisticRegression(random_state = args.seed)
logregmodel_cls = LogisticRegression(random_state = args.seed)

# Fit the training data
logregmodel_mean.fit(mean_pool_embeddings_train, data_dict["train"][:]["labels"])
logregmodel_cls.fit(cls_embeddings_train, data_dict["train"][:]["labels"])


# Get the test labels
labels_test_logreg_mean = logregmodel_mean.predict(mean_pool_embeddings_test)
labels_test_logreg_cls = logregmodel_cls.predict(cls_embeddings_test)

# Get the probabilities
probs_test_logreg_mean = logregmodel_mean.predict_proba(mean_pool_embeddings_test)
probs_test_logreg_cls = logregmodel_cls.predict_proba(cls_embeddings_test)


# Lets put everything together and save it
# create the dataframe
final_data = pd.DataFrame(columns = ["label_pool", "label_cls", "prob_0_pool", "prob_0_cls", "prob_1_pool", "prob_1_cls"])

# Add the labels
final_data['label_pool'] = labels_test_logreg_mean
final_data['label_cls'] = labels_test_logreg_cls

# Add the probabilities
final_data[["prob_0_pool", "prob_1_pool"]] = probs_test_logreg_mean
final_data[["prob_0_cls", "prob_1_cls"]] = probs_test_logreg_cls

# Now we concat
output_data = pd.concat([test, final_data], axis = 1)

# Save output
output_data.to_csv(args.out, index = False)
