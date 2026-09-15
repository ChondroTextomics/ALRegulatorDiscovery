# Clustering of the sentences given a cls embedding file
# This is going to be done in CPU but it will require quite a lot of
# RAM

# We are doing precomputed distance because we need to calculate it either way


import argparse
import os
import sys
import pandas as pd
from sklearn.metrics.pairwise import cosine_distances
import math

# Arguments to give to the script
parser = argparse.ArgumentParser()
parser.add_argument("-embeddings",
                    help = "file containing the embeddings",
                    required = True)
parser.add_argument("-matrixFolder",
                    help = "folder for the cosine batches",
                    required = True) # need to be created previously so it does not interfer the pararlel processes
parser.add_argument("-matrixPrefix",
                    help = "prefix to each one of the h5 batches files, it will be followed by an underscore, number of batch and extension",
                    required = True)
parser.add_argument("-batches",
                    help = "number of batches that the embeddings are going to be split",
                    type = int,
                    required = True)
parser.add_argument("-numberBatch",
                    help = "the number of the batch that is being processed in this script",
                    type = int,
                    required = True) # If there are no batches, this should be 0
args = parser.parse_args()

# Checks
if os.path.isfile(args.embeddings):
    cls = pd.read_csv(args.embeddings)
else:
    print(f"ERROR: file {args.embeddings} cannot be found")
    sys.exit(1)

if not os.path.exists(args.matrixFolder):
   print(f"ERROR: folder {args.matrixFolder} does not exist, create it before proceeding")
   sys.exit(1)

## ---------------------------------------
## Cosine distances

# Create the cosine distance matrix
batch_size = math.ceil(len(cls) / args.batches)
num_batch = args.numberBatch

# What we are doing here is doing little by little the cosine similarity
batch = cosine_distances(cls.iloc[num_batch*batch_size:(num_batch*batch_size) + batch_size],
                         cls)
dataframe = pd.DataFrame(batch)
dataframe.to_csv(os.path.join(args.matrixFolder, f"{args.matrixPrefix}_{num_batch}.csv"), index = False)