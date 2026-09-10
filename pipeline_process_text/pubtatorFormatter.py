# Python script that is going to transform the sentences to pubtator format
# This pubtator format is the one that need to be changed to be in the input of GNORM2
# This script is an update and will be able to give me sentences and abstarcts
# in pubtator format

import pandas as pd
import sys
import os
import argparse

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "file with pmid, title and abstract of articles in table format", required = True)
parser.add_argument("-out", help = "output file that will contain the divided sentences of those articles according to SciSpacySentenceSplitter", required = True)
parser.add_argument("-structure", help = "format of the text, either sentence or abstract", choices = ["sentence", "abstract"], required = True)
args = parser.parse_args()

# Checks of arguments

if os.path.exists(args.out):
    answer = input(f"The file '{args.out}' given for -out already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -out file already exists and was not replaced.")

if os.path.isfile(args.input):
    print(f"Reading file {args.input}\n")
    text = pd.read_csv(args.input)
else:
    sys.exit(f"ERROR: file {args.input} cannot be found")

if args.structure == "sentence" and "sentence" not in text.columns:
    sys.exit(f"ERROR: if sentences are going to be transformed file {args.input} needs to have a column called 'sentence'")
if args.structure == "sentence":
    if any(column not in text.columns for column in ["pmid", "sentence"]):
        sys.exit(f"ERROR: columns 'pmid' and 'sentence' need to be in file {args.input}")

if args.structure == "abstract" and "abstract" not in text.columns:
    sys.exit(f"ERROR: if abstracts are going to be transformed file {args.input} needs to have a column called 'abstract'")
if args.structure == "abstract":
    if any(column not in text.columns for column in ["pmid", "title", "abstract"]):
        sys.exit(f"ERROR: columns 'pmid', 'title' and 'abstract' need to be in file {args.input}")
    
# Functions
def format_sentence(sentence):
    # We format it in a way that GNorm can read it assuming that the first line of all of them are titles
    if sentence['number_group'] == 1:
        return f"{sentence['pmid']}_{sentence['number_group']}|t|{sentence['sentence']}\n{sentence['pmid']}_{sentence['number_group']}|a|-"
    else:
        return f"{sentence['pmid']}_{sentence['number_group']}|t|-\n{sentence['pmid']}_{sentence['number_group']}|a|{sentence['sentence']}"

def format_abstract(abstract):
    # Establish the initial values
    text_title = abstract['title']
    text_abstract = abstract["abstract"]

    # Check if any of them is empty
    if pd.isna(abstract['title']):
        text_title = "-"
    if pd.isna(abstract["abstract"]):
        text_abstract = "-"

    return f"{abstract['pmid']}|t|{text_title}\n{abstract['pmid']}|a|{text_abstract}"

def pubtator_transform(table, structure):
    if structure == "sentence":
        # Here we group the sentences by the id so we can identify them after and for each one we format the sentence
        table["number_group"] = table.groupby("pmid").cumcount() + 1
        pubtator_text = "\n\n".join(table.apply(format_sentence, axis = 1))
    elif structure == "abstract":
        pubtator_text = "\n\n".join(table.apply(format_abstract, axis = 1))
    else:
        raise Exception(f"The structure '{structure}' is not recognized")
    
    return pubtator_text + "\n"

def sentences_to_pubtator_file(table, filename, structure):
    if structure not in ["abstract", "sentence"]:
        raise Exception(f"The structure '{structure}' is not recognized")

    # format the text
    formatted_text = pubtator_transform(table, structure)
    # Write the file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(formatted_text)
        f.write("\n") # This is neccessary because PubTator format has 2 endlines and this way we dont get the error in gnorm2


# Body of the script
# Read the file
rows_before_droppingNA = text.shape[0]

if args.structure == "sentence":
    print("Removing blank lines")
    text.dropna(subset = ["sentence"], inplace = True)
    print(f"Sentences that have been removed: {rows_before_droppingNA - text.shape[0]}\n")
else:
    print("Removing blank lines")
    text.dropna(subset = ["title","abstract"], how = "all", inplace = True) # Remove lines when 
    print(f"Articles that have been removed: {rows_before_droppingNA - text.shape[0]}\n")

# Give the text to our function
print("Processing sentences...\n")
sentences_to_pubtator_file(text, args.out, args.structure)
print(f"Data saved in {args.out}")