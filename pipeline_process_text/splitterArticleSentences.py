# Python script that will:
# - read the csv with the pmid, abstract and title
# - fuse title and abstract
# - sentence splitter that text
# - create a table with the pmid and sentence
# - save that table


# Packages
import pandas as pd # treat the table
from flair.splitter import SciSpacySentenceSplitter # split the sentences
# we need to install both flair and scispacy for this because flair is a wrapper
# as well we need to download the model 'en_core_sci_sm'
import os
import sys
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "file with pmid, title and abstract of articles in table format", required = True)
parser.add_argument("-out", help = "output file that will contain the divided sentences of those articles according to SciSpacySentenceSplitter", required = True)
args = parser.parse_args()

if os.path.exists(args.out):
    answer = input(f"The file '{args.out}' given for -out already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -out file already exists and was not replaced.")

if os.path.exists(args.input):
    dataArticles = pd.read_csv(args.input)
else:
    print(f"ERROR: file {args.input} cannot be found")
    sys.exit(1)

if any(column not in dataArticles.columns for column in ["pmid", "title", "abstract"]):
    print(f"ERROR: columns 'pmid', 'title' and 'abstract' need to be in file {args.input}")
    sys.exit(1)

# Body of the script
columns_fuse = ["title", "abstract"]

print("\nReading articles csv data\n")

# Initiate sentence splitter
splitter = SciSpacySentenceSplitter()

# create the dataframe pmid - sentence for each title+abstract
dataSentencesPMID = pd.DataFrame(columns = ["pmid", "sentence"])

# Sometimes we will have abstracts that are not available and they will produce an error after
# We replace those with a space
dataArticles.fillna(" ", inplace = True)

print("\nSplitting text into sentences, it could take some time...")
for index, row in dataArticles.iterrows():
    textSplit = " ".join(row.get(columns_fuse).values)
    sentences = splitter.split(textSplit)
    # create the dataframe of the article
    sentencesArticle = pd.DataFrame(data = {"pmid": [row["pmid"]]*len(sentences),
                                            "sentence": [text.to_original_text() for text in sentences]})
    
    # Fuse with the dataframe that we have already
    dataSentencesPMID = pd.concat([dataSentencesPMID, sentencesArticle], ignore_index = True)

print(f"\nSaving data in {args.out}")
# Save the dataframe
dataSentencesPMID.to_csv(args.out, header = True, index = False)
print("\nData processed and saved!")
