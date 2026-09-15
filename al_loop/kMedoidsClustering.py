# Clustering of the sentences given a cls embedding file
# This step can take a lot of time if the cosine distance is big
# hence why it is separated from the other, so it can run in a pararlel way while
# other processes also happen

import argparse
import os
import sys
import pandas as pd
import kmedoids
import numpy as np
from sklearn.metrics.pairwise import cosine_distances
import psutil
import math

## Arguments
parser = argparse.ArgumentParser()
parser.add_argument("-pool", help = "pool file in which columns with cluster label, medoid and outlier will be added", required = True)
parser.add_argument("-cosineDistances", help = "file containing the cosine distances between the samples", required = True)
parser.add_argument("-out", help = "file name to store the final results", required = True)
parser.add_argument("-seed", help = "random seed", type = int)
parser.add_argument("-k", required = True, type = int, help = "number of cluster to divide the samples")
args = parser.parse_args()

# Checks
if os.path.isfile(args.pool):
    pool = pd.read_csv(args.pool)

    if any(column not in pool.columns for column in ["text", "pmid", "number"]):
        print(f'ERROR: columns "text", "number", "pmid" need to be in file {args.pool}')
        sys.exit(1)

    output_pool = pool.copy(deep = True)
else:
    print(f"ERROR: file {args.pool} cannot be found")
    sys.exit(1)

if os.path.isfile(args.cosineDistances):
    cls = pd.read_csv(args.cosineDistances)
    #cls = cls.astype(np.float32)
else:
    print(f"ERROR: file {args.cosineDistances} cannot be found")
    sys.exit(1)

## Functions
def print_memory_usage(tag=""):
    process = psutil.Process(os.getpid())
    mem_gb = process.memory_info().rss / 1e9
    print(f"[{tag}] Memory usage: {mem_gb:.2f} GB")

def kmedioids_clustering_cosine(embeddings, number_clusters, seed):
  # Get the clustering model
  # cosine is cosine distance according to this part of the github doc
  # https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/metrics/pairwise.py#L1922
  # also #L1907 states it
  # This is the dictionary that says that cosine is the distance, not the similarity
  kmed = kmedoids.KMedoids(n_clusters = number_clusters,
                           metric = 'precomputed',
                           random_state = seed)
  # https://python-kmedoids.readthedocs.io/en/latest/#kmedoids.KMedoids.fit_transform
  kmed.fit(embeddings)
  
  # Get labels of teh clusters
  labels = kmed.labels_

  # Get the indexes of the medioids
  medioids = kmed.medoid_indices_

  # Get the outliers of each cluster
  # In our case it is the further point of the medioid in each cluster
  # Initialize teh outliers indexes
  outliers = []

  for cluster_id, med in enumerate(medioids):
    # Get the indexes of the points that are in the cluster
    # We are only given one condition so we take just the first element
    cluster_points = np.where(labels == cluster_id)[0]
    # we remove the medoid
    cluster_points = cluster_points[cluster_points != med]
    # We get the indexes of those points

    # Lets get the vector of the distances that corresponds to the medioid
    # this vector contains all the distances to all of the other points
    medioid_distances = cosine_distances(embeddings[med].reshape(1, -1), # We need to reshape it because cosine distance expect a 2d array
                                         embeddings[cluster_points])
    
    # Now lets get the index of the outlier of that cluster
    # We get the index of the max value of the distances between the med and their cluster points
    # we select the index of the whole ammount of points
    outlier_index_cluster = cluster_points[np.argmax(medioid_distances[0])]

    # Append the outlier of that cluster
    outliers.append(int(outlier_index_cluster))
  return (labels, medioids, outliers)

## ---------------------------------------
## Pool Clustering
# We have the cls embeddings so now we will get the clustering
# We want to have at least 10 per cluster, that way we can have 1 outlier, 1 medoid and 1 random besides 7 uncertain
# This is because this way we have at least 10% of randomness selection

# Lets get the embeddings of the sampels from the predictions
# Now we do the clustering with those embeddings
labels, med_clusters, outliers_cluster = kmedioids_clustering_cosine(cls.to_numpy(),
                                                                     args.k,
                                                                     args.seed)

# Lets add now to the pool the cluster information
output_pool["cluster"] = labels

# Initialize the information columns
output_pool["medoid"] = False
output_pool["outlier"] = False

# Add the information
# labels, med_clusters, outliers_cluster, distance_matrix
output_pool.loc[med_clusters, "medoid"] = True
output_pool.loc[outliers_cluster, "outlier"] = True

## ---------------------------------------
## Save the file
output_pool.to_csv(args.out, index = False)