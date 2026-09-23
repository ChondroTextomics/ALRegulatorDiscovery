# Fusing the predictions of the nlp model
# with the table with all the extra info of that gene that ahs been
# given by GNorm2

# What we are going to do is get the indexes of the nlp prediction ones
# we did the mistake of remove them at some moment so we need to add them now again
# and then merge by pmid+number+index start+index end

"""
Note for me here to remove after because I am going to take this one to change
this script to make it better because this was an actual patch

"""

## Packages
import re
import pandas as pd
import argparse
import os
import sys

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-metadata", help = "path to the file that will have the emtadata of the genes such as original text, uniprot id, specie, etc. The indexes should be 1-based", required = True)
parser.add_argument("-interFile", help = "path of a file in which we have the masked gene with the original index", required = True)
parser.add_argument("-labels", help = "path to the file that has the predicted (and probabilities) or annotated labels", required = True)
parser.add_argument("-output", help = "path to store the merged dataset (all columns will be merged and equal column names will have suffixes added)", required = True)
parser.add_argument("-interFolder", help = "fodler to store the intermidiate files that come from merging")
args = parser.parse_args()

# checks
if not os.path.isfile(args.metadata):
    print(f"Error: file {args.metadata} does not exist")
else:
    metadata = pd.read_csv(args.metadata)

    # Lets check that the columns that we are going to use exist in the dataframe
    if all(col in metadata.columns for col in ["pmid", "number","start", "end"]) == False:
        sys.exit(f'Error: We need the following columns to be in {args.metadata}: pmid, number, start, end')

if args.interFolder and not os.path.isdir(args.interFolder):
    print(f"Folder {args.interFolder} does not exist, creating it")
    os.makedirs(args.interFolder)

if not os.path.isfile(args.interFile):
    print(f"Error: file {args.interFile} does not exist")
else:
    inter = pd.read_csv(args.interFile)

    # Lets check that the columns that we are going to use exist in the dataframe
    if all(col in inter.columns for col in ["pmid", "number","indexStart", "indexEnd"]) == False:
        sys.exit(f'Error: We need the following columns to be in {args.interFile}: pmid, number, indexStart, indexEnd')

if not os.path.isfile(args.labels):
    print(f"Error: file {args.labels} does not exist")
else:
    labels = pd.read_csv(args.labels)

    # Lets check that the columns that we are going to use exist in the dataframe
    if all(col in labels.columns for col in ["pmid", "number"]) == False:
        sys.exit(f'Error: We need the following columns to be in {args.labels}: pmid, number')
    if any(col in labels.columns for col in ["start", "end"]):
        sys.exit(f"Error: 'start' or 'end' column in {args.labels}, this will be overwritten, so change the names of the columns")


## Functions
def get_indexes(text):
    match = re.search(r"\[TARGET\]\[GENE\]\[\/TARGET\]", text) # Only returns only the first occurence
    if match:
        start, end = match.span()
        return (start+1, end+1) # The metadata index will be 1 based so we need to add 1 to both of them
    return (None, None) # If we get here is because there is no match
    

## Body of the script
# Lets extract the indexes of the prediction file
spans = labels["text"].apply(get_indexes).to_list()

span_df = pd.DataFrame(spans, columns=['start', 'end'])
labels_indexes = pd.concat([labels, span_df], axis = 1)

# Lets create the indexes of the original one that is targetered
spans_original = inter["text"].apply(get_indexes).to_list()
span_df_original = pd.DataFrame(spans_original, columns=['start_masked', 'end_masked'])
inter_indexes = pd.concat([inter, span_df_original], axis = 1)
if args.interFolder:
    inter_indexes.to_csv(os.path.join(args.interFolder, "interFile_withCalculated_masked_indexes.csv"), index = False)

# with this intermidiate we can track the original metadata with the masked
# lets merge the metadata with the intermidiate
metadata_merged_indexes = inter_indexes.merge(metadata,
                                              how = "inner",
                                              left_on = ["pmid", "number", "indexStart", "indexEnd"],
                                              right_on = ["pmid", "number", "start", "end"],
                                              suffixes = ("_inter", "_metadata"))

if args.interFolder:
    metadata_merged_indexes.to_csv(os.path.join(args.interFolder, "metadata_interFile_merged.csv"), index = False)
    # This one is done correctly, the non genes are removed and the other are okay
    # This one looks good so now we need to merge it with the prediction ones

# Now we have basically that bridge of information and we need to fuse the other one
final_merged = metadata_merged_indexes.merge(labels_indexes,
                                             how = "inner", #  we just want the one that we have rpedictions from and also the name of genes
                                             left_on=["pmid", "number", "start_masked", "end_masked"],
                                             right_on=["pmid", "number", "start", "end"],
                                             suffixes = ("_inter_metadata", "_labels"))

final_merged.to_csv(args.output, index = False)
print(f"""Intermediate: {inter_indexes.shape}
Metadata: {metadata.shape}
Labels: {labels_indexes.shape}
Merged Inter-metadata: {metadata_merged_indexes.shape}
Merged inter-metadata-labels: {final_merged.shape}""")