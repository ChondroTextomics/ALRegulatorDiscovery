# script to do bootsrapping over the results
# Sometimes it is not possible to produce the results that many times
# because some of teh models are highly time consuming

## Packages
import pandas as pd
import numpy as np
import argparse
import sys
import os
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-data", help = "path to the trainig dataset", required = True)
parser.add_argument("-out", help = "file name root where to save the different bootstrap sets, example 'output_bootstrap_model'. Extension and iteration will be added. This argument will only be read if outFolder is given as well")
parser.add_argument("-filePerformance", help = "file that will contain the performance of each one of the bootrsapping data", required = True)
parser.add_argument("-summaryFile", help = "file containing summary of the variance of each performance metric", required = True)
parser.add_argument("-outFolder", help = "directory where all of the different bootstrap datasets files will be stored. This argument should be given only if datasets want to be stored. If this argument is given, also argument out should be provided")
parser.add_argument("-iterations", help = "number of iterations of resampling for the bootraping", type = int, required = True)
parser.add_argument("-cluster", help = "if provided it will do cluster bootsraping with the given columns", nargs = "+")
parser.add_argument("-column_label", help = "column name that contains the true labels", required = True)
parser.add_argument("-column_predicted_label", help = "column name that contains the predicted labels", required = True)
parser.add_argument("-column_prob_positive", help = "column name that contains the probability of the positive class", required = True)
parser.add_argument("-positive_class", help = "the label of the positive class", required = True)

args = parser.parse_args()

# Check all of the files are correct
if not os.path.isfile(args.data):
    print(f"ERROR: file {args.data} cannot be found")
    sys.exit(1)
else:
    data = pd.read_csv(args.data)

    if any(column not in data.columns for column in [args.column_label, args.column_predicted_label, args.column_prob_positive]):
        print(f'ERROR: columns "text", "{args.column_label}", "{args.column_predicted_label}", "{args.column_prob_positive}" need to be in file {args.data}')
        sys.exit(1)

    if str(args.positive_class) not in data[args.column_label].astype(str).unique():
        print(f'ERROR: the positive class "{args.positive_class}" is not in the column "{args.column_label}" of the file {args.data}')
        sys.exit(1)

if args.iterations <= 0:
    print("ERROR: the argument iterations needs to be greater than 0")
    sys.exit(1)

if args.cluster != None:
    if any(column not in data.columns for column in args.cluster):
        print(f"ERROR: one or more columns provided in the argument cluster, {args.cluster} are not in the file {args.data}")
        sys.exit(1)
    
    # Get the unique combinations for the clustering
    unique_sentences = data[args.cluster].drop_duplicates()

if args.outFolder != None:
    if args.out == None:
        print(f"ERROR: if outFolder is given, out must be given as well")
        sys.exit(1)
    if not os.path.isdir(args.outFolder):
        os.makedirs(args.outFolder, exist_ok = True )
        print(f"Directory {args.outFolder} has been created succesfully")


## ---------------------------------------
## Functions

def calculate_performances(data, column_label = "label", column_predicted_label = "predicted_label", column_prob_positive = "prob_yes", positive_class = "Yes"):

    label_dtype = data[column_label].dtype
    if pd.api.types.is_numeric_dtype(label_dtype):
        positive_class = int(positive_class)
    else:
        positive_class = str(positive_class)
    # Compute AUC-ROC using probability of the positive class
    auc_value = roc_auc_score((data[column_label] == positive_class).astype(int), data[column_prob_positive])
    # this is neccessary by how auc roc computes the value, it needs to be 0 and 1 instead of Yes/No or any other label so we first check if it is equal to the
    # positive label giving true and false positives and then we convert it to 1 and 0 so it can be used in the auc roc function
    # this will work for any label as long as the positive class is provided in the argument positive_class, it doesnt matter if it is categorical or not

    # Precision, recall, F1
    precision = precision_score(data[column_label], data[column_predicted_label], pos_label = positive_class)
    recall = recall_score(data[column_label], data[column_predicted_label], pos_label = positive_class)
    f1 = f1_score(data[column_label], data[column_predicted_label], pos_label = positive_class)

    return {
        "auc_roc": auc_value,
        "f1": f1,
        "precision": precision,
        "recall": recall
    }

def bootstrap_ci(x, alpha=0.05):
    lower, upper = np.percentile(x, [100*alpha/2, 100*(1-alpha/2)])
    # we divide alpha by 2 because we are gettingthe 2 tails, so if we leave 5% in total, we leave 2.5% in each tail, so we need to divide by 2
    return pd.Series({"ci_lower": lower, "ci_upper": upper})
    # we return the series so we can create a dataframe with the results of the confidence intervals for each metric

## Body of the script
# create a dataframe where teh results of the performance of each one of the bootstrapped datasets will be stored
performance_results_list = []
performance_results = pd.DataFrame(columns = ["bootstrap_file", "iteration", "auc_roc", "f1", "precision", "recall"])

# go through the data and create the bootstrapped datasets
for iter in range(args.iterations):
    print(f"Working in iteration {iter}")
    # Get the data that is going to be teh "bootstrapping" dataset
    if args.cluster == None:
        sample_data = data.sample(frac = 1, replace = True, random_state = iter)
    else:
        unit_selected = unique_sentences.sample(frac = 1, replace = True, random_state = iter)
        sample_data = data.merge(unit_selected, on = args.cluster, how = "right")

    # calculate the performance of the bootstrapped dataset
    performances = calculate_performances(sample_data, column_label = args.column_label, column_predicted_label = args.column_predicted_label, column_prob_positive = args.column_prob_positive, positive_class = args.positive_class)

    if args.outFolder != None:
        sample_data.to_csv(os.path.join(args.outFolder, f"{args.out}_{iter}.csv"), index = False)

    # Append the performance results
    if args.outFolder != None:
        performance_results_list.append({"bootstrap_file": os.path.join(args.outFolder, f"{args.out}_{iter}.csv"), "iteration": iter, **performances})
    else:
        performance_results_list.append({"iteration": iter, **performances})

# create the performance file
performance_results = pd.DataFrame(performance_results_list)
performance_results.to_csv(args.filePerformance, index = False)

# lets get the confidence interval of teh performance metrics
ci_results = performance_results[["auc_roc", "f1", "precision", "recall"]].apply(bootstrap_ci, alpha = 0.05).reset_index()
# we will obtain for each metric a dictionary with the lower and upper confidence interval, so we will have a row for upper and a row for lower
# we reset the idnex so it is the same index as the one we will have in the summary results, so we can concatenate them later

# finally, lets create the summary of the performance results
summary_results = performance_results[["auc_roc", "f1", "precision", "recall"]].agg(["mean", "std", "min", "max"], axis = 0).reset_index()
# the agg is axis = 0 because we collapse the rows to obtain a value per column (it confused me at first because usually axis = 1 means doing it per column)
# lets add the confidence interval to the summary results
summary_results = pd.concat([summary_results, ci_results], axis = 0, ignore_index = True)

summary_results.to_csv(args.summaryFile, index = False)