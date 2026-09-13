# Script that is going to be used to get different data that is labelled
# and put them together in a new one
# The catch is that only the ones that doesnt correspond or doesnt exist in 1 of the files
# are going to be selected

# Packages
import pandas as pd
import numpy as np
from functools import reduce
import argparse
import sys
import os

import warnings
warnings.filterwarnings("ignore")

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-files", help = "files that will be checked and merged for values that does not match", required = True, nargs = "+")
parser.add_argument("-curators", help = "names of the curators that have labelled each one of the files, they need to be in the same order as the files", required = True, nargs = "+")
parser.add_argument("-out", help = "name of the file that the merged and filtered rows will be stored", required = True)
parser.add_argument("-finalDecision", help = "name of the curator that is going to be added as the final decision, by default is called 'Final'", default = "Final")
parser.add_argument("-group", help = "if activated it will group the sentences together and then shuffled", action = "store_true")
parser.add_argument("-seed", help = "seed for the random shuffling if -group is activated, default 20", default = 20, type = int)
args = parser.parse_args()

# Checking arguments
# Check that the number of files is same as number of curators
if len(args.files) != len(args.curators):
    print("ERROR: the number of files and the name of curators must be the same")
    sys.exit(1)

# Check that all the files exist
dataframes = []
for name_file, curator in zip(args.files, args.curators):
    # Check that the files have the same columns for the concatenation
    if not os.path.isfile(name_file):
        print(f"ERROR: file {name_file} does not exist")
        sys.exit(1)
    
    frame = pd.read_csv(name_file)
    # Check that all the files have the id columns("pmid","number","sentence","allGenesIndexStart","allGenesIndexEnd","indexStart","indexEnd") and the "label" column
    if not all(column in frame.columns for column in ["pmid","number","sentence","allGenesIndexStart","allGenesIndexEnd","indexStart","indexEnd", "label"]):
        print(f'ERROR: all columns "pmid","number","sentence","allGenesIndexStart","allGenesIndexEnd","indexStart","indexEnd", "label" need to be in file {name_file}')
        sys.exit(1)
    elif any(col.startswith("label_") for col in frame.columns):
        print(f"ERROR: {name_file} has some column that starts with 'label_' and that will interfere with the merging process")
        sys.exit(1)
    else:
        # Add the name of the curator in the dataframe
        frame["Curator"] = curator
        dataframes.append(frame)

# Check that the dataframes have the same columns
columns_dataframe = dataframes[0].columns
for df in dataframes:
    if set(columns_dataframe) != set(df.columns):
        print("ERROR: all files should have the same columns, they can be in a different order but all of them should have the same ones")
        sys.exit(1)

# Merge the dataframes by the identifier list
id_list = ["pmid","number", "indexStart", "indexEnd"] # These for give the id of the sentence, bth all indexes and sentence will be in a lot of them

df_suffixes = []

for i, data in enumerate(dataframes):
    if i == 0:
        df_suffixes.append(data[id_list+["label"]]) # For the merge part we dont need all of the columns, just the ids and the label (because we are going to filter on it)
    else:
        df_suffixes.append((data[id_list+["label"]], f"_{i+1}")) # We add the suffixes in case that there is more than 3 dataframes so the column names are not overlapped


merged_dataframe = reduce(lambda left, right: left.merge(right[0],
                                                         how = "outer", # we want all of the ids
                                                         on = id_list,
                                                         suffixes = ("", right[1])), df_suffixes)

# We obtain a lot of columns but the ones that we are interested are the label ones
label_columns = merged_dataframe.columns[merged_dataframe.columns.map(lambda x: x.startswith("label_"))]

# We obtain the rows that dont have the same label value in all of the files given
# As well as the ones that are unclear
different_label_df = merged_dataframe[~merged_dataframe.apply(lambda row: all(row["label"] == row[column] for column in label_columns), axis = 1)] # Rows with different labels are taken
unclear_label_df = merged_dataframe[merged_dataframe.apply(lambda row: any("Unclear" == row[column] for column in label_columns), axis = 1)] # Rows with any unclear are taken

different_unclear_merged_df = pd.concat([different_label_df, unclear_label_df])
different_unclear_merged_df.drop_duplicates(subset = id_list, inplace = True) # It is possible for duplicates for rows with unclear

# We are going to extract the sentences with different values from the original dataframes so we are going to
# record the dataframe with only the ids
keep_rows = different_unclear_merged_df[id_list]

# Now we are going to create the final dataframe that will be concatenating the rows of all the dataframes given (filterred)
final_df = pd.DataFrame(columns = dataframes[0].columns)
columns_add_curator_df = list(dataframes[0].columns)
columns_add_curator_df.remove("Curator")
added_curator_df = pd.DataFrame(columns = columns_add_curator_df) # This is going to be the one with the final curator

# We concatenate the dataframes filterred
# As well we add the respective dataframes but with the Final curator
for df in dataframes:
    # We filter the given dfs and concatenate it to the final df
    keep_from_df = df.merge(keep_rows, how = "inner", on = id_list)
    keep_from_df.dropna(axis = 1, how = "all")
    final_df = pd.concat([final_df, keep_from_df],
                         axis = 0,
                         ignore_index = True)
    
    # We create the Final curator one
    added_curator_df = pd.concat([keep_from_df.drop(columns = ["Curator"]), added_curator_df],
                                  axis = 0,
                                  ignore_index = True)

# Empty the columns that need to be filled in the revision app
added_curator_df[[col for col in added_curator_df.columns if col not in ["pmid","number","sentence","allGenesIndexStart","allGenesIndexEnd","indexStart","indexEnd"]]] = np.nan
# Drop the duplciates rows (there are going to be a lot of duplicates in the final dataframe)
added_curator_df.drop_duplicates(subset = id_list, inplace = True)
# Add to the final curator the curator column
added_curator_df["Curator"] = args.finalDecision

# Lets fuse the filtered rows with the added curator one
final_df = pd.concat([final_df, added_curator_df],
                     axis = 0,
                     ignore_index = True)

# Group and shuffle the sentences
if args.group:
    # group by the id columns
    group_sentences = list(final_df.groupby(["pmid", "number"]))

    # shuffle the groups
    np.random.seed(args.seed)
    np.random.shuffle(group_sentences)

    # concatenate the groups
    final_df = pd.concat([group for _, group in group_sentences], ignore_index = True)

# Now we just give the final document
final_df.to_csv(args.out, index = False)
# This final file will have the rows that dont have the same label in all the given files in a way that can be filled in a revision app
# as well as the rows that have made the discordance, but it wont have empty lines so if that line didnt exist in one of the dataframes, it will
# not be included and can be assumed that everything is NA in the app

print("Program finished! :)")