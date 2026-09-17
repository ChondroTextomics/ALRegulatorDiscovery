# Using the Trained Model on New Abstracts

This guide walks through using the already-trained model to classify genes in new abstracts, in three stages: turning new abstracts into a filtered sentence dataset (§1), reshaping that dataset into the model's expected input format (§2), and running the fine-tuned model to get a regulator/non-regulator label per gene (§3). Each section's output feeds directly into the next.

## 1. Preprocessing: From PubMed to a Filtered Sentence Dataset

Before the trained classifier can score any genes, new abstracts need to go through the same preprocessing pipeline used to build the training data. This turns a PubMed query (or a list of PMIDs you already have) into a sentence-level CSV containing only the sentences that mention both a recognised gene and a relevant concept term — the format the model expects as input.

Dependencies for these scripts are listed in `envs/`.

**Example — start and end of this stage:**

_pmids.txt_ (input to step 1.1)
```text
39764517
39764126
```

_filtered_sentences.csv_ (output of step 1.7)

| pmid | number | text | gene | start | end | id | uniprotid | sa |
|---|---|---|---|---|---|---|---|---|
|39764517|1|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells stemness.|['SPI1']|['0']|['4']|['6688']|['P17947']|['9606']|
|39764517|7|In vitro experiments identified SPI1 as a potential stemness target gene, which could enhance the stemness and chondrogenesis of OBMSCs.|['SPI1']|['34']|['38']|['6688']|['P17947']|['9606']|
|39764126|4|Electrical stimulation of chondrogenic progenitor cells increased SOX9 expression and promoted cartilage matrix deposition.|['SOX9']|['68']|['72']|['6663']|['P48436']|['9606']|

### 1.1 Retrieve articles from PubMed (`pipeline_process_text/fetchQueryResults.py`)

`fetchQueryResults.py` takes a PubMed-format query and a date range, and downloads the matching articles (title + abstract).

```bash
python fetchQueryResults.py \
  -out pmids.txt \
  -mindate "2025/01/01" \
  -maxdate "2025/12/31" \
  -db pubmed \
  -email you@example.com \
  -query '(chondrogenesis OR chondrocyte differentiation) AND "English"[Language]' \
  -retrieve articles.xml
```

If you already have a list of PMIDs instead of a query, skip the search and fetch data directly:

```bash
python fetchQueryResults.py \
  -out pmids.txt \
  -db pubmed \
  -email you@example.com \
  -pmidfile my_pmids.txt \
  -retrieve articles.xml
```

### 1.2 Parse the XML into a CSV (`pipeline_process_text/pubmedXMLtoCSV.py`)

`pubmedXMLtoCSV.py` extracts PMID, title and abstract from the XML into a simple CSV.

```bash
python pubmedXMLtoCSV.py -input articles.xml -out parsed.csv
```

### 1.3 Split articles into sentences (`pipeline_process_text/splitterArticleSentences.py`)

`splitterArticleSentences.py` breaks each article's title/abstract into one sentence per row.

```bash
python splitterArticleSentences.py -input parsed.csv -out sentences.csv
```

### 1.4 Convert to PubTator format (`pipeline_process_text/pubtatorFormatter.py`)

`pubtatorFormatter.py` reformats the sentences into the PubTator format GNorm2 requires.

```bash
python pubtatorFormatter.py -input sentences.csv -out sentences.pubtator -structure sentence
```

### 1.5 Run GNorm2 gene recognition (twice) (`pipeline_process_text/gnormSingularityExecution.sh`)

`gnormSingularityExecution.sh` runs GNorm2 gene/species normalization inside a container. It takes no command-line arguments — edit the variables at the top of the script (`results_directory`, `input_pubtator_file`, `setup_path`/`setup_file`, `gnorm_singularity_path`, `gnorm_script_path`) before running.

This needs to be run **twice**, once per setup config, so the results can be fused in the next step:
- once with the "all entities" setup config
- once with the "UniProt ID–restricted" setup config

```bash
bash gnormSingularityExecution.sh > run.log 2> run.err
```

> **Note:** the script calls `singularity exec` internally. On our cluster this now needs to be `apptainer exec` instead — the CLI is a drop-in replacement, so just swap the command name in the script if you hit a setuid install error from `singularity`.

The output for each run lands at `[results_directory]/output/<same filename as input>`.

### 1.6 Fuse the two GNorm2 result sets (`pipeline_process_text/fusionAllEntitiesAndUniprotID.py`)

`fusionAllEntitiesAndUniprotID.py` combines the "all entities" and "UniProt ID" runs into one CSV (sentence text + gene metadata) and one fused PubTator file.

```bash
python fusionAllEntitiesAndUniprotID.py \
  -allEntitiesInput results_allEntities/output/sentences.pubtator \
  -uniprotIDInput results_proteinID/output/sentences.pubtator \
  -format sentence \
  -outFolder fused
```

### 1.7 Filter to gene + concept sentences (`pipeline_process_text/filterSentencesGeneConcept.py`)

`filterSentencesGeneConcept.py` keeps only sentences containing at least one recognised gene **and** at least one term from a concept list (one term per line).

```bash
python filterSentencesGeneConcept.py \
  -input fused/genes-sentences.csv \
  -concepts concepts.txt \
  -output filtered_sentences.csv
```

> Use the same concept list the model was trained on (chondrogenesis-related terms) — inconsistent concept terms at this stage will feed the classifier sentences unlike the ones it learned from.

---

**Output of this stage:** `filtered_sentences.csv` — a sentence-level dataset of genes and their context, ready to be passed into the trained model for classification (next section).


## 2. Formatting for the Model

`filtered_sentences.csv` (the output of stage 1) isn't quite what the model takes as input yet: each row can still contain several candidate genes per sentence, and the model expects one row per candidate gene, with that gene masked as `[TARGET][GENE][/TARGET]` and any other genes in the same sentence masked as `[GENE]`. Getting there is two steps, pulled from two different folders in the repo — `labelling` and `al_loop`. For classifying new abstracts there's no human labelling involved, so only one script from each folder is needed; the labelling app, consensus revision and agreement-fusing scripts are for building training data and aren't part of this path.

### 2.1 Expand to one row per candidate gene (`labelling/modelToLabellingFormatting.py`)

Takes the stage-1 output directly (same `pmid, number, text, gene, start, end, id, uniprotid, sa` columns) and expands any multi-gene sentence into one row per gene, adding the index columns the masking step needs. The `label`/`association`/etc. columns it adds are left as `NA` — for inference these stay empty rather than being filled in by a curator.

```bash
python modelToLabellingFormatting.py -input filtered_sentences.csv -output filtered_sentences_appFormat.csv -group -seed 1
```

### 2.2 Convert to the masked NLP format (`al_loop/appToNLPFormatting.py`)

Reads the `sentence` column (default) and, for each row, masks that row's target gene as `[TARGET][GENE][/TARGET]` and any other genes in the same sentence as `[GENE]`, producing the `pmid, number, text, labels` format the model consumes. `labels` stays `NA` here since there's no ground truth for new abstracts.

```bash
python appToNLPFormatting.py filtered_sentences_appFormat.csv filtered_sentences_nlpFormat.csv -columnAdd text
```

---

**Example — start and end of this stage:**

_filtered\_sentences.csv_ (input to 2.1, one row, two genes)
```text
pmid,number,sentence,gene,start,end,id,uniprotid,sa
1952598,2,Synergistic action of transforming growth factor-beta and fibroblast growth factor.,"['transforming growth factor-beta', 'fibroblast growth factor']","['24', '60']","['55', '84']","['7040', '-']","['P01137', '-']","['9606', '9606']"
```

_filtered\_sentences\_nlpFormat.csv_ (output of 2.2, one row per gene)

| pmid | number | text | labels |
|---|---|---|---|
|1952598|2|Synergistic action of [GENE] and [TARGET][GENE][/TARGET].|NA|
|1952598|2|Synergistic action of [TARGET][GENE][/TARGET] and [GENE].|NA|

---

**Output of this stage:** `filtered_sentences_nlpFormat.csv` — ready to be passed to the trained model (`al_loop/finetunnedModelClassification.py`) for classification, covered next.

---

## 3. Classifying the Genes (`al_loop/finetunnedModelClassification.py`)

This runs the already fine-tuned model on `filtered_sentences_nlpFormat.csv` and gives each candidate gene a prediction (regulator [1] or not [0]) with the associated probabilities. This is the last stage for straightforward inference on new abstracts; the rest of `al_loop` (BALD scoring, clustering, hybrid sampling) exists to pick new sentences for human labelling during active learning.

```bash
python finetunnedModelClassification.py \
  -batch filtered_sentences_nlpFormat.csv \
  -model /path/to/finetuned_model \
  -tokenizer /path/to/finetuned_model_tokenizer \
  -batchNumber 1 \
  -prefix classification_results \
  -prefixEmbeddings classification_embeddings \
  -out results_classification
```

`-model`/`-tokenizer` point to a local copy of the fine-tuned model. The script loads it from disk rather than pulling it from the Hub directly, so it needs to be downloaded there first.

`-batchNumber` just labels the output files for a given run and it matters when splitting a large pool with `batchingPoolDataset.py`, but for a single run any value (e.g. 1) works fine.

---

**Example — start and end of this stage:**

_filtered\_sentences\_nlpFormat.csv_ (input)

| pmid | number | text | labels |
|---|---|---|---|
|1952598|2|Synergistic action of [TARGET][GENE][/TARGET] and [GENE].|NA|

_results\_classification/classification\_results\_1.csv_ (output)

| pmid | number | text | labels | logits_0 | logits_1 | predicted_label | prob_0 | prob_1 |
|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of [TARGET][GENE][/TARGET] and [GENE].|NA|-0.06|0.31|1|0.41|0.59|

---

**Output of this stage:** `classification_results_1.csv` — for each candidate gene, `predicted_label`/`prob_1` gives the model's call on whether it's a chondrogenesis regulator. This is the final deliverable of the "use the trained model on new abstracts" pipeline.
