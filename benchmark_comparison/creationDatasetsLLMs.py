# Creating the datasets for the LLMs

import pandas as pd
from pathlib import Path
from datasets import Dataset, DatasetDict
import argparse
import os
import sys

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "csv file that will be transformed into the hd dataset", nargs="*", required = True)
parser.add_argument("-systemPrompt", help = "file with the system prompt", required = True)
parser.add_argument("-userPrompt", help = "file with the user prompt", required = True)
parser.add_argument("-output", help = "path to the output file", required = True)
parser.add_argument("-nameHfDataset", help = "name of the object(s) in the dataset dict", nargs="*", required = True)
args = parser.parse_args()

# Check them
if len(args.input) != len(args.nameHfDataset):
    sys.exit(f"The same number of files as name of hf datasets need to be provided and you have given {len(args.input)} files and {len(args.nameHfDataset)} names for the datasets")

if os.path.isdir(args.output):
    answer = input(f"Folder {args.output} already exists. Do you want to overwrite it? [y/N]: ").strip().lower()
    if answer not in ("y", "yes"):
        sys.exit("Aborting, the existing output was not modified")

data = {}
for file, name_hf in zip(args.input, args.nameHfDataset):
    if os.path.isfile(file):
        data[name_hf] = pd.read_csv(file)
    else:
        sys.exit(f"File {args.input} cannot be found")

if os.path.isfile(args.systemPrompt):
    system_prompt = Path(args.systemPrompt).read_text(encoding="utf-8").strip()
else:
    sys.exit(f"File {args.systemPrompt} cannot be found")

if os.path.isfile(args.userPrompt):
    user_prompt_template = Path(args.userPrompt).read_text(encoding="utf-8").strip()
else:
    sys.exit(f"File {args.userPrompt} cannot be found")


# Build records
dataset_records = {} # This way we are not going to overwrite anything, if we get a lot of data this needs to be optimised

for name_df, dataset in data.items():
    records = []

    for index, row in dataset.iterrows():
        user_prompt_row = user_prompt_template.format(sentence_to_classify = row["text"])
        if row["labels"] == 1:
            assistant_answer = "Yes"
        else:
            assistant_answer = "No"
        
        records.append({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt_row},
                {"role": "assistant", "content": assistant_answer}
            ],
            "metadata":{"pmid":row["pmid"],
                        "number":row["number"]}
        })

    # Create the dataset for huggingface
    dataset_records[name_df] = Dataset.from_list(records)

dataset_dict = DatasetDict(dataset_records)

# Save it
output_path = Path(args.output)
output_path.parent.mkdir(parents = True,
                         exist_ok = True)
dataset_dict.save_to_disk(output_path)
print(f"Dataset saved in '{output_path}'")