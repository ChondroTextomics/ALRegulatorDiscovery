"""
Convert the sentence-level output of the gene pipeline into a gene-mention table
(one row per gene) with their correspondent metadata.

The script (in a nutshell):
    1. Converts the string lists ("['172', '84']") into real Python lists.
    2. Corrects the start/end character indexes so they match the sentence text
       as R reads it (1-based, inclusive end) and removes the offset that GNorm2
       adds because it processes title and abstract together.
    3. Splits every sentence row into one row per gene mention.
    4. Removes duplicate mentions (same pmid, number, start, end), keeping the
       one that has a normalised NCBI id over the one with "-" so we have 1 row
       per gene-text
"""


## Packages
import pandas as pd
import sys
import os
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "input file that is going to be transformed", required = True)
parser.add_argument("-output", help = "name of the file where the results will be stored", required = True)
args = parser.parse_args()

if not os.path.isfile(args.input):
    sys.exit(f"Error: file {args.input} does not exist")
else:
    data = pd.read_csv(args.input)

    # Lets check that the columns that we are going to use exist in the dataframe
    if all(col in data.columns for col in ["pmid", "number","start", "end", "text", "gene", "id", "uniprotid", "sa"]) == False:
        sys.exit(f'Error: We need the following columns to be in {args.input}: pmid, number, start, end, text, gene, id, uniprotid, sa')

# Functions
def format_index_list(text_indexes, number_sentence, start = False):
    """
    This is a function that will take a list in string format and will convert it in
    a real list.
    As well, it will extract the needed numbers to make it in indexes that the R app
    can take and will display correctly.
    It will be used the same one for the start and the end indexes.

    This is the same function as the one in modelToLabellingFormatting.py
    """

    # The format of the input is "['172', '84']"

    # Sentences without genes can be empty (NaN)
    if pd.isna(text_indexes):
        return []

    # Firt we need to remove the characters ', spaces, [ and ]
    text_indexes = str(text_indexes).translate({ord(i): None for i in "' []"})

    # If the list was empty ("[]") there are no indexes
    if text_indexes == "":
        return []

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

def str_list_to_list(data):
    # Sentences without genes can be empty (NaN)
    if pd.isna(data):
        return []

    # We remove the characters ', [ and ] of the text
    data = str(data).translate({ord(i): None for i in "'[]"})

    # If the list was empty ("[]") there are no elements
    if data.strip() == "":
        return []

    # Create the initial list
    data = re.split(", |,", data)

    return data
     
def expand_row(original_df):
        for row in original_df.itertuples():
            for gene, index_start, index_end, ncbid, uniprotid, sa in zip(row.gene, row.start_f, row.end_f, row.id, row.uniprotid, row.sa):
                yield {"pmid": row.pmid,
                       "number": row.number,
                       "text": row.text,
                       "gene": gene,
                       "start": index_start,
                       "end": index_end,
                       "id": ncbid,
                       "uniprotid": uniprotid,
                       "sa": sa}

# Body of the script
# We are going to apply the formatting of the indexes to the start and end column
# We need to do axis = 1 because we need to extract different information from the same row
data["start_f"] = data.apply(lambda x: format_index_list(x["start"], x["number"], start = True), axis = 1)
data["end_f"] = data.apply(lambda x: format_index_list(x["end"], x["number"], start = False), axis = 1)

# We need to transform some columns that ave lists as strings in real lists
data["gene"] = data["gene"].apply(lambda x: str_list_to_list(x))
data["id"] = data["id"].apply(lambda x: str_list_to_list(x))
data["uniprotid"] = data["uniprotid"].apply(lambda x: str_list_to_list(x))
data["sa"] = data["sa"].apply(lambda x: str_list_to_list(x))

# Now we need to create the individual rows for each gene
df_new = pd.DataFrame(expand_row(data))

# If there are no genes at all we save the empty table and stop
if df_new.empty:
    print(f"Warning: no gene mentions found in {args.input}")
    df_new.to_csv(args.output, index = False)
    sys.exit(0)

# Now we need to remove the duplicated ones if existed
# We creat e a holder column
df_new['has_dash'] = (df_new['id'] == ('-'))

# Now we drop the duplciates but we take, if it has, the oens that have normalised it
# The sort is stable so, if there are more than one with ids, the first one in the original order is kept
df_cleaned = (df_new.sort_values('has_dash', ascending = True, kind = 'stable') # When sorted, False is 0 and True is 1 so we will have the False first
              .drop_duplicates(subset=["pmid", "number", "start", "end"], keep = 'first') # We want to select the falses (not hash but ids) which will be first, if both options
              .drop(columns=['has_dash']))

df_cleaned.to_csv(args.output, index = False)

