# Python script that is going to change from a raw sentence file or entity file (in an app format)
# to an entity with masked genes ready for the model training, testing and sampling
# As well we are going to finally filter the columns that we need for the models

# In v2 we are going to add the changing of labels from yes and no to 1 and 0 (something that was odne with labels_change_to01.py) as
# well as the changes of column names
# Also we will add some customization of the name of the intremediate files

# In v3 we are going to remove the duplicates and solve some problems of the masking duplicating the sentences
# In v4 we are going to not use the allindexes columns because it has a lot of problems so we will only using the
# indexes columns instead (we are changing the filtering_nonGenes fucntion and also slightly masking_sentences)

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import argparse
import sys
import os

# Functions
def filtering_nonGenes(group):
    """We are going to filter the rows that have a non Gene as well as
    remove their indexes from the all indexes genes
    As well, we are going to do already some pre-processing of the allindexes so we can
    work with them easierly
    """
    
    all_pairs = list(zip(group["indexStart"].values, group["indexEnd"].values))

    group["gene_indexes"] = [all_pairs] * len(group) # If we dont multiply it it gives to each row an element of the list
    return group

def masking_sentences(row, column):
    """We are masking with this function all of the genes of the sentence
    
    These indexes are based on the R indexes which are 1 based"""
    # Define the replacement value
    gene = "[GENE]"
    target = "[TARGET][GENE][/TARGET]"
    
    # Get the sentence to mask
    sentence = row["sentence"]


    # If there is only 1 gene we know that is going to be the target and we just return it
    if len(row["gene_indexes"]) == 1:
        sentence = sentence[:row["indexStart"]-1]+target+sentence[row["indexEnd"]:]
    else: # There is more than 1 gene to mask
        # Get all the indexes
        target_gene = [row["indexStart"], row["indexEnd"]]

        # Sort the indexes descending so we dont mess up with the indexes as we replace
        #indexes_sorted = sorted(indexes, key=lambda x: x[0], reverse = True)
        indexes_sorted = sorted(row["gene_indexes"], 
                        key = lambda x: x[0], 
                        reverse = True) # We do it reverse because if we go back to front it doesnt change the other indexes

        # Loop through the indexes
        for index_start, index_end in indexes_sorted:
            # print(index_start)
            # print(index_end)
            # print()
            if index_start == target_gene[0] and index_end == target_gene[1]:
                sentence = sentence[:index_start-1]+target+sentence[index_end:]
            else:
                sentence = sentence[:index_start-1]+gene+sentence[index_end:]
    
    row[column] = sentence

    return row

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("file", help = "name of the file to transform")
parser.add_argument("out", help = "name of the file to save the transformed sentences")
parser.add_argument("-columnAdd", help = "column name to add", default = "masked")
parser.add_argument("-columnOriginal", help = "column that is going to be read to change", default = "sentence")
parser.add_argument("-inter", help = "if activated returns intermidiate dataframes", action = "store_true")
parser.add_argument("-iter", help = "if argument inter activated this will be a marker of the intermidiate files", type = int)
parser.add_argument("-folderInter", help = "if argument inter activated a folder needs to be given to store the intermediate files")

args = parser.parse_args()

# checks of arguements
if not os.path.isfile(args.file):
    print(f"ERROR: file {args.file} cannot be found")
    sys.exit(1)
else:
    data = pd.read_csv(args.file)

if args.columnOriginal not in data.columns:
    print(f"ERROR: column {args.columnOriginal} cannot be found in {args.file}")
    sys.exit(1)

if args.columnAdd in data.columns:
    print(f"ERROR: column {args.columnAdd} is already a column in {args.file} and it will be overwritten")
    sys.exit(1)

if any(column not in data.columns for column in ["pmid", "number", "NotGeneError", "indexStart", "indexEnd", "sentence", "label"]):
    print(f"ERROR: columns 'pmid', 'number', 'indexStart', 'indexEnd', 'sentence', 'label' and 'NotGeneError' need to be in the file {args.file} if filtering of genes is wanted")
    sys.exit(1)

if args.inter:
    if args.iter == None:
        print("ERROR: if argument -inter is given the argument -iter needs to be given as well")
        sys.exit(1)
    if not args.folderInter:
        print("ERROR: if argument -inter is given the argument -folderInter needs to be given as well")
        sys.exit(1)
    if not os.path.exists(args.folderInter):
        os.makedirs(args.folderInter)
        print(f"Directory {args.folderInter} has been created")

# Lets filter the first by duplicates. This is the only thing that is going to change the v3

data.drop_duplicates(inplace = True)
data.reset_index(drop = True, inplace = True)

# Filter the non gene rows and indexes
# In v4 we are not going to use the columns all Indexes so we can just filter by the NotGeneError column
data["NotGeneError"] = data["NotGeneError"].fillna(False)
data = data[data["NotGeneError"] == False]


#data = data.groupby(["pmid","number"]).apply(filtering_nonGenes)
data = data.groupby(["pmid", "number"], group_keys = True).apply(filtering_nonGenes, include_groups = False).reset_index(drop = False)
# data.to_csv(args.out, index = False)
# quit()
data.set_index("level_2", inplace = True) # The level_2 is teh original index that comes from the reset_index()

if args.inter:
    data.to_csv(os.path.join(args.folderInter, f"filtered_and_indexes_preprocessed_middle_iter{args.iter}.csv"), index = False)

# Now we mask the genes
# First we add the column for the masked sentence
data[args.columnAdd] = None

# Then we apply for every row the masking
masked_dataframe = data.apply(lambda row: masking_sentences(row, args.columnAdd), axis = 1)


if args.inter:
    masked_dataframe.to_csv(os.path.join(args.folderInter, f"masked_sentences_middle_iter{args.iter}.csv"), index = False)

# Change the labels from yes to no
if not masked_dataframe["label"].isna().all():
    masked_dataframe["label"] = masked_dataframe["label"].map({"Yes":1, "No":0})

# Rename columns to the ones that the nlp model will read
masked_dataframe.rename(columns = {"label":"labels"},
                        inplace = True)

# Filter columns
columns_get = ["pmid", "number", args.columnAdd, "labels"]
out = masked_dataframe[columns_get]

# Save the output
out.to_csv(args.out, index = False)