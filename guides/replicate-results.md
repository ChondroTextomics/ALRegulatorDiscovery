# Replicating the Study Results

This guide walks through reproducing the datasets and results of the study, part by part. Each part builds on the outputs of the previous one.

1. **Data extraction:** from PubMed to the three filtered sentence datasets (this section)

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
