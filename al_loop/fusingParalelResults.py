# Script that will be the last step of the pipeline
# it will take the files with different predictions
# one bald and the other file with cluster and label

# as well, it will take optionally the folder where the

import argparse
import os
import sys
import pandas as pd

## Arguments to give to the script
parser = argparse.ArgumentParser()
parser.add_argument("-bald", help = "file path with the bald predictions", required = True)
parser.add_argument("-label", help = "file path with label predictions", required = True)
parser.add_argument("-cluster", help = "file path with cluster predictions", required = True)
parser.add_argument("-out", help = "name of the file where teh resuts fused will be given", required = True)
args = parser.parse_args()

# Checks
if not os.path.isfile(args.bald):
    print(f"ERROR: file {args.bald} cannot be found")
    sys.exit(1)
else:
    bald = pd.read_csv(args.bald)

if any(column not in bald.columns for column in ["pmid", "number", "text", "BALD"]):
    print(f"ERROR: columns 'pmid', 'number', 'text', 'BALD' need to be in file {args.bald}")
    sys.exit(1)

if not os.path.isfile(args.cluster):
    print(f"ERROR: file {args.cluster} cannot be found")
    sys.exit(1)
else:
    cluster = pd.read_csv(args.cluster)

if any(column not in cluster.columns for column in ["pmid", "number", "text", "medoid", "outlier", "cluster"]):
    print(f"ERROR: columns 'pmid', 'number', 'text', 'medoid', 'outlier' and 'cluster' need to be in file {args.cluster}")
    sys.exit(1)

if not os.path.isfile(args.label):
    print(f"ERROR: file {args.label} cannot be found")
    sys.exit(1)
else:
    label = pd.read_csv(args.label)

if any(column not in label.columns for column in ["pmid", "number", "text", "predicted_label", "logits_0", "logits_1", "prob_0", "prob_1"]):
    print(f"ERROR: columns 'pmid', 'number', 'text', 'predicted_label', 'logits_0', 'logits_1', 'prob_0' and 'prob_1' need to be in file {args.label}")
    sys.exit(1)

## Body of the script
# We are going to do merges the reuslts so we need to make sure that they have the same ones
keys = ['pmid', 'number', 'text']

set1 = set(label[keys].itertuples(index = False, name = None))
set2 = set(cluster[keys].itertuples(index = False, name = None))
set3 = set(bald[keys].itertuples(index = False, name = None))

if set1 != set2:
    print(f"ERROR: {args.label} and {args.cluster} have different 'pmid', 'number', 'text' combinations")
    sys.exit(1)

if set1 != set3:
    print(f"ERROR: {args.label} and {args.bald} have different 'pmid', 'number', 'text' combinations")
    sys.exit(1)

if set3 != set2:
    print(f"ERROR: {args.bald} and {args.cluster} have different 'pmid', 'number', 'text' combinations")
    sys.exit(1)
    
# Lets merged them
# Lets merge first labels with the bald
# For duplicated non-key columns, keep the -label version and drop the -bald one, so the merge doesn't create '_x'/'_y' duplicates
overlap_bald_label = [column for column in label.columns if column in bald.columns and column not in keys]
bald_labels = bald.drop(columns = overlap_bald_label).merge(label, how = "inner", on = keys)

# For duplicated non-key columns with -cluster, keep the bald_labels version and drop the -cluster one
overlap_baldlabels_cluster = [column for column in cluster.columns if column in bald_labels.columns and column not in keys]
cluster_bald_labels = bald_labels.merge(cluster.drop(columns = overlap_baldlabels_cluster), how = "inner", on = keys)

# Save it
cluster_bald_labels.to_csv(args.out, index  = False)