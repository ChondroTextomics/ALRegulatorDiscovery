# Python script to transform from the csv file that we have as an output of the formatting of pubtator
# to the format that the app needs
# This transformation consist in:
# 1. Change indexes so the gens are highlighted correctly
# 2. Transform the indexes columns in individual rows (explode the columns)
# 3. Restructure how indexes are displayed (from list to string)
# 4. Add neccessary columns for the labelling and make sure all columns have right name

## Packages
import pandas as pd
import sys
import os
import argparse
import numpy as np

## Arguments

parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "input file that is going to be transformed", required = True)
parser.add_argument("-output", help = "name of the file where the results will be stored", required = True)
parser.add_argument("-group", help = "if activated it will group the sentences together and then shuffled, if not, it is onlly shuffled", action = "store_true")
parser.add_argument("-seed", help = "seed used for shuffling, by default 28", type = int, default = 28)
args = parser.parse_args()

# Check arguments
if os.path.exists(args.output):
    answer = input(f"The file '{args.output}' given for -output already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -output file already exists and was not replaced.")

if not os.path.isfile(args.input):
    sys.exit(f"Error: file {args.input} does not exist")
else:
    data = pd.read_csv(args.input)
    file_name_output = args.output

# Lets check that the columns that we are going to use exist in the dataframe
if all(col in data.columns for col in ["pmid", "number","start", "end", "text"]) == False:
    sys.exit('We need the following columns to be in the input csv: pmid, number, start, end, text')

## Functions
def format_string_list(text_indexes, number_sentence, start = False):
    """
    This is a function that will take a list in string format and will convert it in
    a real list.
    As well, it will extract the needed numbers to make it in indexes that the R app
    can take and will display correctly.
    It will be used the same one for the start and the end indexes.
    """

    # The format of the input is "['172', '84']"

    # Firt we need to remove the characters ', spaces, [ and ]
    text_indexes = text_indexes.translate({ord(i): None for i in "' []"})

    # Create the initial list
    list_indexes = text_indexes.split(",")
    # Change the strings to numbers because they are indexes
    list_indexes = [int(index) for index in list_indexes]

    # Now we are going to change the indexes for 2 reasons:
    # 1. R has a 1 start index while python has a 0 start index
    # 2. The sentences, because of how GNorm2 works needs to have a title and abstract
    # so the indexes are not the real ones

    # For the titles, i.e., sentences where value of number is 1
    # we need to add +1 to the start index
    if number_sentence == 1 and start:
        list_indexes = [index+1 for index in list_indexes]
    # For the abstracts we need to substract one -1 for how different substraction
    # systems are taking in account in R and python; python doesnt take in account the last index while R does with substring
    # and we need to substract 2 to the end (-1 for start hyphen and -1 for how different substraction
    # systems are taking in account in R and python; python doesnt take in account the last index while R does with substring)
    elif number_sentence == 1 and not start:
        pass
    elif number_sentence != 1 and start:
        list_indexes = [index-1 for index in list_indexes]
    elif number_sentence != 1 and not start:
        list_indexes = [index-2 for index in list_indexes]
    else:
        sys.exit("Error in function 'format_string_list'")

    return list_indexes

## Body of the script
# 1.
# We are going to apply the formatting of the indexes to the start and end column
# We need to do axis = 1 because we need to extract different information from the same row
data["start_f"] = data.apply(lambda x: format_string_list(x["start"], x["number"], start = True), axis = 1)
data["end_f"] = data.apply(lambda x: format_string_list(x["end"], x["number"], start = False), axis = 1)

# 2.
# We need to create one row per each gene that there is in a sentence and we will do this
# with the explode() function of pandas
# Before that we will copy the columns because we need them as well
data["allGenesIndexStart"] = data["start_f"]
data["allGenesIndexEnd"] = data["end_f"]
data_final = data[["pmid", "number", "text", "allGenesIndexStart", "allGenesIndexEnd", "start_f", "end_f"]].explode(["start_f", "end_f"])

# 3.
# Now we need to turn the allGenes columsn into strings instead of lists
data_final["allGenesIndexStart"] = data_final["allGenesIndexStart"].map(lambda x:",".join(map(str, x)))
data_final["allGenesIndexEnd"] = data_final["allGenesIndexEnd"].map(lambda x:",".join(map(str, x)))

# 4.
# Lets rename the columns
data_final.columns = ["pmid", "number", "sentence","allGenesIndexStart","allGenesIndexEnd","indexStart","indexEnd"]

# Let's add the neccessarry columns
for col in ["label","association","experiment","proof", "errorReported","errorMoreGenes","numberGenesTotal","NotGeneError"]:
    data_final[col] = None

# Group and shuffle the sentences
if args.group:
    # group by the id columns
    group_sentences = list(data_final.groupby(["pmid", "number"]))

    # shuffle the groups
    np.random.seed(args.seed)
    np.random.shuffle(group_sentences)

    # concatenate the groups
    shuffled_df = pd.concat([group for _, group in group_sentences], ignore_index = True)

else: # Just shuffle the sentences in general
    # Shuffle the dataframe so the labelling is fairer
    shuffled_df = data_final.sample(frac = 1, random_state = args.seed)

shuffled_df.to_csv(file_name_output, index = False)