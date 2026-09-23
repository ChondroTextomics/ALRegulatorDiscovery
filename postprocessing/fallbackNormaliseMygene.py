
# This script takes unresolved genes from, for example, GNorm2, and
# try to fill in an Entrez ID for them, then writes out a copy of the
# input file with the extra ID column merged in.

## Packages
import pandas as pd
import argparse
import os
import sys
import mygene
import time

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("input", help = "csv with the gene names")
parser.add_argument("output", help = "name of the file where the results are going to be stored")
parser.add_argument("-columnGeneName", help = "name of the column where the gene name will be", default = "gene")
parser.add_argument("-columnGeneIDGnorm", help = "name of the column where the entrez id taht comes from gnorm2", default = "id")
parser.add_argument("-columnMyGeneID", help = "column where the id will be stored", default = "id_myGene")
parser.add_argument("-symbolNoIDGNorm", help = "character that symbolises the no identification of gene ids from gnorm2", default = "-")
parser.add_argument("-inter", help = "folder where you will get intermidiate files as the ones results from merging")
args = parser.parse_args()

# checks
if os.path.isfile(args.input):
    data = pd.read_csv(args.input)

    if args.columnGeneName not in data.columns:
        print(f"ERROR: file {args.input} does not have column '{args.columnGeneName}'")
        sys.exit(1)
    
    if args.columnMyGeneID in data.columns:
        print(f"ERROR: file {args.input} have already column '{args.columnMyGeneID}' and it would be overwritten")
        sys.exit(1)
    
    if args.symbolNoIDGNorm not in data[args.columnGeneIDGnorm].values:
        print(f"ERROR: value '{args.symbolNoIDGNorm}' does not exist in column '{args.columnGeneIDGnorm}' in file {args.input}")
        sys.exit(1)

    if args.columnGeneIDGnorm not in data.columns:
        print(f"ERROR: column {args.columnGeneIDGnorm} nor in file {args.input}")
else:
    print(f"ERROR: file {args.input} cannot be found")
    sys.exit(1)

## Functions
def query_batch(mg, batch, retries = 3):
    for attempt in range(retries):
        try:
            res = mg.querymany(batch,
                       fields = "_score,entrezgene", # We dont need more
                       species = 9606,
                       scopes = "symbol,name,alias", #https://docs.mygene.info/en/latest/doc/query_service.html#available-fields
                       as_dataframe = True)
            return res
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                # split batch in half and try smaller chunks
                if len(batch) > 50:
                    print(f"  Retrying with smaller batch size...")
                    mid = len(batch) // 2
                    res1 = query_batch(mg, batch[:mid], retries=retries)
                    res2 = query_batch(mg, batch[mid:], retries=retries)
                    if res1 is not None and res2 is not None:
                        return pd.concat([res1, res2])
                time.sleep(5)
            else:
                print(f"  Batch permanently failed, skipping")
                return None

## Body of the script
# first lets get just the rows that do not have an id
data_noID = data[data[args.columnGeneIDGnorm] == args.symbolNoIDGNorm]

# Lets get the mygene object
mg = mygene.MyGeneInfo()

# Lets do the search
genes_to_search = list(data_noID[args.columnGeneName].unique()) # We get unique values of gene names
print(f"Genes to search: {len(genes_to_search)}\n")
# https://docs.mygene.info/projects/mygene-py/en/latest/#tutorial

batch_size = 500
all_results = []

for i in range(0, len(genes_to_search), batch_size): # in case that we have more than 1000 genes, which is the max
    batch = genes_to_search[i:i+batch_size]
    print(f"batch {i} to {i+batch_size}")
    res = query_batch(mg, batch, retries = 5)
    if res is not None:
        all_results.append(res)
    time.sleep(20)
    print("\n")

if not all_results:
    print("ERROR: no results were returned from mygene, all batches failed")
    sys.exit(1)

results = pd.concat(all_results)

# The index of results is the query
# we may have more than 1 match but we want the one with the highest score
results = results[~results.index.duplicated(keep='first')]
# Change the _id of the ones that have not been found
results["entrezgene"] = results["entrezgene"].fillna(args.symbolNoIDGNorm) # this way it is consistent with the ones that we have from gnorm2
results = results.reset_index()

# prepare the dataset for the merge
results_merging = results[["query", "entrezgene"]]
results_merging.rename(columns = {"query":args.columnGeneName, "entrezgene":args.columnMyGeneID}, inplace = True)
if args.inter:
    results_merging.to_csv(os.path.join(args.inter, "mergedDataframe.csv"), index = False)

final_results = data.merge(results_merging, how = "left", on = args.columnGeneName)
final_results[args.columnMyGeneID] = final_results[args.columnMyGeneID].fillna(args.symbolNoIDGNorm)

final_results.to_csv(args.output, index = False)