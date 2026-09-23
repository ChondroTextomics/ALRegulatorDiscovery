"""
Preprocess and unify gene ID annotations, keeping only human genes.

Each input row can carry two candidate gene IDs: a "main" ID (e.g. from
gnorm2) and a "secondary" ID (e.g. from mygene, already known to be human).
Either may be missing, represented by a placeholder symbol (default "-").

Steps performed:
  1. Drop rows where both the main and secondary ID are missing (nor normalised to id so removed).
  2. Keep only rows that are human: either the main ID is present and its species column equals "9606" (NCBI taxon ID for Homo sapiens), or the
     main ID is missing but the secondary ID is present (already human-only because of how it has been obtained).
  3. Build a single "final ID" column: use the main ID when present, otherwise fall back to the secondary ID.
  4. Optionally exclude rows whose final ID appears in a separate filter file (e.g. to remove genes already covered elsewhere).
  5. Drop duplicate (final ID, label) pairs and write the result to the output CSV.
  
  If -inter is given, intermediate CSVs from each step are
  also saved to that folder for inspection/debugging.
"""

## Packages
import pandas as pd
import argparse
import os
import sys

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("input", help = "input file to process")
parser.add_argument("output", help = "file where to save the process file")
parser.add_argument("-columnLabel", help = "column with the label, predicted or annotated", required = True)
parser.add_argument("-finalIdcolumn", help = "name of the column with the final id", required = True)
parser.add_argument("-symbolNotID", help = "character that symbolises the lack of an id", default = "-")
parser.add_argument("-filter", help = "if given a file, the input file will be filtered with this file (it will be filtered with the ensemble id column, the same name as the finalIdcolumn)")
parser.add_argument("-columnFilterSpecie", help = "column to look for the human specie", default = "sa")
parser.add_argument("-columnMainID", help = "column with the main ensemble id (gnorm2 identified)", default = "id")
parser.add_argument("-columnSecondnID", help = "column with the secondary ensemble id (mygene identified and only human)", default = "id_myGene")
parser.add_argument("-inter", help = "foler path where intermidiate files will be stored")
args = parser.parse_args()

# Check arguments
if os.path.isfile(args.input):
    data = pd.read_csv(args.input)

    if any(column not in data.columns for column in [args.columnLabel, args.columnFilterSpecie, args.columnMainID, args.columnSecondnID]):
        print(f"ERROR: one or more of the neccessary columns ('{args.columnLabel}','{args.columnFilterSpecie}','{args.columnMainID}','{args.columnSecondnID}') is not in {args.input}")
        sys.exit(1)
    
    if args.finalIdcolumn in data.columns:
        print(f"ERROR: column {args.finalIdcolumn} already in file {args.input}")
        sys.exit(1)
else:
    print(f"ERROR: file {args.input} cannot be found")
    sys.exit(1)

if args.filter:
    if os.path.isfile(args.filter):
        filter_file = pd.read_csv(args.filter)

        if args.finalIdcolumn not in filter_file.columns:
            print(f"ERROR: column {args.finalIdcolumn} not in {args.filter}")
            sys.exit(1)
    else:
        print(f"ERROR: file {args.filter} cannot be found")
        sys.exit(1)

if args.inter:
    if not os.path.isdir(args.inter):
        os.mkdir(args.inter)

## Body of the script
# first of all we remove any rwo that doesnt have a primary nor secondary id
genes_withID = data[(data[args.columnMainID] != args.symbolNotID) | 
                    (data[args.columnSecondnID] != args.symbolNotID)]
if args.inter:
    genes_withID.to_csv(os.path.join(args.inter, "only_genes_withSomeID.csv"), index = False)

# Now we are in the situation that they have at least 1 id and human
# We want only 2 cases: mainID and species == 9606 or only secondaryID (because we know that is already human)
mask = (
    ((genes_withID[args.columnMainID] != args.symbolNotID) & (genes_withID[args.columnFilterSpecie].astype(str) == "9606")) |
    ((genes_withID[args.columnMainID] == args.symbolNotID) & (genes_withID[args.columnSecondnID] != args.symbolNotID))
    )
# This mask works because it assumes that the secondary id is only human
selected_genes = genes_withID.loc[mask].copy()
if args.inter:
    selected_genes.to_csv(os.path.join(args.inter, "genesWithMinOneHumanID.csv"), index = False)

# Now we chose which one is the final id column
# Initialise the new id columns
selected_genes[args.finalIdcolumn] = selected_genes[args.columnMainID]
# now we change the cells that are not identify in the main column
selected_genes.loc[selected_genes[args.columnMainID] == args.symbolNotID, args.finalIdcolumn] = selected_genes[args.columnSecondnID]

# Now, if given, we filter the genes that are in the args.filter file
if args.filter:
    filtered_genes = selected_genes[~selected_genes[args.finalIdcolumn].astype(str).isin(filter_file[args.finalIdcolumn].astype(str))]
    # save the filtered file
    filtered_genes.to_csv(os.path.join(args.inter, "genes_withSomeHumanID_filtered.csv"), index = False)

    # Now we remove duplicates by label
    filtered_genes_unique = filtered_genes.drop_duplicates(subset = [args.finalIdcolumn, args.columnLabel])
    # export the final one
    filtered_genes_unique.to_csv(args.output, index = False)

else: # we dont need to filter
    selected_genes.to_csv(args.output, index = False)

    if args.inter:
        selected_genes.to_csv(os.path.join(args.inter, "genes_withSomeHumanID_unified.csv"), index = False)
    
    # export the final one
    selected_genes_filtered = selected_genes.drop_duplicates(subset = [args.finalIdcolumn, args.columnLabel])
    selected_genes_filtered.to_csv(args.output, index = False)