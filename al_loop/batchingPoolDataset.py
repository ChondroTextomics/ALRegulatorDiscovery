# Generating batches of a specific CSV
# Destiend to do batches of a pool dataset so the prediction
# and rest of the pipeline can be parallelised

import argparse
import os
import sys
import pandas as pd
import math

parser = argparse.ArgumentParser(description = "Split a CSV file (with header) into N batch CSV files of roughly equal size, "
                                               "so downstream steps (e.g. prediction) can run in parallel.")
parser.add_argument("-input", help = "path to the input CSV file to split (must have a header row)", required = True)
parser.add_argument("-batches", help = "number of batches to split the file into; each batch gets at most ceil(rows / batches) rows", required = True, type = int)
parser.add_argument("-out", help = "output folder for the batch files (created if it does not exist)", required = True)
parser.add_argument("-prefix", help = "file name prefix for the batches; files are saved as <prefix>_<batch_number>.csv, numbered from 0 (e.g. -prefix pool gives pool_0.csv, pool_1.csv, ...)", required = True)
args = parser.parse_args()

# Checks
if os.path.isfile(args.input):
    data = pd.read_csv(args.input)
    
else:
    print(f"ERROR: file {args.input} cannot be found")
    sys.exit(1)

if not os.path.exists(args.out):
    os.makedirs(args.out)
    print(f"Folder {args.out} created!")

batch_size = math.ceil(len(data) / args.batches)

print(f"Creating {args.batches} of max {batch_size}")

for num_batch in range(0, args.batches):
    batch = data.iloc[num_batch*batch_size:(num_batch*batch_size) + batch_size]
    batch.to_csv(os.path.join(args.out, f"{args.prefix}_{num_batch}.csv"), index = False)
