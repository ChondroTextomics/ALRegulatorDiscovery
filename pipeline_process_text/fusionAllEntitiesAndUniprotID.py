# In this script we are going to fuse the
# all entities and protein files that have been given
# by GNorm2

# IMPORTANT:
# This script is possible if the blocks in the output are equal
# doesnt matter that the order of the entities but they need to contain
# the same entities localized
# For that, we have done the temporal file comparison with comparisonResultsGNorm2.py and if they are okay
# we can run this script

import os
import sys
import argparse
import pandas as pd
import re

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-allEntitiesInput", help = "path to the file with GNorm2 output given with setup to give unormalized mention as well ", required = True)
parser.add_argument("-uniprotIDInput", help = "path to the file with GNorm2 output given with setup with protein IDs", required = True)
parser.add_argument("-format", help = "format of the pubtator split of text (sentence split or complete abstract)", required = True, choices = ["sentence", "abstract"])
parser.add_argument("-outFolder", help = "path to the output folder where fused results will be stored", required = True)
args = parser.parse_args()

# Checks of arguments
if not os.path.isfile(args.allEntitiesInput):
    sys.exit(f"ERROR: file {args.allEntitiesInput} cannot be found")

if not os.path.isfile(args.uniprotIDInput):
    sys.exit(f"ERROR: file {args.uniprotIDInput} cannot be found")

if not os.path.isdir(args.outFolder):
    os.makedirs(args.outFolder)
    print(f"Folder {args.outFolder} has been created")
else:
    answer = input(f"The folder '{args.outFolder}' given for -outFolder already exists. Overwrite it? [y/N]: ").strip().lower()
    if answer != "y":
        sys.exit("ABORTED: -outFolder folder already exists and was not replaced.")
     
## Functions
def get_blocks_file(file):
    with open(file, "r", encoding="utf-8") as file:
        content = file.read().split("\n\n")
        for block in content:
            yield block

def create_table(text, name_columns: list, add_rest_columns = True, abstract = False):
    """
    The columns are the names of the columns that we are going to give to the table columns. It has to be
    the same length as the number of columsn that are going to be created.

    If we want to just fill the rest of the columns if needed with a Null value, we set add_rest_columns as True

    From this text we are going to return the id of the sentence, the text that the entities correspond
    and a table with the different entities
    """

    # Make sure that name columns is a list and not empty
    if not isinstance(name_columns, list):
        raise Exception("the argument 'name_columns' needs to be a list")
    else:
        if not name_columns:
            raise Exception("the argument 'name_columns' cannot be an empty list")

    # Preprocess of the whole text
    rows_text = text.splitlines()
    text = rows_text[:2]
    entities = rows_text[2:]

    # Treatment of text
    if abstract == False:
        for row in text:
            if "|t|" in row:
                type_row = "t"
            else:
                type_row = "a"
            row = re.split(r'\|t\||\|a\|', row)
            if row[1] != "-":
                id = row[0]
                sentence = row[1]
                type_sentence = type_row
    elif abstract == True:
        type_sentence = None # We have both sentences
        id = re.split(r'\|t\||\|a\|', text[0])[0]
        sentence = text

    # Treatment of the entities
    entities = [row_entity.split("\t") for row_entity in entities]
    
    # Make sure that we can create the table
    if any(len(row_check) != len(name_columns) for row_check in entities):
        if any(len(row_check) > len(name_columns) for row_check in entities) or add_rest_columns == False:
            raise Exception(f"There is an entity line that does not have the same length as the columns provided:\nTEXT\n{text}\nENTITIES\n{entities}\nCOLUMNS\n{name_columns}")
        else: # This means that we need to complete some rows of the entity
            # Ensure all rows are the same length by filling missing values with NaN
            entities = [row + [pd.NA] * (len(name_columns) - len(row)) for row in entities]
            
    table_content = pd.DataFrame(entities, columns = name_columns)

    return id, type_sentence, sentence, table_content

def pubtator_file(id_text, type_text, text_sentence, table_sentence, output_filename, abstract):
    with open(output_filename, "a") as output_file:
        if abstract == True:
            output_file.write(f"{text_sentence[0]}\n{text_sentence[1]}\n")
        elif abstract == False:
            output_file.write(f"{id_text}|{type_text}|{text_sentence}\n")
        else:
            raise Exception("argument abstarct only received 2 types of values: True or False")
        table_sentence.to_csv(output_file, header = True, mode = "a", index = False, sep= "\t")
        output_file.write("\n")
    return "Pubtator file updated"

def csv_file(id, text, addition_table, original_df, abstract = False):
    """
    Add the information of the additional_table to the original dataframe already formatted

    Return the new dataframe
    """

    addition_table_csv = addition_table.fillna("-")
    if abstract == False:
        row_sentence = [id.split("_")[0],
                        id.split("_")[1],
                        text,
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["text"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["start"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["end"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["ID"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["UniProt_ID"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["SA"].values.tolist())
                        ]
    elif abstract == True:
        row_sentence = [id,
                        text,
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["text"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["start"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["end"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["ID"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["UniProt_ID"].values.tolist()),
                        str(addition_table_csv[addition_table_csv["type"]=="Gene"]["SA"].values.tolist())
                        ]
    else:
        raise Exception("This function only accepts the arguments True or False for abstract")

    original_df.loc[len(original_df)] = row_sentence

    return original_df

## Body of the script

if args.format == "abstract":
    abstract_store = True
else:
    abstract_store = False

# Initiaze the dataframe that is going to be finally the csv file
if args.format == "sentence":
    final_df_csv = pd.DataFrame(columns=["pmid",
                                        "number",
                                        "text",
                                        "gene",
                                        "start",
                                        "end",
                                        "id",
                                        "uniprotid",
                                        "sa"]) # Initial table
else: # abstract
    final_df_csv = pd.DataFrame(columns=["pmid",
                                        "text",
                                        "gene",
                                        "start",
                                        "end",
                                        "id",
                                        "uniprotid",
                                        "sa"]) # Initial table
    

# Treat the files
generators_block = [get_blocks_file(file) for file in [args.allEntitiesInput, args.uniprotIDInput]]

for text_all, text_normalized in zip(*generators_block): # Go through all the sentences chunks of the files
    if text_all == "" or text_normalized == "": # Empty block, probably the final block
        continue

    # Create the fused tables that we are going to use to create all the other files
    id_normalized_text, type_sentence_normalized, text_normalized, table_normalized_entities = create_table(text_normalized.rstrip(),
                                                                                                            name_columns = ["id", "start", "end", "text", "type", "normalized_id"],
                                                                                                            abstract = abstract_store)
    id_all_text, type_sentence_all, text_all, table_all_entities = create_table(text_all.rstrip(),
                                                                                name_columns = ["id", "start", "end", "text", "type", "sa-id"],
                                                                                abstract = abstract_store)

    # Check that we are going to analyze the same sentence of each file
    if id_all_text != id_normalized_text or type_sentence_all != type_sentence_normalized or text_all != text_normalized:
        raise Exception(f"There is something wrong with the sentences with ids normalized({id_normalized_text}) and all entities({id_all_text})")

    # Treat the ID column of the tables to extract the NCBI ID, the species associated, the Uniprot ID 
    # Treat the normalized table
    table_normalized_entities['ID'] = table_normalized_entities['normalized_id'].str.extract(r'(\d+)\(UniProt:')  # Extract ID if pattern exists
    table_normalized_entities['UniProt_ID'] = table_normalized_entities['normalized_id'].str.extract(r'UniProt:([A-Z0-9]+)')  # Extract UniProt ID
    table_normalized_entities['ID'] = table_normalized_entities['ID'].fillna(table_normalized_entities['normalized_id'])# In case they didnt had the strcture of uniprot
        
    # Treat the all entities table
    table_all_entities['SA'] = table_all_entities['sa-id'].str.extract(r'Focus:(\d+)\|*')  # Extract the SA if it exist
    table_all_entities['ID'] = table_all_entities['sa-id'].str.extract(r'Focus:\d+\|(\d+)-?')  # Extract the NCBI ID if it exist
    table_all_entities['ID'] = table_all_entities['ID'].fillna(table_all_entities['sa-id'].str.extract(r'^(?!Focus:)(\d+)').iloc[:, 0]) # We fill the ones that just have the ID, which will be not genes

    # We have now to fuse everything
    # This is why the order of the entities doesnt matter, just that there are the same ones
    fused_table = table_all_entities.merge(table_normalized_entities,
                                            how="outer", # we want to get the ones in all entities that are not in the normalized as well
                                            left_on=["id", "start", "end", "text", "type", "ID"],
                                            right_on=["id", "start", "end", "text", "type", "ID"]) # columns that need to be the same
        

    # Update the PUBTATOR file
    pubtator_file(id_normalized_text,
                  type_sentence_normalized,
                  text_normalized,
                  fused_table,
                  os.path.join(args.outFolder, "output-both-analyses-test.pubtator"),
                  abstract = abstract_store)
        
    # If we have abstracts we need to process a little bit the text
    if abstract_store:
        text_csv = ""
        for row in text_all:
            text_csv += re.split(r'\|t\||\|a\|', row)[1]
    else:
        text_csv = text_all

    # Update the csv file
    final_df_csv = csv_file(id_all_text, text_csv, fused_table, final_df_csv, abstract = abstract_store)

# Export final CSV file
final_df_csv.to_csv(os.path.join(args.outFolder, "genes-sentences-test.csv"), index = False)

print("All files are formatted and exported! :)")