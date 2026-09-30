# Replicating the Study Results

This guide walks through reproducing the datasets and results of the study, part by part. Each part builds on the outputs of the previous one.

1. **Data extraction:** from PubMed to the three filtered sentence datasets
2. **Initial labelled data:** selecting and labelling the core set (first training set) and the validation set
3. **Active learning iterations:** training a model, selecting the next batch to label, and labelling it, repeated for each iteration
4. **Production model and application predictions:** training the final PubMedBERT model on the AL training data plus the validation set, and classifying the application dataset
5. **Held-out evaluation:** predicting the held-out set with the production model, and preparing and running the benchmark models (logistic regression and LLMs) on it
6. **Post-processing:** performance metrics, linking the predictions to human gene IDs, GO coverage, over-representation analysis (ORA) and figures

Per-script documentation (arguments, input/output examples) lives in each folder's `README.md`. This guide only covers how the scripts were chained and configured to produce the study's data.

## 1. Data Extraction: Building the Three Sentence Datasets

The study uses three sentence-level datasets, all built with the same pipeline (`pipeline_process_text/`) and the same concept list. They differ only in the PubMed publication-date window:

| Dataset | Used for | Publication date window | Sentences after filtering |
|---|---|---|---|
| **Training–validation / LLM development** | Active learning loop (training and validation) and LLM prompt development | `1000/01/01` – `2025/01/31` | 39,180 |
| **Held-out** | Final evaluation of all models, on literature published after the training data | `2025/06/01` – `2025/12/31` | 835 |
| **Application** | Running the final model to extract candidate regulators | `2006/01/01` – `2026/02/28` | 31,325 |

The gap between the training window and the held-out window (February–May 2025) is intentional. It keeps held-out articles temporally separate from anything the model was trained or validated on.

All three use the same base query, with only the `[dp]` (date of publication) range changed:

```text
((chondrogenesis OR chondrocyte differentiation) AND "English"[Language]) NOT "Review"[Publication Type] AND ("<start>"[dp] : "<end>"[dp])
```

> **Exact replication vs. re-running the queries:** PubMed changes over time as papers get added, corrected or retracted so re-running these queries will likely not return exactly the same results. To reproduce the datasets exactly, use the PMID lists provided on Zenodo (`data/`, see [`data/README.md`](../data/README.md)) with the `-pmidfile` option in step 1.1.

**Requirements**

All software requirements are listed in `envs/environments_pipeline_process_text.txt` (Python packages in `envs/requirements_pipeline_process_text.txt`). Two of them matter especially for this part:

- **NCBI EDirect** (`esearch`/`efetch`) must be installed and on `PATH`. `fetchQueryResults.py` switches from Biopython's Entrez to EDirect when a query returns more than 9,999 articles, which is the case for the training and application datasets. EDirect needs a Unix-like shell, so Windows users need WSL.
- **Singularity** (or Apptainer), to run the GNorm2 container. The image (`gnorm2-ncbi_latest.sif`) is obtained with `singularity pull docker://nadarajan07/gnorm2-ncbi`. Usage of these scripts in a HPC is recommended as GNOrm2 require a high use of RAM.

The following study files are archived on Zenodo (see [`data/README.md`](../data/README.md)):

- The PMID list for each dataset (`pubMedDataExtraction/`), used in step 1.1 for exact replication
- The two GNorm2 setup files, used in step 1.5
- The chondrogenesis concept list (`concepts.txt`, one term per line), used in step 1.7

The commands below use a `DATASET` name (`training`, `heldout`, `application`) to keep the three runs' files apart.

Steps 1.2 to 1.7 are identical for every dataset; only step 1.1 changes.

### 1.1 Retrieve the articles (`fetchQueryResults.py`)

`fetchQueryResults.py` takes the query plus `-mindate`/`-maxdate`. The queries already carry the `[dp]` range, so `-mindate`/`-maxdate` are set to the same dates.

**Training–validation / LLM development**

```bash
python fetchQueryResults.py \
  -out pmids_training.txt \
  -mindate "1000/01/01" \
  -maxdate "2025/01/31" \
  -db pubmed \
  -email you@example.com \
  -query '((chondrogenesis OR chondrocyte differentiation) AND "English"[Language]) NOT "Review"[Publication Type] AND ("1000/01/01"[dp] : "2025/01/31"[dp])' \
  -retrieve articles_training.xml
```

**Held-out**

```bash
python fetchQueryResults.py \
  -out pmids_heldout.txt \
  -mindate "2025/06/01" \
  -maxdate "2025/12/31" \
  -db pubmed \
  -email you@example.com \
  -query '((chondrogenesis OR chondrocyte differentiation) AND "English"[Language]) NOT "Review"[Publication Type] AND ("2025/06/01"[dp] : "2025/12/31"[dp])' \
  -retrieve articles_heldout.xml
```

**Application (Final search for trained model classification)**

```bash
python fetchQueryResults.py \
  -out pmids_application.txt \
  -mindate "2006/01/01" \
  -maxdate "2026/02/28" \
  -db pubmed \
  -email you@example.com \
  -query '((chondrogenesis OR chondrocyte differentiation) AND "English"[Language]) NOT "Review"[Publication Type] AND ("2006/01/01"[dp] : "2026/02/28"[dp])' \
  -retrieve articles_application.xml
```

**For exact replication**, use the archived PMID lists instead of the search (each dataset has its own PMID file):

```bash
python fetchQueryResults.py \
  -out pmids_data.txt \
  -db pubmed \
  -email you@example.com \
  -pmidfile <PMID file from pubMedDataExtraction/> \
  -retrieve articles_search.xml
```

### 1.2 – 1.4 Parse, split into sentences and convert to PubTator

These three steps are run exactly the same way and it is as explained in the `pipeline_process_text/README.md`. They turn the XML file with the article's data into one sentence per row and then into the PubTator format GNorm2 expects as input.

```bash
DATASET=training   # or: heldout, application

python pubmedXMLtoCSV.py -input articles_${DATASET}.xml -out parsed_${DATASET}.csv
python splitterArticleSentences.py -input parsed_${DATASET}.csv -out sentences_${DATASET}.csv
python pubtatorFormatter.py -input sentences_${DATASET}.csv -out sentences_${DATASET}.pubtator -structure sentence
```

### 1.5 Run GNorm2 twice (`gnormSingularityExecution.sh`)

GNorm2 is run **twice on each dataset**, on the same input PubTator file, with two different setup configurations. That makes six GNorm2 runs across the three datasets.

| Run | Purpose | Key setup options |
|---|---|---|
| **All entities** | Capture *every* gene mention GNorm2 recognises, including those it cannot normalise to an identifier so we can have all of the possible genes of the text | `Normalization2Protein = False`, `ShowUnNormalizedMention = True` |
| **UniProt ID** | Normalise recognised genes to a UniProt accession wherever possible so we can have all of th epossible metadtaa about the localised genes | `Normalization2Protein = True` |

Both runs are needed because neither one gives the full picture on its own.

Step 1.6 then merges the two, keeping every mention from the all-entities run and attaching the UniProt ID where the second run found one.

The exact setup files used in the study are on Zenodo, so use those to replicate the study.

`gnormSingularityExecution.sh` takes no arguments. For each run, edit the variables at the top of the bash script, then launch it:

```bash
# Run 1: all entities
results_directory="results_allEntities_${DATASET}"
input_pubtator_file="sentences_${DATASET}.pubtator"
setup_file="setup_allEntities.txt"

# Run 2: UniProt ID
results_directory="results_uniprotID_${DATASET}"
input_pubtator_file="sentences_${DATASET}.pubtator"
setup_file="setup_uniprotID.txt"
```

```bash
bash gnormSingularityExecution.sh > run.log 2> run.err
```

Use a **different `results_directory` for each run**. The script creates its working folders inside it, and GNorm2 writes its output with the same filename as the input, so two runs sharing a directory would overwrite each other. Each run's result ends up at `<results_directory>/output/sentences_${DATASET}.pubtator`.

Optionally (but recommended to prevent errors), `comparisonResultsGNorm2.py` can be used to check that the two runs agree on the recognition stages (`tmp_SR`, `tmp_GNR`, `tmp_SA`), ssince it is required by the fusing step (1.6) to have the same amount of entities localised by the software (no matter the order of them)

### 1.6 Fuse the two GNorm2 runs (`fusionAllEntitiesAndUniprotID.py`)

```bash
python fusionAllEntitiesAndUniprotID.py \
  -allEntitiesInput results_allEntities_${DATASET}/output/sentences_${DATASET}.pubtator \
  -uniprotIDInput results_uniprotID_${DATASET}/output/sentences_${DATASET}.pubtator \
  -format sentence \
  -outFolder fused_${DATASET}
```

This writes `fused_${DATASET}/genes-sentences-test.csv` (one row per sentence, with the gene metadata of both runs) and `fused_${DATASET}/output-both-analyses-test.pubtator`.

| pmid | number | text | gene | start | end | id | uniprotid | sa |
|---|---|---|---|---|---|---|---|---|
|39764517|1|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells stemness.|['SPI1']|['0']|['4']|['6688']|['P17947']|['9606']|

### 1.7 Keep sentences with a gene and a concept term (`filterSentencesGeneConcept.py`)

```bash
python filterSentencesGeneConcept.py \
  -input fused_${DATASET}/genes-sentences-test.csv \
  -concepts concepts.txt \
  -output filtered_sentences_${DATASET}.csv
```

A sentence is kept only if it has at least one gene from GNorm2 **and** at least one term from `concepts.txt`. Matching is case-insensitive and on whole words. Use the `concepts.txt` from Zenodo, and use the same file for all three datasets.

---

## 2. Initial Labelled Data: Core Set and Validation Set

Before the active learning loop can start, the model needs a first labelled training set (the **core set**) and a fixed **validation set** to evaluate each iteration against. Both are taken from the training–validation pool (`filtered_sentences_training.csv`, the 39,180 sentences from Part 1):

| Set | Size | How it is selected | Purpose |
|---|---|---|---|
| **Core set** | 150 sentences | Diversity-based selection over sentence embeddings | Training data for the first (core) model |
| **Validation set** | 500 sentences | Random sample from the pool left after removing the core set | Evaluating the model at every AL iteration |

Both sets were labelled by the same 2 curators, and both are removed from the pool so that the AL loop never selects them again.

The sizes are in **sentences** (rows of `filtered_sentences_training.csv`). A sentence can contain several genes, so the number of labelled gene instances in each set is larger than the number of sentences. As well, some sentences did not have anmy real genes (as in the labelling processes entiteis localised as genes by GNorm2 that were mistakes were reported and removed so the final number of sentences is not the same as the selected ones)

**Files on Zenodo** (see [`data/README.md`](../data/README.md)):

- The labelling guidelines used by the curators. The rules applied to these two sets are also in [`labelling/AnnotationrulesPerDataset.md`](../labelling/AnnotationrulesPerDataset.md).
- The labelled files of each curator, and the final consensus labelled file, for both the core set and the validation set

### 2.1 Select the core set (`al_loop/embedingsSBioBERT.py` + `al_loop/coreSetExtraction.py`)

The core set is chosen to cover the variety of sentences in the pool as widely as possible, rather than at random. This gives the first model a varied starting point.

```bash
python embedingsSBioBERT.py filtered_sentences_training.csv training_embeddings.csv \
  -tokenizer pritamdeka/S-BioBert-snli-multinli-stsb \
  -model pritamdeka/S-BioBert-snli-multinli-stsb
```

Then select 150 sentences with a greedy core-set selection. The script starts from one random sentence and keeps adding the sentence that is furthest (cosine distance) from the ones already selected:

```bash
python coreSetExtraction.py \
  -embeddings training_embeddings.csv \
  -selection 150 \
  -metadata filtered_sentences_training.csv \
  -output coreset.csv
```

`-metadata` is the same file that was embedded, so `coreset.csv` keeps all of the gene columns (`pmid, number, text, gene, start, end, id, uniprotid, sa`).

The study used the script's default seed (`-seed 42`), which sets the random sentence the selection starts from.

### 2.2 Select the validation set

The 150 core-set sentences were removed from the pool, and 500 sentences were then drawn at random from what was left. This was done with a one-off Python command, not with a script in this repository, so it cannot be re-run from here. To replicate the study, use the validation set archived on Zenodo.

### 2.3 Label both sets (`labelling/`)

The core set and the validation set are labelled separately but in exactly the same way. The commands below use `SET` for either `coreset` or `validation`. Each gene in each sentence gets a label (regulator of chondrogenesis or not) by following the labelling guidelines.

**1. Convert to the labelling app format** (`modelToLabellingFormatting.py`). This gives one row per gene. `-group` keeps the genes of the same sentence together (for faster labelling) and shuffles the order of the sentences:

```bash
python modelToLabellingFormatting.py -input ${SET}.csv -output ${SET}_appFormat.csv -group
```

**2. Label independently.** Each curator gets their own copy of `${SET}_appFormat.csv`, loads it in `labelling_shiny_app.R`, and labels every gene without seeing the other curator's labels to avoid bias.

```bash
Rscript -e "shiny::runApp('labelling_shiny_app.R', launch.browser = TRUE)"
```

**3. Collect the disagreements** (`labellingToRevisionFormatting.py`). This merges the two curators' files and keeps only the sentences where the labels differ. It also adds an empty `Final` row for each of them, to be filled in during the revision:

```bash
python labellingToRevisionFormatting.py \
  -files ${SET}_appFormat_curator1.csv ${SET}_appFormat_curator2.csv \
  -curators Curator1 Curator2 \
  -out ${SET}_revision.csv \
  -group
```

**4. Reach a consensus.** The curators review each disagreement together in `revision_shiny_app.R` and fill in the `Final` rows with the agreed label:

```bash
Rscript -e "shiny::runApp('revision_shiny_app.R', launch.browser = TRUE)"
```

**5. Build the consensus labelled file** (`fusingAgreementData.py`). This takes the genes both curators already agreed on (from one curator's file) and adds the `Final` decisions for the rest:

```bash
python fusingAgreementData.py \
  -fileCurator ${SET}_appFormat_curator1.csv \
  -fileAgree ${SET}_revision.csv \
  -curatorAgree Final \
  -fileOut ${SET}_labelled.csv
```

The per-curator files (step 2) and the consensus file (step 5) are the ones archived on Zenodo for both sets. The per-curator files can also be used to calculate inter-annotator agreement.

### 2.4 Remove the labelled sentences from the pool

The final unlabelled pool for the AL loop is the training–validation pool minus the core set and the validation set. Like the random sampling, this removal was done with a one-off Python command that is not part of the repository. To replicate the study, take the core-set and validation files from Zenodo and remove their sentences from `filtered_sentences_training.csv`, matching on `pmid` + `number`.

---


## 3. Active Learning Iterations

Each iteration of the active learning (AL) loop trains a model on all of the labelled data so far and evaluates it on the validation set. The trained model then scores the unlabelled pool, and a new batch of sentences is selected from it. That batch is labelled by the curators (as in Part 2) and added to the training data for the next iteration.

The loop covers the core model and iterations 1 to 6. The steps are the same every time, so they are described once below. Only the training and selection settings change between iterations:

| Iteration | Training data | Weighted loss function | Hyperparameters | Batch selection score |
|---|---|---|---|---|
| Core | Core set | No | Fixed | BALD |
| 1 | Core set + batch 1 | No | Fixed | BALD |
| 2 | Core set + batches 1–2 | No | Fixed | Weighted BALD |
| 3 | Core set + batches 1–3 | Yes | Fixed | Weighted BALD |
| 4 | Core set + batches 1–4 | Yes | Fixed | Weighted BALD |
| 5 | Core set + batches 1–5 | Yes | Grid search | Weighted BALD |
| 6 | Core set + batches 1–6 | No | Grid search | Final model, NO new batch |

"Batch *n*" is the batch selected by the model of the previous iteration and labelled in between. For example, batch 1 is selected by the core model.

After every training run, the model classifies the gene mentions of the validation set, and its performance is recorded. These results (mainly AUC-ROC) guided the changes to the training settings from one iteration to the next. The reasoning is explained in the paper and is not repeated here.

The labelled batch of each iteration (per curator and consensus), plus the training and validation results of each iteration are on Zenodo, see [`data/README.md`](../data/README.md))

The commands below use `ITER` for the iteration number (`0` for the core model) and `NEXT` for the next one (`ITER + 1`).

### 3.1 Prepare the model inputs (`labelling/modelToLabellingFormatting.py` + `al_loop/appToNLPFormatting.py`)

The model takes one row per gene mention. The target gene is masked as `[TARGET][GENE][/TARGET]`, and the other genes of the sentence are masked as `[GENE]`. `appToNLPFormatting.py` does this masking and turns `Yes`/`No` labels into `1`/`0`. `-columnAdd text` names the output column `text`, which is the name the training script expects.

----
----
**Training data.** Concatenate the consensus labelled files of the core set and of every batch labelled so far (all in the labelling app format), then format them:
**We need to check this because I must have done it automatically but I have not done it here**
----
----

```bash
python appToNLPFormatting.py training_iter${ITER}_labelled.csv training_iter${ITER}_nlpFormat.csv -columnAdd text
```

**Validation data.** This only needs to be done once, because the validation set is the same in every iteration:

```bash
python appToNLPFormatting.py validation_labelled.csv validation_nlpFormat.csv -columnAdd text
```

**Pool.** The pool is still in the Part 1 format (one row per sentence), so it first has to be expanded to one row per gene. It is re-created every iteration, because each labelled batch is removed from it (step 3.7):

```bash
python modelToLabellingFormatting.py -input pool_iter${ITER}.csv -output pool_iter${ITER}_appFormat.csv -group
python appToNLPFormatting.py pool_iter${ITER}_appFormat.csv pool_iter${ITER}_nlpFormat.csv -columnAdd text
```

### 3.2 Train and evaluate the model (`trainingModelTestPredictionBALDPool.py`)

This fine-tunes PubMedBERT on the training data. It then predicts the validation set (`-test`) and computes the BALD uncertainty score of every pool row with MC dropout (`-iterMC` stochastic passes):

```bash
python trainingModelTestPredictionBALDPool.py \
  -train training_iter${ITER}_nlpFormat.csv \
  -test validation_nlpFormat.csv \
  -pool pool_iter${ITER}_nlpFormat.csv \
  -out results_iter${ITER} \
  -model <path to PubMedBERT model> \
  -tokenizer <path to PubMedBERT tokenizer> \
  -iteration ${ITER} \
  -iterMC <MC dropout passes> \
  -epoch <epochs> \
  -batch <batch size> \
  -lr <learning rate> \
  -warmup <warmup ratio> \
  -weightDecay <weight decay> \
  -weightLossFunction <True|False>
```

- `-weightLossFunction`: `False` for the core model and iterations 1, 2 and 6, and `True` for iterations 3, 4 and 5 (see the table above).
- **Grid search (iterations 5 and 6):** the grid search uses this same script, run once per hyperparameter combination by changing only its arguments. The model with the best validation performance is kept as the model of the iteration, and it is the one used in the rest of the steps.

`results_iter${ITER}` then contains:

- The fine-tuned model (`trained_model/`)
- The validation predictions (`<seed>_testPredictions_iter${ITER}.csv`). Record the model's performance on the validation set from this file.
- The pool BALD scores (`<seed>_poolBALD_iter${ITER}.csv`)

For iteration 6 the loop stops here as it is the last iteration done and there was no selection of the next batch to label.

### 3.3 Classify the pool and get its embeddings (`finetunnedModelClassification.py`)

The trained model classifies every pool row and saves its CLS embeddings. The probabilities are used for the class weights (3.4), and the embeddings for the clustering (3.5):

The script does not create its output folder, so create it first:

```bash
mkdir -p results_iter${ITER}/pool_predictions

python finetunnedModelClassification.py \
  -batch pool_iter${ITER}_nlpFormat.csv \
  -model results_iter${ITER}/trained_model \
  -tokenizer results_iter${ITER}/trained_model \
  -batchNumber 0 \
  -prefix pool_classification \
  -prefixEmbeddings pool_embeddings \
  -out results_iter${ITER}/pool_predictions
```

This writes `pool_classification_0.csv` (probabilities) and `pool_embeddings_0.csv` (CLS embeddings).

**Large pools (parallel run).** When the pool is too large to classify in one go, split it into parts with `batchingPoolDataset.py`. In the study, the pool was split into 200 parts so that 200 jobs could run in parallel. The number 200 was chosen to fit the HPC cluster the jobs ran on. It does not come from any analysis and has no effect on the results, so pick whatever number of parts suits your own setup.

`batchingPoolDataset.py` splits the file in its original row order into `-batches` consecutive parts of about the same size, and saves them as `<prefix>_<n>.csv` (`n` from `0` to `batches - 1`). The output folder is created if it doesn't exist:

```bash
python batchingPoolDataset.py \
  -input pool_iter${ITER}_nlpFormat.csv \
  -batches 200 \
  -out pool_iter${ITER}_batches \
  -prefix pool_iter${ITER}_batch
```

Then classify each part in parallel (e.g. as separate HPC jobs) with the command above. For part `N`, use `-batch pool_iter${ITER}_batches/pool_iter${ITER}_batch_${N}.csv -batchNumber ${N}`, so each part writes its own `pool_classification_${N}.csv` and `pool_embeddings_${N}.csv`. Finally, merge the parts into one file and one embeddings file, keeping the header only once. The files are listed in numeric order (see the note below):

```bash
N_PARTS=200
awk 'FNR==1 && NR!=1 { next } { print }' $(for i in $(seq 0 $((N_PARTS - 1))); do echo results_iter${ITER}/pool_predictions/pool_embeddings_$i.csv; done) > results_iter${ITER}/pool_embeddings.csv
awk 'FNR==1 && NR!=1 { next } { print }' $(for i in $(seq 0 $((N_PARTS - 1))); do echo results_iter${ITER}/pool_predictions/pool_classification_$i.csv; done) > results_iter${ITER}/pool_classification.csv
```

> **Keep the parts in the same order.** The embeddings file has no `pmid`/`number` columns, so rows are matched to sentences by their position. Both files have to list the parts in the same order, and in the original pool order. A shell glob sorts `_10` before `_2`, so with 10 or more parts, list the files in numeric order instead of using `*`.

The steps below use the merged files, `results_iter${ITER}/pool_classification.csv` and `results_iter${ITER}/pool_embeddings.csv`. With a single run, use the `_0` files instead.

### 3.4 Weight by predicted probability (`sampleBALDClassWeighthing.R`)

This step is only needed for the iterations whose batch is selected with the weighted BALD score (iterations 2 to 5, see the table above). For the core model and iteration 1, which use the plain BALD score, skip it and go to 3.5.

In this step, each row gets a weight that is the inverse of how many rows fall in its `prob_1` bin (`[0, 0.1]`, …, `(0.9, 1]`). Rare probability ranges are weighted up. The weight is saved in a new `weights` column.

```bash
Rscript sampleBALDClassWeighthing.R \
  -i results_iter${ITER}/pool_classification.csv \
  -o results_iter${ITER}/pool_classification_classWeights.csv
```

The weights are applied in the selection step (3.6), where the `-weights` argument of `hybridBALDClusterRandomSampling.py` multiplies the BALD score by this column (`BALD × weights`).

### 3.5 Cluster the pool (`cosineDistancesCalculate.py` + `kMedoidsClustering.py` + `separatingCosineDistanceMatrix.sh`)

Part of the sampling is going to be based on diversity, which is going to be based on selecting samples from different clusters.

**1. Cosine distance matrix** between all of the pool embeddings. `-matrixFolder` must already exist.

```bash
mkdir -p results_iter${ITER}/cosine

python cosineDistancesCalculate.py \
  -embeddings results_iter${ITER}/pool_embeddings.csv \
  -matrixFolder results_iter${ITER}/cosine \
  -matrixPrefix pool_cosine \
  -batches 1 \
  -numberBatch 0
```

**Large pools (parallel run).** With a large pool, compute the matrix in parts. Run once per part with `-batches N` and `-numberBatch 0` to `N-1`, for example as separate HPC jobs. Each part holds a block of rows of the full matrix, so merging the parts in order (the same `awk` command as in 3.3, with the files listed in numeric order) gives the full matrix.

The steps below use `results_iter${ITER}/cosine/pool_cosine_0.csv`. When the matrix was computed in parts, use the merged file instead.

**2. k-medoids clustering** on the distance matrix. This adds the `cluster`, `medoid` and `outlier` columns to the pool classification:

```bash
python kMedoidsClustering.py \
  -pool results_iter${ITER}/pool_classification.csv \
  -cosineDistances results_iter${ITER}/cosine/pool_cosine_0.csv \
  -out results_iter${ITER}/pool_classification_clusters.csv \
  -k <number of clusters>
```

**3. One distance file per row.** The sampling step (3.6) looks up the distances of single sentences, to find the nearest neighbours of a medoid or outlier. Splitting the matrix into one small file per row (`sample_<row>.csv`) means that step does not have to load the whole matrix into memory, which matters for large pools:

```bash
bash separatingCosineDistanceMatrix.sh results_iter${ITER}/cosine/pool_cosine_0.csv results_iter${ITER}/distances
```

The script skips rows whose file already exists, so it can be re-launched and continue where a previous run stopped.

### 3.6 Select the batch (`fusingParalelResults.py` + `hybridBALDClusterRandomSampling.py`)

First, merge the BALD scores, the pool classification and the clusters into one file:

```bash
python fusingParalelResults.py \
  -bald results_iter${ITER}/<seed>_poolBALD_iter${ITER}.csv \
  -label <pool classification file> \
  -cluster results_iter${ITER}/pool_classification_clusters.csv \
  -out results_iter${ITER}/pool_fusedResults.csv
```

`-label` depends on the selection score of the iteration:

- **Weighted BALD (iterations 2 to 5):** `results_iter${ITER}/pool_classification_classWeights.csv`, the output of 3.4, so that the fused file has the `weights` column.
- **Plain BALD (core model and iteration 1):** `results_iter${ITER}/pool_classification.csv`, the output of 3.3, because 3.4 was skipped.

Then select the batch. For each cluster, the quota is split into:

- **Diversity samples:** the medoid and the outlier of the cluster
- **Uncertainty samples:** the highest-scoring rows, keeping one per sentence. The score is the plain BALD score, or `BALD × weights` when `-weights` is given
- **Random samples:** about 10% of the quota

The same script is used in every iteration. Only the `-weights` argument changes, which takes the name of the column the BALD score is multiplied by.

**Weighted BALD (iterations 2 to 5):**

```bash
python hybridBALDClusterRandomSampling.py \
  -input results_iter${ITER}/pool_fusedResults.csv \
  -distance results_iter${ITER}/distances \
  -sampling <number of sentences to select> \
  -out results_iter${ITER}/pool_hybridSamplingResults.csv \
  -seed <seed> \
  -weights weights
```

**Plain BALD (core model and iteration 1):** leave `-weights` out.

```bash
python hybridBALDClusterRandomSampling.py \
  -input results_iter${ITER}/pool_fusedResults.csv \
  -distance results_iter${ITER}/distances \
  -sampling <number of sentences to select> \
  -out results_iter${ITER}/pool_hybridSamplingResults.csv \
  -seed <seed>
```

The output marks the chosen sentences with `selected = True`, together with the reason each one was chosen (`reason`). With `-weights`, it also has a `BALD_weighted` column with the score used for the uncertainty samples.

### 3.7 Separate the batch from the pool (`poolAndBatchUpdating.py`)

This moves the selected sentences out of the pool and into the batch to label. The batch is tagged with the next iteration number (`NEXT`), because its labels are used to train that iteration's model:

```bash
python poolAndBatchUpdating.py \
  pool_iter${ITER}.csv \
  results_iter${ITER}/pool_hybridSamplingResults.csv \
  ${NEXT} \
  -outUnlabelled pool_iter${NEXT}.csv \
  -outBatch batch_iter${NEXT}.csv
```

### 3.8 Label the batch (`labelling/`)

`batch_iter${NEXT}.csv` is labelled. Follow Part 2, step 2.3: format for the app, label independently by the two curators, revise the disagreements, and fuse into a consensus file. Each iteration is labelled with the rules for that iteration in the labelling guidelines (see also [`labelling/AnnotationrulesPerDataset.md`](../labelling/AnnotationrulesPerDataset.md)). The rules are additive, so later iterations add rules to the earlier ones.

The consensus labelled batch is added to the training data, and the loop starts again from 3.1 with the next iteration.

---

**Output of this part:**

| Output | Contents |
|---|---|
| `results_iter0` … `results_iter6` | The model of each iteration, its validation predictions and pool BALD scores |
| `batch_iter1` … `batch_iter6` (labelled) | The 6 batches selected and labelled during the loop |
| `results_iter6/trained_model` | The final model, trained on the core set plus the 6 labelled batches |

---

## 4. Production Model and Application Predictions

Once the AL loop is finished, one last PubMedBERT model is trained: the **production model**. It is trained on the training data of the last iteration **plus the validation set**, so it learns from all of the labelled data of the training–validation pool. The validation set can be added now because it is no longer needed to compare iterations. The held-out set is still kept out of training.

The production model then classifies every gene mention of the application dataset (`filtered_sentences_application.csv`). These predictions are used for the benchmarking and for the post-processing of the candidate regulators.

The production model's gene classification outputs are on Zenodo (`modelPubMedGeneExtractionResults/`, see [`data/README.md`](../data/README.md)).

### 4.1 Prepare the training data

The validation set is already in the model format (`validation_nlpFormat.csv`, from 3.1). Concatenate it with the training data of the last iteration (core set + batches 1–6).

Both files come from `appToNLPFormatting.py`, so they have the same columns. The training script only uses `text` and `labels`.

### 4.2 Train the production model (`benchmark_comparison/trainingProductionModel.py`)

`trainingProductionModel.py` does the same training as `trainingModelTestPredictionBALDPool.py` (same tokenization, special tokens and training arguments), but only trains and saves the model. There is no validation prediction and no BALD scoring of a pool, so it does not need `baal`:

```bash
python trainingProductionModel.py \
  -train production_training_nlpFormat.csv \
  -out production_model \
  -model <path to PubMedBERT model> \
  -tokenizer <path to PubMedBERT tokenizer> \
  -epoch <epochs> \
  -batch <batch size> \
  -lr <learning rate> \
  -warmup <warmup ratio> \
  -weightDecay <weight decay> \
  -weightLossFunction <True|False>
```

The hyperparameters and `-weightLossFunction` are the ones of the final model (iteration 6, see the table in Part 3).

`production_model` then contains the trained model and its tokenizer (`trained_model/`) and the time spent in each step (`time_tracking.txt`).

### 4.3 Prepare the application pool (`labelling/modelToLabellingFormatting.py` + `al_loop/appToNLPFormatting.py`)

The application dataset is in the Part 1 format (one row per sentence), so it is expanded to one row per gene and masked, exactly as the pool in 3.1:

```bash
python modelToLabellingFormatting.py -input filtered_sentences_application.csv -output application_appFormat.csv -group
python appToNLPFormatting.py application_appFormat.csv application_nlpFormat.csv -columnAdd text \
  -inter -iter 0 -folderInter application_inter
```

`-inter` also saves the intermediate files of the masking. One of them, `application_inter/masked_sentences_middle_iter0.csv`, keeps the original position of each gene in the sentence and is needed in Part 6 to link each prediction back to its gene metadata. The folder given to `-folderInter` must already exist.

### 4.4 Classify the application pool (`al_loop/batchingPoolDataset.py` + `al_loop/finetunnedModelClassification.py`)

This is the same as the pool classification of the AL loop (3.3), but with the production model. The application pool is split into parts that are classified in parallel:

```bash
python batchingPoolDataset.py \
  -input application_nlpFormat.csv \
  -batches 200 \
  -out application_batches \
  -prefix application_batch
```

As in 3.3, the number of parts only needs to fit your own setup and has no effect on the results.

Classify each part `N` (e.g. as separate HPC jobs). Only the classification is needed here, so `-onlyClassification` skips the CLS embeddings. The output folder has to exist first:

```bash
mkdir -p production_model/application_predictions

python finetunnedModelClassification.py \
  -batch application_batches/application_batch_${N}.csv \
  -model production_model/trained_model \
  -tokenizer production_model/trained_model \
  -batchNumber ${N} \
  -prefix application_classification \
  -out production_model/application_predictions \
  -onlyClassification
```

Finally, merge the parts into one file, with the files listed in numeric order (see the note in 3.3):

```bash
N_PARTS=200
awk 'FNR==1 && NR!=1 { next } { print }' $(for i in $(seq 0 $((N_PARTS - 1))); do echo production_model/application_predictions/application_classification_$i.csv; done) > production_model/application_classification.csv
```

`application_classification.csv` has one row per gene mention, with the logits, the predicted label (`predicted_label`) and the probability of each class (`prob_0`, `prob_1`). This is the file used for the benchmarking and the post-processing.

---

**Output of this part:**

| Output | Contents |
|---|---|
| `production_model/trained_model` | The production model, trained on the core set, the 6 labelled batches and the validation set |
| `production_model/application_classification.csv` | The production model's predictions for every gene mention of the application dataset |

---

## 5. Held-out Evaluation: Production Model and Benchmark Models

The held-out dataset (`filtered_sentences_heldout.csv`) is used to evaluate the production model and to compare it with the benchmark models: a logistic regression on PubMedBERT embeddings and LLMs. It comes from literature published after the training–validation window and is never used for training, so all of the models are evaluated on the same unseen data.

The scripts for the benchmark models are in `benchmark_comparison/` (see [`benchmark_comparison/README.md`](../benchmark_comparison/README.md)). They need their own environments, listed in `envs/` (`requirements_lr_benchmarking.txt` for the logistic regression, `requirements_qwen_benchmarking.txt` and `requirements_llama_benchmarking.txt` for the LLMs), because some HuggingFace models are not compatible with the same package versions.

The held-out results of all of the models are on Zenodo (`LLMs/`, `logisticRegressionClassificationHeldOut.csv` and `alLoopIterations/`, see [`data/README.md`](../data/README.md)).

### 5.1 Label and format the held-out set (`labelling/` + `al_loop/appToNLPFormatting.py`)

The held-out set is labelled exactly as the core set and the validation set (Part 2, step 2.3, with `SET=heldout`), using the held-out rules of the labelling guidelines (see the *Held-out dataset* section of [`labelling/AnnotationrulesPerDataset.md`](../labelling/AnnotationrulesPerDataset.md)). The input of step 2.3 is `filtered_sentences_heldout.csv` directly, since the held-out set is labelled in full:

```bash
python modelToLabellingFormatting.py -input filtered_sentences_heldout.csv -output heldout_appFormat.csv -group
```

The consensus file, `heldout_labelled.csv`, is then put in the model format as in 3.1:

```bash
python appToNLPFormatting.py heldout_labelled.csv heldout_nlpFormat.csv -columnAdd text
```

`heldout_nlpFormat.csv` (one row per gene mention, with `pmid`, `number`, `text` and `labels`) is the input of every model below.

### 5.2 Production model predictions (`al_loop/finetunnedModelClassification.py` + `al_loop/bootstrapRetrain.py`)

The production model (Part 4) classifies the held-out set with the same script as the application pool. The held-out set is small, so it runs in one go:

```bash
mkdir -p production_model/heldout_predictions

python finetunnedModelClassification.py \
  -batch heldout_nlpFormat.csv \
  -model production_model/trained_model \
  -tokenizer production_model/trained_model \
  -batchNumber 0 \
  -prefix heldout_classification \
  -out production_model/heldout_predictions \
  -onlyClassification
```

`heldout_classification_0.csv` keeps the `labels` column next to the predictions (`predicted_label`, `prob_0`, `prob_1`), so the performance (AUC-ROC, F1, precision, recall) is computed directly from this file, with `prob_1` as the probability of the positive class.

**Confidence intervals.** `bootstrapRetrain.py` resamples the held-out set by sentence (`-cluster pmid number`, so all genes of a sentence stay together) and predicts every resampled dataset with the production model. The model is not retrained, despite the name:

```bash
python bootstrapRetrain.py \
  -data heldout_nlpFormat.csv \
  -out bootstrap_heldout \
  -model production_model/trained_model \
  -tokenizer production_model/trained_model \
  -batch <prediction batch size> \
  -outFolder production_model/heldout_bootstrap \
  -iterations <bootstrap iterations> \
  -cluster pmid number \
  -seed <seed>
```

This writes one prediction file per iteration (`bootstrap_heldout_<iteration>.csv`). The script does not compute the metrics. They are computed in Part 6 (step 6.1).

### 5.3 Logistic regression baseline (`benchmark_comparison/logisticRegressionWithEmbeddings.py`)

The logistic regression is trained on sentence embeddings from the **base** PubMedBERT model (not fine-tuned), using only the core set as training data (`training_iter0_nlpFormat.csv`, the training data of the core model from 3.1), and evaluated on the held-out set:

```bash
python logisticRegressionWithEmbeddings.py \
  -training training_iter0_nlpFormat.csv \
  -test heldout_nlpFormat.csv \
  -out lr_baseline_heldout.csv \
  -model <path to PubMedBERT model> \
  -tokenizer <path to PubMedBERT tokenizer> \
  -batch <batch size> \
  -seed <seed>
```

The script fits two logistic regressions, one on the mean-pooled token embeddings and one on the CLS embedding. `lr_baseline_heldout.csv` has the held-out rows with the predictions of both (`label_pool`, `prob_0_pool`, `prob_1_pool` and `label_cls`, `prob_0_cls`, `prob_1_cls`).

### 5.4 LLM datasets (`benchmark_comparison/creationDatasetsLLMs.py`)

The LLMs take the held-out set as a HuggingFace `DatasetDict` in chat format: one conversation per gene mention, with the system prompt, the user prompt (with the masked sentence inserted in its `{sentence_to_classify}` placeholder) and the expected answer (`Yes` for label 1, `No` for label 0):

```bash
python creationDatasetsLLMs.py \
  -input heldout_nlpFormat.csv \
  -systemPrompt system_prompt.xml \
  -userPrompt user_prompt.md \
  -nameHfDataset heldout \
  -output datasets/llm_heldout
```

Use the system and user prompts of the study which can be found in Zenodo.

`datasets/llm_heldout` is then given to the inference scripts with `-split heldout`: `LLMInferenceHF.py` for non-quantised models and `LLMInferenceHFAWQ.py` for AWQ-quantised Llama models.

---

**Output of this part:**

| Output | Contents |
|---|---|
| `heldout_nlpFormat.csv` | The labelled held-out set, one row per gene mention |
| `production_model/heldout_predictions/heldout_classification_0.csv` | The production model's predictions for the held-out set |
| `production_model/heldout_bootstrap/` | The bootstrap predictions for the production model's confidence intervals |
| `lr_baseline_heldout.csv` | The logistic regression predictions (mean-pooled and CLS embeddings) for the held-out set |
| `datasets/llm_heldout` | The held-out set in chat format, ready for LLM inference |

---

## 6. Post-processing: Metrics, Gene IDs, GO Coverage and ORA

This part does not train or run any model. It takes the outputs of Parts 3 to 5 and turns them into:

- **Performance metrics** with confidence intervals for the production model on the held-out set
- **Gene-level results:** each predicted gene mention linked back to its GNorm2 metadata and to a single human Entrez ID
- **A biological evaluation against the Gene Ontology (GO):** how many known chondrogenesis genes the model recovers (coverage), which new candidate regulators it proposes, and which GO processes are over-represented among its regulators (ORA)
- **The figures** of the paper

The scripts are in `postprocessing/` (see [`postprocessing/README.md`](../postprocessing/README.md)). The requirements are in `envs/environment_postprocessing.txt` (Python packages in `envs/requirements_python_postprocessing.txt`, R packages in `envs/requirements_R_postprocessing.txt`). Step 6.4 queries MyGene.info, so it needs internet access.

The production model's gene classification outputs and the GO coverage results are on Zenodo (`modelPubMedGeneExtractionResults/`, see [`data/README.md`](../data/README.md)).

### 6.1 Held-out performance of the production model (`bootstrappingResultsAnalysis.R`)

This computes F1, accuracy, AUC-ROC, precision and recall for each bootstrap file of 5.2, and the mean and standard deviation of each metric across all of them. The default column names (`labels`, `predicted_label`, `prob_1`) and positive class (`1`) are the ones of the PubMedBERT outputs, so no options are needed:

```bash
Rscript bootstrappingResultsAnalysis.R \
  production_model/heldout_bootstrap \
  production_heldout_bootstrap_metrics.csv \
  --summary_file=production_heldout_bootstrap_summary.csv
```

`production_heldout_bootstrap_metrics.csv` has one row per bootstrap file. The 95% confidence interval of each metric is its 2.5 and 97.5 percentiles in this file.

### 6.2 Gene mentions of the application dataset (`gnorm2ToGeneMentions.py`)

The predictions only have the masked sentence (`[TARGET][GENE][/TARGET]`), not which gene was the target. To get it back, the Part 1 file (one row per sentence, with lists of genes) is first expanded into one row per gene mention with its GNorm2 metadata (gene text, Entrez ID, UniProt ID, species):

```bash
python gnorm2ToGeneMentions.py \
  -input filtered_sentences_application.csv \
  -output application_geneMentions.csv
```

### 6.3 Link the predictions to the gene metadata (`mergePredictionsWithGeneMetadata.py`)

The predictions (4.4) are joined with the gene mentions (6.2), using the intermediate file with the original gene positions saved in 4.3 (`-inter`):

```bash
python mergePredictionsWithGeneMetadata.py \
  -metadata application_geneMentions.csv \
  -interFile application_inter/masked_sentences_middle_iter0.csv \
  -labels production_model/application_classification.csv \
  -output application_predictions_metadata.csv \
  -interFolder application_merge_inter
```

Both joins are inner joins, so only the gene mentions with both a prediction and metadata are kept.

### 6.4 Recover IDs for the genes GNorm2 could not normalise (`fallbackNormaliseMygene.py`)

GNorm2 leaves some gene mentions without an Entrez ID (`-`). Their names are looked up in MyGene.info (human genes only), and the recovered IDs are saved in a new `id_myGene` column:

```bash
python fallbackNormaliseMygene.py \
  application_predictions_metadata.csv \
  application_predictions_metadata_mygene.csv \
  -inter application_mygene_inter
```

`-inter` is optional and must be an existing folder. It saves the name-to-ID table returned by MyGene.info.

### 6.5 Keep human genes with a single ID (`harmoniseHumanGeneIDs.py`)

This keeps only human genes and merges the two IDs into one final ID, `id_human`: the GNorm2 ID when there is one, otherwise the MyGene.info ID. It then removes the duplicated (gene, predicted label) pairs.

It is run twice on the application predictions:

**All genes.** This gives the unique gene-label table, and, in the intermediate folder, `genes_withSomeHumanID_unified.csv`, which keeps **every** gene mention (before removing duplicates). That file is used to count in how many sentences each gene was predicted as a regulator (6.6 and 6.8):

```bash
python harmoniseHumanGeneIDs.py \
  application_predictions_metadata_mygene.csv \
  application_humanGenes.csv \
  -columnLabel predicted_label \
  -finalIdcolumn id_human \
  -inter application_harmonise_inter
```

**Without the manually labelled genes.** The same table, after removing every gene that the curators already labelled (core set, batches 1–6, validation set and held-out set). This leaves only the genes the model classified on its own:

```bash
python harmoniseHumanGeneIDs.py \
  application_predictions_metadata_mygene.csv \
  application_humanGenes_filtered.csv \
  -columnLabel predicted_label \
  -finalIdcolumn id_human \
  -filter manual_humanGenes.csv \
  -inter application_harmonise_filtered_inter
```

**The manually labelled genes (`manual_humanGenes.csv`).** The filter file (and the manually labelled input of the ORA in 6.9) is built by running steps 6.2 to 6.5 on the labelled data instead of on the predictions:

1. Concatenate the consensus labelled files (labelling app format) of all of the labelled sets, and format them with `-inter`:

   ```bash
   mkdir -p manual_inter
   awk 'FNR==1 && NR!=1 { next } { print }' coreset_labelled.csv batch_iter{1..6}_labelled.csv validation_labelled.csv heldout_labelled.csv > manual_labelled.csv
   python appToNLPFormatting.py manual_labelled.csv manual_nlpFormat.csv -columnAdd text -inter -iter 0 -folderInter manual_inter
   ```

2. Build the gene mentions from the Part 1 files the labelled sentences come from (training–validation and held-out):

   ```bash
   awk 'FNR==1 && NR!=1 { next } { print }' filtered_sentences_training.csv filtered_sentences_heldout.csv > filtered_sentences_labelledSources.csv
   python gnorm2ToGeneMentions.py -input filtered_sentences_labelledSources.csv -output manual_geneMentions.csv
   ```

   The merge in the next step is an inner join, so only the labelled sentences are kept.

3. Merge, recover IDs and harmonise, as for the predictions, but with the annotated label (`labels`) instead of the predicted one:

   ```bash
   python mergePredictionsWithGeneMetadata.py \
     -metadata manual_geneMentions.csv \
     -interFile manual_inter/masked_sentences_middle_iter0.csv \
     -labels manual_nlpFormat.csv \
     -output manual_metadata.csv

   python fallbackNormaliseMygene.py manual_metadata.csv manual_metadata_mygene.csv

   python harmoniseHumanGeneIDs.py \
     manual_metadata_mygene.csv \
     manual_humanGenes.csv \
     -columnLabel labels \
     -finalIdcolumn id_human
   ```

### 6.6 Coverage of chondrogenesis GO terms (`coverageAnalysisGOSingleTerm.R`)

This checks how many of the human genes annotated to a GO term the model predicted as regulators (coverage), and lists the regulators that are **not** annotated to it: these are the new candidate regulators, ranked by the number of sentences that classified them as regulators.

The study analyses *chondrocyte differentiation* (`GO:0002062`). The candidates that are not in it are also checked against the broader *cartilage development* term (`GO:0051216`) with `--parent_go_term`:

```bash
Rscript coverageAnalysisGOSingleTerm.R GO:0002062 coverage/chondrocyte_differentiation \
  application_humanGenes_filtered.csv \
  application_harmonise_inter/genes_withSomeHumanID_unified.csv \
  --parent_go_term=GO:0051216
```

- The third argument (`final_csv`) is the unique gene-label table from 6.5.
- The fourth argument (`full_csv`) is the file with every gene mention, from the intermediate folder of the "all genes" run of 6.5. It is used to count in how many sentences each gene was predicted as a regulator.

Coverage is given both for the term with all of its descendants and for the term alone. The script also writes Venn diagrams, the ranked candidate regulators (`frequency_classification_regulators_genes_not_in_chondrocyte_differentiation_andOffspring.csv`), and the GO genes the model missed, split into genes that were in the dataset but predicted as non-regulators and genes that never appeared in the dataset. The full list of output files is in [`postprocessing/README.md`](../postprocessing/README.md).

### 6.7 Coverage of every human GO Biological Process term (`coverageAllGOHumanTerms.R`)

The same coverage (term and descendants) is calculated for every GO Biological Process term with at least one human gene. This shows which processes are well covered by the model's regulators, and so how specific the predictions are to chondrogenesis.

There are too many terms for one run, so the script processes one range of rows of the GO term table at a time. Each run prints the total number of terms at the start, and a `fin_batch` beyond it is capped. The output folder must already exist:

```bash
mkdir -p coverage/allGO

Rscript coverageAllGOHumanTerms.R <init_batch> <fin_batch> application_humanGenes_filtered.csv coverage/allGO
```

Run it for consecutive ranges (e.g. `1 1000`, `1001 2000`, … as separate HPC jobs) until all of the terms are covered. Each range writes `coverage_allGO_terms_human_<init_batch>_<fin_batch>.csv`, and the files can be merged with the same `awk` command as in 3.3.

### 6.8 Number of mentions per gene and label (`labelClassificationGeneMentions.R`)

For each human gene, this counts how many of its mentions were predicted as regulator (`label_1`) and as non-regulator (`label_0`). It uses the file with every gene mention from 6.5. The output folder must already exist:

```bash
Rscript labelClassificationGeneMentions.R \
  application_harmonise_inter/genes_withSomeHumanID_unified.csv \
  application_gene_label_counts.csv
```

### 6.9 Over-representation analysis (`ORA_analysis.Rmd`)

The ORA tests which GO Biological Processes are over-represented among the regulators (label `1`) and among the non-regulators (label `0`), for three gene sets:

| Gene set | Input file | Label column |
|---|---|---|
| Manually labelled genes | `manual_humanGenes.csv` (6.5) | `labels` |
| Final predictions | `application_humanGenes.csv` (6.5) | `predicted_label` |
| Final predictions without the manually labelled genes | `application_humanGenes_filtered.csv` (6.5) | `predicted_label` |

This is an R Markdown notebook, not a command-line script. Before running it, edit the `root.dir` of the `setup` chunk (the folder with the three files above), the three file names in the "Prepare Input" chunk, and the `ggsave()` path of the publication dotplot. Then knit it in RStudio (or run all of its chunks).

### 6.10 Figures (`histogramFrequencyGenesRegulatorClassification.R` + `modelALPerformanceAndDatasetCompositionPlot.R`)

These two scripts only make figures. Like the ORA notebook, they take no arguments: edit the input paths at the top, run them in RStudio, and export the plots from the plots panel (they are not saved to file).

- **`histogramFrequencyGenesRegulatorClassification.R`:** the distribution of the number of sentences that predicted each gene as a regulator, plus its summary statistics. The input is `coverage/chondrocyte_differentiation/frequency_classification_regulators_allNormalisedgenes_chondrocyte_differentiation.csv` (from 6.6).
- **`modelALPerformanceAndDatasetCompositionPlot.R`:** the AL performance per iteration, the composition of the training data, and the comparison with the random-selection baseline. It needs:
  - The validation predictions of each iteration, `results_iter<n>/<seed>_testPredictions_iter<n>.csv` (3.2)
  - The predictions of the iteration 6 model on the held-out set, obtained with `finetunnedModelClassification.py` exactly as in 5.2, but with `-model results_iter6/trained_model -tokenizer results_iter6/trained_model`
  - The number of sentences and of regulator/non-regulator genes in the training data of each iteration
  - The random-selection baseline results, which are on Zenodo (`alLoopIterations/`)

  See the script's configuration table in [`postprocessing/README.md`](../postprocessing/README.md) for where each file is set.

---

**Output of this part:**

| Output | Contents |
|---|---|
| `production_heldout_bootstrap_metrics.csv`, `production_heldout_bootstrap_summary.csv` | Held-out performance of the production model, per bootstrap file and summarised |
| `application_humanGenes.csv` | One row per human gene and predicted label, for the whole application dataset |
| `application_humanGenes_filtered.csv` | The same, without the manually labelled genes |
| `manual_humanGenes.csv` | One row per human gene and annotated label, for all of the labelled sets |
| `coverage/chondrocyte_differentiation/` | Coverage of `GO:0002062`, candidate regulators and missed GO genes |
| `coverage/allGO/` | Coverage of every human GO Biological Process term |
| `application_gene_label_counts.csv` | Number of regulator and non-regulator mentions per gene |
| ORA notebook output | Enriched GO terms of regulators and non-regulators, for the three gene sets |

---
