# We are going to get the embeddings and get the coreset

import os
import sys
import pandas as pd
import numpy as np
from small_text.query_strategies import coresets
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-embeddings", help = "path to the file with the embeddings of the data", required = True)
parser.add_argument("-selection", help = "number of sentences to select/return", type = int, required = True)
parser.add_argument("-metadata", help = "path to the file with the information of teh sentences of '-embeddings'", required = True)
parser.add_argument("-output", help = "file to save the selected rows of the data", required = True)
parser.add_argument("-seed", help = "random seed set for reproducible selection", default = 42, type = int)
args = parser.parse_args()

# Check arguments
if not os.path.isfile(args.embeddings):
    print(f"ERROR: file {args.embeddings} cannot be found")
    sys.exit(1)
else:
    data_raw = pd.read_csv(args.embeddings, index_col = 0)

if not os.path.isfile(args.metadata):
    print(f"ERROR: file {args.metadata} cannot be found")
    sys.exit(1)
else:
    metadata = pd.read_csv(args.metadata)

if data_raw.shape[0] != metadata.shape[0]:
    print(f"ERROR: '-embeddings' ({data_raw.shape[0]} rows) and '-metadata' ({metadata.shape[0]} rows) do not have the same number of rows")
    sys.exit(1)

if args.selection > data_raw.shape[0]:
    print(f"ERROR: -selection ({args.selection}) cannot be greater than the number of rows available ({data_raw.shape[0]})")
    sys.exit(1)

if os.path.exists(args.output):
    answer = input(f"The file '{args.output}' given for -out already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -out file already exists and was not replaced.")

## Functions
# This function comes from https://github.com/webis-de/small-text/blob/v2.0.0.dev1/small_text/query_strategies/coresets.py
# It has been changed because it was returning constantly runtime warning because of this (RuntimeWarning: invalid value encountered in arccos)
def safe_cosine_distance(a, b, normalized=False):
    sim = np.matmul(a, b.T)
    if not normalized:
        sim = sim / np.dot(np.linalg.norm(a, axis=1)[:, np.newaxis],
                           np.linalg.norm(b, axis=1)[np.newaxis, :])
    sim = np.clip(sim, -1.0, 1.0)  # <- This is the fix that I had to do because of the np.arccos(sim) being called on values slightly outside [-1, 1], due to floating point error (e.g., 1.0000001 or -1.0000001).
    return np.arccos(sim) / np.pi

# Introduce patched function into the library
coresets._cosine_distance = safe_cosine_distance
coresets._cosine_distance_matrix = safe_cosine_distance  # in case you hit this directly

## Body of script
np.random.seed(args.seed) # for reproducibility

# read the embeddings
embeddings = data_raw.iloc[:, 3:].to_numpy()

# we are going to normalize because we use cosine and when set the function to normalized=false we have some warnings
# embeddings = normalize(embeddings, norm='l2', axis=1) # If we uncoment this one we need to set normalized = True in greedy_coreset
number_total_samples = embeddings.shape[0]

indices_unlabeled = np.array(list(range(0, number_total_samples)), dtype = int)
# greedy_coreset needs at least 1 index but it is initialized randomly in the original algorithm
# we need to give it here because usually it is dealth with the GreedyCore query but we are using only the
# function
not_included_point = np.random.choice(indices_unlabeled)

indices_labeled = np.array([not_included_point], dtype=int)
# Lets remove that index from the unlabeled
indices_unlabeled = np.setdiff1d(indices_unlabeled, indices_labeled)

selected_indices = coresets.greedy_coreset(
    embeddings,
    indices_labeled = indices_labeled,
    indices_unlabeled = indices_unlabeled,
    n = args.selection-1, # number of samples we want in our corset -1 because we are going to include the excluded randomly
    distance_metric = "cosine",
    normalized = False # They are not normalized so they need to me normalized
)

final_indices = np.concatenate([indices_labeled, selected_indices])
# We have the final indices, now we ened to return simply the sentences with those indices
data_selected = data_raw.iloc[final_indices]

# Lets fuse it with the metadata one and give the final results
data_selected_final = metadata.merge(
    data_selected[["pmid","number","text"]].drop_duplicates(),
    on=["pmid","number","text"],
    how='inner'
)

data_selected_final.to_csv(args.output, index = False)