# This is a script that is going to take the labelling data that the curators
# were already agreeding about and the file that was used to label it together
# giving at the end one unique dataframe that has all of the data

# This way the output is the initial given dataset but labelled

import pandas as pd
import argparse
import os
import sys

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-fileCurator", help = "1 of the labelled files of the curators, it will be used to take the data that it was already same between curators", required = True)
parser.add_argument("-fileAgree", help = "file where the agreement was labelled", required = True)
parser.add_argument("-curatorAgree", help = "name of the curator that is the final agreement decision", required = True)
parser.add_argument("-fileOut", help = "name of the file where the agreement dataset is going to be recorded", required = True)
parser.add_argument("-inter", help = "if activated all intermediate dataframes will be stored as well", action = "store_true")
parser.add_argument("-nameFilesInt", help = "if -inter is activated, 2 namefiles need to be provided, the first one for the file with all sentences agreed by curators and the second for the sentences that were revised with the final decision", nargs = 2)
args = parser.parse_args()

# checks
if os.path.exists(args.fileOut):
    answer = input(f"The file '{args.fileOut}' given for -fileOut already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -fileOut file already exists and was not replaced.")

if not os.path.isfile(args.fileCurator):
    print(f"ERROR: file {args.fileCurator} cannot be found")
    sys.exit(1)
else:
    data_curator = pd.read_csv(args.fileCurator)

if not os.path.isfile(args.fileAgree):
    print(f"ERROR: file {args.fileAgree} cannot be found")
    sys.exit(1)
else:
    data_agree = pd.read_csv(args.fileAgree)
    if "Curator" not in data_agree.columns:
        print(f"ERROR: column 'Curator' needs to be in {args.fileAgree}")
        sys.exit(1)

    curators = data_agree["Curator"].unique()

    if args.curatorAgree not in curators:
        print(f"ERROR: curator {args.curatorAgree} not found in {args.fileAgree}")
        sys.exit(1)

if args.inter and args.nameFilesInt == None:
    print("If argument 'inter' is provided argument 'nameFilesInt' need to be provided as well")
    sys.exit(1)


## Body of the script
# Filter the agreement dataset to get only the final one
final_decision = data_agree[data_agree["Curator"] == args.curatorAgree]

# Now we are going to remove the ones that are in the agreement from the ones in the 1 curator file
# We only want the data_curator columns
data_agree_first_time = data_curator.merge(final_decision, how = "outer", on = ["pmid", "number", "indexStart", "indexEnd"], suffixes = ["","_y"], indicator = True)
data_agree_first_time = data_agree_first_time[data_agree_first_time["_merge"] == "left_only"][data_curator.columns]

if args.inter:
    data_agree_first_time.to_csv(args.nameFilesInt[0], index = False)
    final_decision[data_curator.columns].to_csv(args.nameFilesInt[1], index = False)

# We have now separate way the decisions for all the samples so we need to concatenate both
final_label_all = pd.concat([data_agree_first_time, final_decision[data_curator.columns]])
# We need to make sure that the final decision only has teh columns of the data curator, because in teh agreement columns are addded

final_label_all.to_csv(args.fileOut, index = False)