# This is an check of the results of GNorm2 just to make sure they are the same because
# it has been run twice (and they need to have the same identified genes for the fuse of format to work)
# In this script the termporal fiels are being compared

import os
import sys
import argparse

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-folders", help = "the folders (the whole result folder) that come from a GNorm2 process that are going to be compared", required = True, nargs="+")
parser.add_argument("-fileNameCompare", help = "the name of the file to compare (e.g., 'sentences.pubtator'), it must have the same name in all of the folders (just the name, no path)", required = True)
parser.add_argument("-outputFolder", help = "path to the folder where all of the output comparison files will be saved", required = True)
args = parser.parse_args()

# check that the output folder does not exist, if it does we will not continue to avoid overwriting files
if os.path.isdir(args.outputFolder):
    answer = input(f"The file '{args.outputFolder}' given for -outputFolder already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -outputFolder file already exists and was not replaced.")

# Checks of at least the structure of the folders
for folder in args.folders:
    lacking_folders = []
    if not os.path.isdir(folder):
        sys.exit(f"ERROR: {folder} is not a folder or cannot be found")
    else:
        # check that we have the other folders to check
        # then we will check if the fileNameCompare is in all of the folders
        if not os.path.exists(os.path.join(folder, "tmp_SA")):
            lacking_folders.append("tmp_SA")
        if not os.path.exists(os.path.join(folder, "tmp_SR")):
            lacking_folders.append("tmp_SR")
        if not os.path.exists(os.path.join(folder, "tmp_GNR")):
            lacking_folders.append("tmp_GNR")
        
    if lacking_folders: # This means that there is at least 1 folder that is not inside
        sys.exit(f"ERROR: inside the folders to compare we need to have all of the temporal folder created by GNorm2 (tmp_SA, tmp_GNR and tmp_SR). The following ones are missing from directory {folder}: {lacking_folders}")
    
    # Check that the file is in all the folders
    # now that we know all of them exist
    for subfolder in ["tmp_SA", "tmp_SR", "tmp_GNR"]:
        if not os.path.isfile(os.path.join(folder, subfolder, args.fileNameCompare)):
            sys.exit(f"ERROR: file {os.path.isfile(os.path.join(args.folder, subfolder, args.fileNameCompare))} cannot be found")


## Functions
def get_blocks_file(file):
    with open(file, "r", encoding="utf-8") as file:
        content = file.read().split("\n\n")
        for block in content:
            yield block

def compare_blocks(list_files:list):
    generators_block = [get_blocks_file(file) for file in list_files]
    number_of_different_blocks = 0
    different_blocks = []
    number_of_same_blocks = 0
    for blocks in zip(*generators_block):
        if all(part == blocks[0] for part in blocks):
            number_of_same_blocks += 1
        else: # some blocks are different
            number_of_different_blocks += 1
            different_blocks.append(blocks)
    return number_of_same_blocks, number_of_different_blocks, different_blocks

def format_differences(number_same, number_diff, different, folder_analyse, out_file):
    with open(out_file, "w") as error_file:
        error_file.write(f"""-----------------------------------------
Analysis of {folder_analyse} folders from GNorm2
-----------------------------------------

Number of same blocks: {number_same}
Number of different blocks: {number_diff}

-----------------------------------------""")
        if different: # This means that it is not empty
            error_file.write("\n\nDIFFERENT BLOCKS\n")
            
            for i, different_block in enumerate(different):
                error_file.write(f"\n{i+1}\n")
                for element in different_block:
                    error_file.write(f"{element}\n\n")
                error_file.write("\n")
    return

## Body of the script
# If the directory doesnt exist we will create it
if not os.path.exists(args.outputFolder):
    os.mkdir(args.outputFolder)

# Now that we have checked that the files exist in the respective folders, lets check that they are the same temporal ones
for subfolder in ["tmp_SA", "tmp_SR", "tmp_GNR"]:
    number_same_blocks_folder, number_different_blocks_folder, different_blocks_folder = compare_blocks([os.path.join(folder, subfolder, args.fileNameCompare) for folder in args.folders])
    format_differences(number_same_blocks_folder,
                       number_different_blocks_folder,
                       different_blocks_folder,
                       subfolder,
                       os.path.join(args.outputFolder, f"analysis_{subfolder}.txt"))