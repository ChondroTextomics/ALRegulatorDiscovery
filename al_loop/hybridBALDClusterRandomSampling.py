# Script to get different types of sampling
# from a dataframe with cluster and also BALD scores

## packages
import argparse
import sys
import os
import pandas as pd

## arguments
parser = argparse.ArgumentParser()
parser.add_argument("-input", help = "path to the file with the bald and cluster info", required = True)
parser.add_argument("-distance", help = "folder where the distance between samples are, they need to be called 'sample_X.csv' being X the index of the sentence", required = True)
parser.add_argument("-sampling", help = "number of samples to take", required = True, type = int)
parser.add_argument("-out", help = "name of the file to save the selected sentences", required = True)
parser.add_argument("-seed", help = "random seed", type = int, required = True)
args = parser.parse_args()

# checks
# Check if input and distance exist
if not os.path.isfile(args.input):
    print(f"ERROR: file {args.input} cannot be found")
    sys.exit(1)
else:
    output_pool = pd.read_csv(args.input)

    if any(column not in output_pool.columns for column in ["pmid", "number", "BALD", "outlier", "medoid", "weights"]):
        print(f'ERROR: columns "pmid", "number", "BALD", "weights", "medoid" and "outlier" need to be in file {args.input}')
        sys.exit(1)
    
    # These ones are added and we are going to change their values
    output_pool["selected"] = False
    output_pool["reason"] = pd.NA

    # First of all lets check that there are enough sentences to get
    if output_pool.groupby(["pmid", "number"]).ngroups < args.sampling:
        print(f"Error: Not enough sentences to do a sampling batch from file {args.input}")
        sys.exit(1)

if not os.path.isdir(args.distance):
    print(f"ERROR: folder {args.distance} cannot be found")
    sys.exit(1)

# Check that theouput file doesnt exist
if os.path.isfile(args.out):
    print(f"File {args.out} already exists, remove before running this program")
    sys.exit(1)

# Check that sampling is at least 2*number_clusters
if args.sampling < 2*len(output_pool["cluster"].unique()):
    print("ERROR: We are going to take 2 samples for diversity per each cluster and sampling argument lower than 2*number_clusters")
    sys.exit(1)

## Functions
def find_nearest(name_file_distances, indexes_compare):
    """Function that find the nearest sample to the row contained in name_file_distances from the
    samples that are in indexes_compare
    
    This way we only comparing the same cluster samples
    """

    # Get the file with the distance
    if not os.path.isfile(name_file_distances):
        print(f"ERROR: file {name_file_distances} doesnt exist so nearest point could be found")
        sys.exit(1)
    else:
        distances_compare = pd.read_csv(name_file_distances, index_col = 0)

    # Lets make sure that the indexes_compare are str because they are going to be the columns
    indexes_compare = [str(ind) for ind in indexes_compare]
    missing = [col for col in indexes_compare if col not in distances_compare.columns]
    if any(col not in distances_compare.columns for col in indexes_compare):
        print(f"ERROR: one of the samples to compare are not in the file {name_file_distances}")
        print(missing)
        sys.exit(1)

    # We only want to compare it to the ones in index_compare so we take only those
    distances_compare = distances_compare[indexes_compare]

    # Now we take the min value of those distances
    return int(distances_compare.idxmin(axis = 1).iat[0])

def cluster_uncertain_treatment(cluster_dataframe):
    """
    Create the selection uncertain dataframe for that cluster
    which will be formed by the most uncertain score of each
    pmid+number
    """

    # Initialize list of selected rows
    selected = []

    for _, group_sentence in cluster_dataframe.groupby(by = ["pmid", "number"]):
        selected.append(group_sentence["BALD_weighted"].idxmax())

    return cluster_dataframe.loc[selected]

def clean_cluster_from_selected(cluster_dataframe, selected_dataframe):

    # Do a left merge with the sentence indicators
    merged_dataframe = cluster_dataframe.merge(selected_dataframe,
                                               on = ["pmid", "number"],
                                               how = "left",
                                               indicator = True,
                                               suffixes = ["", "_y"])
    
    # Restore the original index because it resets it when doing the merging

    merged_dataframe.index = cluster_dataframe.index

    # Get only rows that are in the left one, in the cluster one
    filtered_cluster = merged_dataframe[merged_dataframe["_merge"] == "left_only"]

    # Return the "cleaned" cluster dataframe
    return filtered_cluster[cluster_dataframe.columns]

def select_sentences_randomly(cluster_dataframe_groupped, number_selection, random_seed):

    if number_selection == 0:
        return []

    # Get all unique group keys
    all_groups = list(cluster_dataframe_groupped.groups.keys())

    # Handle the case where number_selection > available groups
    number_selection = min(number_selection, len(all_groups))

    # Randomly choose which groups to sample from
    selected_groups = pd.Series(all_groups).sample(n = number_selection,
                                                   random_state = random_seed)

    selected_index = []

    # For each selected group, sample one sentence (row)
    for g in selected_groups:
        group_df = cluster_dataframe_groupped.get_group(g)
        chosen_idx = group_df.sample(n = 1, random_state = random_seed).index[0]
        selected_index.append(chosen_idx)

    return selected_index

## ---------------------------------------------------------
## Establish some sampling variables

# Lets calculate how many samples do we need per cluster
min_samples = int(args.sampling/len(output_pool["cluster"].unique()))
random_samples = int(0.1*min_samples)
uncertain_samples = int(min_samples - 2 - random_samples)

## ---------------------------------------------------------
## Produce the weighted BALD for uncertainty sampling
output_pool["BALD_weighted"] = output_pool["BALD"]*output_pool["weights"]

## ---------------------------------------------------------
## Diversity Sampling

# Start with the cluster loop
for cluster_label in sorted(output_pool["cluster"].unique()):
    # Separate the diveristy samples from the other because we will be treating them differently
    cluster_diver = output_pool[(output_pool["cluster"] == cluster_label) & ((output_pool["medoid"] == True) | (output_pool["outlier"] == True))]
    cluster_no_diver = output_pool[(output_pool["cluster"] == cluster_label) & ((output_pool["medoid"] == False)) & ((output_pool["outlier"] == False))]

    # Lets check if the diversity ones are in the selected samples
    if cluster_diver.set_index(['pmid', 'number']).index.isin(output_pool[output_pool["selected"] == True].set_index(['pmid', 'number']).index).any():
        # This means that there is at least 1 of the diversity samples that is in the already selected batch
        # Lets analyze them individually
        med_repl = False
        out_repl = False

        # Lets analyze the medoid
        med_row = cluster_diver[cluster_diver["medoid"] == True].iloc[0]
        pmid_med = med_row["pmid"]
        number_med = med_row["number"]

        if not ((output_pool[output_pool["selected"] == True]["pmid"] == pmid_med) & (output_pool[output_pool["selected"] == True]["number"] == number_med)).any():
            output_pool.loc[cluster_diver[cluster_diver["medoid"] == True].index, "selected"] = True
            output_pool.loc[cluster_diver[cluster_diver["medoid"] == True].index, "reason"] = "diversity"
        else:
            med_repl = True

        # Lets analyze the outlier (it will also analyze if it is the same as the medioid because it is already in the selected ones)
        if not cluster_diver[cluster_diver["outlier"] == True].empty:
            out_row = cluster_diver[cluster_diver["outlier"] == True].iloc[0]
            pmid_out = out_row["pmid"]
            number_out = out_row["number"]

            if not ((output_pool[output_pool["selected"] == True]["pmid"] == pmid_out) & (output_pool[output_pool["selected"] == True]["number"] == number_out)).any():
                output_pool.loc[cluster_diver[cluster_diver["outlier"] == True].index, "selected"] = True
                output_pool.loc[cluster_diver[cluster_diver["outlier"] == True].index, "reason"] = "diversity"
            else:
                out_repl = True
        
        # Now we are going to do the cleaning of the cluster_no_diver from the pmid+number that are already selected
        cluster_no_diver_clean = clean_cluster_from_selected(cluster_no_diver, output_pool[output_pool["selected"] == True])

        if len(cluster_no_diver_clean) == 0:
            # We cant select a subs so lets go to the next cluster
            continue

        # Now that we know that at least we have 1 option available we can try to substitute at least 1
        # First subs the medioid if neccessary
        if med_repl:
            index_selected_med = find_nearest(os.path.join(args.distance,
                                                           f"sample_{cluster_diver[cluster_diver['medoid'] == True].index.values[0]}.csv"),
                                              cluster_no_diver_clean.index)
            output_pool.loc[index_selected_med, "selected"] = True
            output_pool.loc[index_selected_med, "reason"] = "diversity"
        
        if out_repl: # It will only go if it is true and if it is true there is one in the cluster_div
            # We need to remove the one that has been selected, if that has happened previously
            cluster_no_diver_clean = clean_cluster_from_selected(cluster_no_diver_clean, output_pool[output_pool["selected"] == True])

            if len(cluster_no_diver_clean) == 0:
                # We cant select a subs so lets go to the next cluster
                continue
            
            index_selected_out = find_nearest(os.path.join(args.distance,
                                                           f"sample_{cluster_diver[cluster_diver['outlier'] == True].index.values[0]}.csv"),
                                              cluster_no_diver_clean.index)
            output_pool.loc[index_selected_out, "selected"] = True
            output_pool.loc[index_selected_out, "reason"] = "diversity"

    else:
        # This means that neither the outlier nor medoid are selected
        # Now we need to see if the medoid and outlier are the same sentence

        if len(cluster_diver) > 1 and (cluster_diver[['pmid', 'number']].nunique() == 1).all():
            # If it enters here it means that the outlier and the medoid are the same sentence  so we need
            # to find a substitute to the outlier
            
            # First we include the medoid as selected
            output_pool.loc[cluster_diver[cluster_diver["medoid"] == True].index, "selected"] = True
            output_pool.loc[cluster_diver[cluster_diver["medoid"] == True].index, "reason"] = "diversity"

            # Now we need to remove the rows that have already been selected from the non-diversity df
            # this will include the pmid+number of the medoid so we will not be selecting the same sentence as both the medoid and outlier
            # in this case
            cluster_no_diver_clean = clean_cluster_from_selected(output_pool[(output_pool["cluster"] == cluster_label) & (output_pool["selected"] == False)], output_pool[output_pool["selected"] == True])

            # Now we have it completly clean meaning that the point that we will select will not be in the already selected
            # sentences neither the medoid
            
            # First lets see if we can select anything
            if len(cluster_no_diver_clean) > 0:
                # Lets find the nearest point to the outlier and select that one
                index_selected_outlier = find_nearest(os.path.join(args.distance,
                                                                   f"sample_{cluster_diver[cluster_diver['outlier'] == True].index.values[0]}.csv"),
                                                      cluster_no_diver_clean.index)
                output_pool.loc[index_selected_outlier, "selected"] = True
                output_pool.loc[index_selected_outlier, "reason"] = "diversity"
            # If len(cluster_no_diver_clean) <= 0, we cant select anything else from this cluster and we go to the next one
            # which will happen because it is the end of the if else

        else:
            # We can add both of them so we just get the indexes of the cluster_diver
            output_pool.loc[cluster_diver.index, "selected"] = True
            output_pool.loc[cluster_diver.index, "reason"] = "diversity"

## ---------------------------------------------------------
## Uncertainty sampling
# Start with the cluster loop
if uncertain_samples > 0:
    for cluster_label in sorted(output_pool["cluster"].unique()):
        # Pre-process the cluster so we can have a clean one
        # We remove the rows that have a combination pmid + number already selected
        clean_cluster_df = clean_cluster_from_selected(output_pool[(output_pool["cluster"] == cluster_label) & (output_pool["selected"] == False)], output_pool[output_pool["selected"] == True])

        # Retrieve the most uncertain scores from each sentence (pmid+number)
        sentence_cluster_ranked = cluster_uncertain_treatment(clean_cluster_df)
        # This returns us a dataframe with the biggest uncertain sample of each sentence

        # Select the uncertain samples
        # Get the biggest uncertain ones
        if len(sentence_cluster_ranked) >= uncertain_samples:
            biggest_uncertain = sentence_cluster_ranked.nlargest(uncertain_samples, "BALD_weighted").index
            output_pool.loc[biggest_uncertain, "selected"] = True
            output_pool.loc[biggest_uncertain, "reason"] = "uncertainty"
        else: # We take them all, no random samples from this cluster
            output_pool.loc[sentence_cluster_ranked.index, "selected"] = True
            output_pool.loc[sentence_cluster_ranked.index, "reason"] = "uncertainty"

## ---------------------------------------------------------
## Random sampling
if random_samples > 0:
    for cluster_label in sorted(output_pool["cluster"].unique()):
        # Pre-process the cluster so we can have a clean one
        # We remove the rows that have a combination pmid + number already selected
        clean_cluster_df = clean_cluster_from_selected(output_pool[(output_pool["cluster"] == cluster_label) & (output_pool["selected"] == False)], output_pool[output_pool["selected"] == True])

        grouped_sentences = clean_cluster_df.groupby(["pmid", "number"])

        if len(grouped_sentences) >= random_samples:
            number_selected_sentences = random_samples
        elif len(grouped_sentences) > 0:
            number_selected_sentences = len(grouped_sentences)
        else:
            number_selected_sentences = 0
        indeces_random_selection = select_sentences_randomly(grouped_sentences, number_selected_sentences, args.seed)
        output_pool.loc[indeces_random_selection, "selected"] = True
        output_pool.loc[indeces_random_selection, "reason"] = "random"

## --------------------------------------------------------
## Remaining samples needed
# Figure it out how many more sentences we need to get
remaining_samples = args.sampling - len(output_pool[output_pool["selected"] == True])

if remaining_samples > 0:
    """
        There is at least 1 cluster that did not have enough samples to get the min_samples
        per cluster

        For those, lets get half of them with the max uncertain and half of them randomly

        If there is only 1 sample, it will be taken from the random. If they are uneven samples
        left then it would be one more random than ucnertain by how it is coded right now.
    """
    remaining_uncertain = int(remaining_samples // 2)
    remaining_random = int(remaining_samples - remaining_uncertain)

    # Remove from the pool df all the sentences that have been selected (by any method)
    clean_cluster_after_selection = clean_cluster_from_selected(output_pool[output_pool["selected"] == False],
                                                                output_pool[output_pool["selected"] == True])

    if remaining_uncertain > 0:
        # Get the most uncertain ones out of all of them
        cluster_bald_treated = cluster_uncertain_treatment(clean_cluster_after_selection)

        biggest_uncertain_remained = list(cluster_bald_treated.nlargest(remaining_uncertain, "BALD_weighted").index)
        output_pool.loc[biggest_uncertain_remained, "selected"] = True
        output_pool.loc[biggest_uncertain_remained, "reason"] = "uncertainty_remaining"
    
    if remaining_random > 0:
        # Remove from the pool df all the sentences that have been selected (by any method)
        clean_cluster_after_selection_div = clean_cluster_from_selected(output_pool[output_pool["selected"] == False],
                                                                        output_pool[output_pool["selected"] == True])
        
        grouped_sentences_remain = clean_cluster_after_selection_div.groupby(["pmid", "number"])
        indeces_random_selection_rem = select_sentences_randomly(grouped_sentences_remain,
                                                                 remaining_random,
                                                                 args.seed)
        output_pool.loc[indeces_random_selection_rem, "selected"] = True
        output_pool.loc[indeces_random_selection_rem, "reason"] = "random_remaining"

## --------------------------------------------------------
## Save output
output_pool.to_csv(args.out, index = False)
