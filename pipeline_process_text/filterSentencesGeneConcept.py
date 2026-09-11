# Script to filter sentences by gene and concepts

## Packages
import pandas as pd
import ast
import os
import sys
import argparse

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "", required = True)
parser.add_argument("-concepts", help = "", required = True)
parser.add_argument("-output", help = "", required = True)
args = parser.parse_args()

if os.path.isfile(args.input):
    sentences = pd.read_csv(args.input)
else:
    print(f"ERROR: file {args.input} cannot be found")
    sys.exit(1)

if os.path.isfile(args.concepts):
    with open(args.concepts) as concepts_file:
        concepts_filter = concepts_file.read().strip().split("\n")
else:
    print(f"ERROR: file {args.concepts} cannot be found")
    sys.exit(1)

if os.path.exists(args.output):
    answer = input(f"The file '{args.output}' given for -output already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -output file already exists and was not replaced.")

## Functions
def convert_columns_to_lists(df, column_names):
    """
    Converts specified columns from string representations of lists to actual Python lists.

    Args:
        df (pd.DataFrame): The DataFrame containing the columns.
        column_names (list of str): List of column names to convert.

    Returns:
        pd.DataFrame: The DataFrame with converted columns.
    """
    for col in column_names:
        df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    return df

## Body
# Pre-process the CSV
# This is going to change over the fine tunning of the scripts but right now we need to pre-process a little bit the csv file
# that we obtain from the script fuseAndFormat_content_allEntities_uniprot.py
sentences = convert_columns_to_lists(sentences, ["gene", "start", "end", "id", "uniprotid", "sa"])

# Filter by genes first
sentences_genes = sentences[sentences["gene"].apply(lambda x: len(x) > 0)]

# Now we filter by the concepts in the list of concepts to filter
# Create a pattern to look for
pattern = '|'.join([f"\\b{keyword}\\b" for keyword in concepts_filter])  # \\b ensures word boundary

# Filter rows where the text in the column contains any of the keywords
sentences_genes_concepts = sentences_genes[sentences_genes["text"].str.contains(pattern, case = False, na = False)]

# Save the result
sentences_genes_concepts.to_csv(args.output, index = False)