## Overview

This folder contains the scripts used to post-process and analyse the results obtained in the `al_loop` and `benchmark_comparison` repositories. They do not train or run any model. Instead, they take what those repositories produce (bootstrapped predictions, gene mentions annotated by GNorm2, and the gene-level labels predicted by the final classifier) and turn it into performance metrics and a biological evaluation of the predictions against the Gene Ontology (GO).

Requirements for this folder can found in the `envs` folder in this repository

---
## Files

### `bootstrappingResultsAnalysis.R`

**Description**

Reads a folder of bootstrapped result CSVs (one CSV per bootstrap sample, as produced by the `al_loop` final model) and computes F1, accuracy, AUC-ROC, precision and recall for each file. It can also write a summary file with the mean and standard deviation of each metric across all bootstraps.

Column names and the positive class can be changed, so the same script works for other models whose output files use different column names.

**Usage**
```bash
Rscript bootstrappingResultsAnalysis.R <input_folder> <output_file> [--true_label_col=<column>] [--predicted_label_col=<column>] [--positive_label=<value>] [--prob_col=<column>] [--summary_file=<path>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `input_folder` | `str` (positional) | Yes | Folder containing the bootstrap CSV files. Every `.csv` file in it is processed |
| `output_file` | `str` (positional) | Yes | Path to the CSV where the per-file metrics are saved |
| `--true_label_col` | `str` | No | Column with the true labels (default: `labels`) |
| `--predicted_label_col` | `str` | No | Column with the predicted labels (default: `predicted_label`) |
| `--positive_label` | `str` | No | Value of the positive class (default: `1`) |
| `--prob_col` | `str` | No | Column with the predicted probability of the positive class, used for AUC-ROC (default: `prob_1`) |
| `--summary_file` | `str` | No | Path to save the mean/sd summary CSV. If omitted, no summary is written |

**Input example**

```bash
Rscript bootstrappingResultsAnalysis.R bootstrap_results/ bootstrap_metrics.csv --summary_file=bootstrap_summary.csv
```

_bootstrap\_results/bootstrap\_1.csv_

| text | labels | predicted_label | prob_0 | prob_1 |
|---|---|---|---|---|
|In vitro experiments identified [TARGET][GENE][/TARGET] as a potential stemness target gene, which could enhance the stemness and chondrogenesis of OBMSCs.|1|1|0.08|0.92|
|...|...|...|...|...|

**Output example**

_bootstrap\_metrics.csv_

| file_name | f1 | accuracy | auc_roc | precision | recall |
|---|---|---|---|---|---|
|bootstrap_1.csv|0.81|0.84|0.90|0.79|0.83|
|bootstrap_2.csv|0.79|0.83|0.89|0.77|0.82|
|bootstrap_3.csv|0.82|0.85|0.91|0.80|0.84|

_bootstrap\_summary.csv_

| f1_mean | f1_sd | accuracy_mean | accuracy_sd | auc_roc_mean | auc_roc_sd | precision_mean | precision_sd | recall_mean | recall_sd |
|---|---|---|---|---|---|---|---|---|---|
|0.81|0.015|0.84|0.010|0.90|0.010|0.79|0.015|0.83|0.010|

---

### `fallbackNormaliseMygene.py`

**Description**

Takes the gene mentions that GNorm2 could not normalise (their ID is the "no ID" symbol, `-` by default) and queries [MyGene.info](https://mygene.info/) with their name (as symbol, name or alias, human only) to recover an Entrez ID. When a name returns several matches, the one with the highest score is kept. The recovered IDs are written to a new column in a copy of the input file. Mentions that are still not found get the "no ID" symbol, so they stay consistent with GNorm2.

Queries are sent in batches of 500 unique names, with a pause between batches and retries (splitting the batch in half) if a request fails.

**Usage**
```bash
python fallbackNormaliseMygene.py <input> <output> [-columnGeneName <column>] [-columnGeneIDGnorm <column>] [-columnMyGeneID <column>] [-symbolNoIDGNorm <symbol>] [-inter <folder>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `input` | `str` (positional) | Yes | CSV with the gene mentions |
| `output` | `str` (positional) | Yes | Path to save the input file with the extra MyGene.info ID column |
| `-columnGeneName` | `str` | No | Column with the gene name as it appears in the text (default: `gene`) |
| `-columnGeneIDGnorm` | `str` | No | Column with the Entrez ID from GNorm2 (default: `id`) |
| `-columnMyGeneID` | `str` | No | Name of the new column where the MyGene.info ID is stored. It must not already exist in the input (default: `id_myGene`) |
| `-symbolNoIDGNorm` | `str` | No | Symbol GNorm2 uses for a gene without ID. It must appear at least once in `-columnGeneIDGnorm` (default: `-`) |
| `-inter` | `str` | No | Existing folder where the name-to-ID table returned by MyGene.info is saved as `mergedDataframe.csv` |

**Input example**

```bash
python fallbackNormaliseMygene.py predictionsWithMetadata.csv predictionsWithMetadata_mygene.csv -inter intermediate/
```

_predictionsWithMetadata.csv_

| pmid | number | gene | id | uniprotid | sa | predicted_label | ... |
|---|---|---|---|---|---|---|---|
|39764517|7|SPI1|6688|P17947|9606|1|...|
|...|...|Sox9|20682|Q04887|10090|1|...|
|...|...|collagen type II alpha 1|-|-|-|0|...|
|...|...|BMSC-factor|-|-|-|0|...|

**Output example**

_predictionsWithMetadata\_mygene.csv_

| pmid | number | gene | id | uniprotid | sa | predicted_label | [...] | id_myGene |
|---|---|---|---|---|---|---|---|---|
|39764517|7|SPI1|6688|P17947|9606|1|...|-|
|...|...|Sox9|20682|Q04887|10090|1|...|-|
|...|...|collagen type II alpha 1|-|-|-|0|...|1280|
|...|...|BMSC-factor|-|-|-|0|...|-|

_intermediate/mergedDataframe.csv_

| gene | id_myGene |
|---|---|
|collagen type II alpha 1|1280|
|BMSC-factor|-|

------------------

### `harmoniseHumanGeneIDs.py`

**Description**

Keeps only human genes and combines the two candidate IDs of each row (the "main" ID from GNorm2 and the "secondary" ID from MyGene.info) into a single final ID column. The steps are:

1. Remove rows where neither the main nor the secondary ID is present.
2. Keep only human rows: either the main ID is present and the species column is `9606` (*Homo sapiens*), or the main ID is missing and the secondary ID is present (MyGene.info was queried for human genes only).
3. Create the final ID column: the main ID when present, otherwise the secondary ID.
4. If `-filter` is given, remove rows whose final ID appears in the filter file (e.g. genes that were already manually labelled).
5. Remove duplicated (final ID, label) pairs and save the result.

The output is the `final_csv`/`predictions_csv` used by the coverage scripts.

**Usage**
```bash
python harmoniseHumanGeneIDs.py <input> <output> -columnLabel <column> -finalIdcolumn <column> [-symbolNotID <symbol>] [-filter <file>] [-columnFilterSpecie <column>] [-columnMainID <column>] [-columnSecondnID <column>] [-inter <folder>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `input` | `str` (positional) | Yes | CSV to process (output of `fallbackNormaliseMygene.py`) |
| `output` | `str` (positional) | Yes | Path to save the processed CSV |
| `-columnLabel` | `str` | Yes | Column with the label, predicted or annotated (e.g. `predicted_label`) |
| `-finalIdcolumn` | `str` | Yes | Name of the new column with the final ID (e.g. `id_human`). It must not already exist in the input |
| `-symbolNotID` | `str` | No | Symbol that marks a missing ID (default: `-`) |
| `-filter` | `str` | No | CSV with genes to filter. It must have a column with the same name as `-finalIdcolumn`. Requires `-inter` |
| `-columnFilterSpecie` | `str` | No | Column with the species taxon ID (default: `sa`) |
| `-columnMainID` | `str` | No | Column with the main (GNorm2) Entrez ID (default: `id`) |
| `-columnSecondnID` | `str` | No | Column with the secondary (MyGene.info, human only) Entrez ID (default: `id_myGene`) |
| `-inter` | `str` | No | Folder where the intermediate CSVs of each step are saved. It is created if it doesn't exist |

**Input example**

```bash
python harmoniseHumanGeneIDs.py predictionsWithMetadata_mygene.csv filteredUniqueGeneClassificationLabel_humanGenes.csv -columnLabel predicted_label -finalIdcolumn id_human -filter manuallyLabelledGenes.csv -inter intermediate/
```

_predictionsWithMetadata\_mygene.csv_

| pmid | number | gene | id | uniprotid | sa | predicted_label | [...] | id_myGene |
|---|---|---|---|---|---|---|---|---|
|39764517|7|SPI1|6688|P17947|9606|1|...|-|
|...|...|Sox9|20682|Q04887|10090|1|...|-|
|...|...|collagen type II alpha 1|-|-|-|0|...|1280|
|...|...|BMSC-factor|-|-|-|0|...|-|

_manuallyLabelledGenes.csv_

| id_human | ... |
|---|---|
|6662|...|

**Output example**

_filteredUniqueGeneClassificationLabel\_humanGenes.csv_

| pmid | number | gene | id | uniprotid | sa | predicted_label | ... | id_myGene | id_human |
|---|---|---|---|---|---|---|---|---|---|
|39764517|7|SPI1|6688|P17947|9606|1|...|-|6688|
|[...]|[...]|collagen type II alpha 1|-|-|-|0|...|1280|1280|

Intermediate files written to `intermediate/`:

| File | Content |
|---|---|
| `only_genes_withSomeID.csv` | Rows with at least one ID (step 1) |
| `genesWithMinOneHumanID.csv` | Rows with a human ID (step 2) |
| `genes_withSomeHumanID_filtered.csv` | Human rows after the filter file, before removing duplicates (only with `-filter`) |
| `genes_withSomeHumanID_unified.csv` | Human rows with the final ID, before removing duplicates (only without `-filter`) |

------------------

### `coverageAnalysisGOSingleTerm.R`

**Description**

Given one GO term (by its code in the ontology), measures the amount of genes predicted as regulators by the model (`predicted_label == 1`) that are annotated in that term, how many have not and how many have been classified as regulators but are not in that term. Coverage is computed twice: for the term together with all its descendants (`GOALL`), and for the term alone (`GO`).

Besides the coverage, the script also saves:

* Venn diagrams (SVG) of model regulators vs. GO term genes, with and without descendants
* The offspring and direct children of the GO term
* Genes predicted as regulators that are not annotated to the term ("regulator candidate"), ranked by how many sentences classified them as regulators
* GO genes the model did not capture, split into genes present in the dataset but predicted as non-regulators, and genes absent from the dataset, together with the GO terms (within the analysed term's hierarchy) that each group is annotated to
* Optionally, the "regulator candidates" that are annotated to a broader (parent/ancestor) GO term, when `--parent_go_term` is given

All output file names include the GO term name (spaces replaced by `_`), so several terms can be written to the same folder.

**Usage**
```bash
Rscript coverageAnalysisGOSingleTerm.R <go_term> <output_dir> <final_csv> <full_csv> [--parent_go_term=<GO ID>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `go_term` | `str` (positional) | Yes | GO ID to analyse, e.g. `GO:0002062` |
| `output_dir` | `str` (positional) | Yes | Folder where all outputs are written. It is created if it doesn't exist |
| `final_csv` | `str` (positional) | Yes | CSV with one row per gene and predicted label (output of `harmoniseHumanGeneIDs.py`). Needs the columns `id_human` (Entrez ID) and `predicted_label` |
| `full_csv` | `str` (positional) | Yes | CSV with every classified gene mention, before removing duplicates or filtered. Needs the columns `id_human` and `predicted_label`. Used to count how many sentences classified each gene as a regulator |
| `--parent_go_term` | `str` | No | Ancestor GO ID (e.g. `GO:0051216`) used to find the possible regulators not in the go_term but that are annotated to the broader term |

**Input example**

```bash
Rscript coverageAnalysisGOSingleTerm.R GO:0002062 results/chondrocyte_differentiation \
  filteredUniqueGeneClassificationLabel_humanGenes.csv \
  fullGeneMentionClassification_humanGenes.csv \
  --parent_go_term=GO:0051216
```

_filteredUniqueGeneClassificationLabel\_humanGenes.csv_

| pmid | number | sentence | indexStart | indexEnd | start_masked | end_masked | gene | id | uniprotid | sa | text | predicted_label | prob_0 | prob_1 | id_myGene| id_human |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|15975973|2|OBJECTIVE: To investigate effects of cartilage derived morphogenetic protein-1 and -2 (CDMP-1, CDMP-2), [...]|88|93|46|69|CDMP-1|8200|P43026|9606|OBJECTIVE: To investigate effects of [GENE] ([TARGET][GENE][/TARGET], [GENE]), [...]|0|0.99928516|0.0007148563|-|8200|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

`fullGeneMentionClassification_humanGenes.csv` has the same structure, but keeps every mention, so the same gene can appear several times meanwhile the one that is final file will have only a unique combination gene-label classification

**Output example**

For `GO:0002062` (chondrocyte differentiation) the following files are written to `results/chondrocyte_differentiation/`:

| File | Content |
|---|---|
| `information_coverage_chondrocyte_differentiation_andOffspring.txt` | Coverage summary for the term and its descendants |
| `information_coverage_chondrocyte_differentiation.txt` | Coverage summary for the term only |
| `go_terms_offspring_chondrocyte_differentiation.csv` | The term and all its descendants (`GOID`, `TERM`) |
| `go_terms_children_chondrocyte_differentiation.csv` | The term and its direct children (`GOID`, `TERM`) |
| `venn_chondrocyte_differentiation_GOoffspring.svg` | Venn diagram, model regulators vs. term + descendants |
| `venn_chondrocyte_differentiation_GOmainOnly.svg` | Venn diagram, model regulators vs. term only |
| `frequency_classification_regulators_allNormalisedgenes_chondrocyte_differentiation.csv` | Number of sentences in which each gene was predicted as a regulator |
| `frequency_classification_regulators_genes_not_in_chondrocyte_differentiation_andOffspring.csv` | Novel candidates (regulators not in the term), sorted by sentence count |
| `genes_not_captured_model_chondrocyte_differentiation_andOffspring.csv` | GO genes not predicted as regulators (`ENTREZID`, `SYMBOL`, `GENENAME`) |
| `genes_not_captured_model_full_info_chondrocyte_differentiation_andOffspring.csv` | Same genes, with all their GO annotations (one row per gene-GO pair) |
| `not_caught_genes_but_in_dataset_as_NONregulators_chondrocyte_differentiation.csv` | GO genes present in the dataset but predicted as non-regulators |
| `not_caught_genes_not_in_dataset_chondrocyte_differentiation.csv` | GO genes absent from the dataset |
| `not_caught_genes_but_in_dataset_as_NONregulators_GOTerms_chondrocyte_differentiation.csv` | GO terms within the term's hierarchy annotated to the non-regulator genes |
| `not_caught_genes_not_in_dataset_GOTerms_chondrocyte_differentiation.csv` | GO terms within the term's hierarchy annotated to the absent genes |
| `not_caught_genes_but_in_dataset_as_NONregulators_GOTerms_count_chondrocyte_differentiation.csv` | Number of non-regulator genes per GO term |
| `not_caught_genes_not_in_dataset_GOTerms_count_chondrocyte_differentiation.csv` | Number of absent genes per GO term |
| `information_coverage_cartilage_development.txt` | Only with `--parent_go_term`: novel candidates found in the parent term |
| `drivers_in_cartilage development_not_in_chondrocyte_differentiation.csv` | Only with `--parent_go_term`: those novel candidates, with their Entrez ID and symbol |

_information\_coverage\_chondrocyte\_differentiation\_andOffspring.txt_

```text
Information GO:0002062 (chondrocyte differentiation) and descendants
Total GO genes: 119
Retrieved by model: 94
Not retrieved: 25
Coverage: 78.991597
Genes that are not in GO: 1034
```

_frequency\_classification\_regulators\_genes\_not\_in\_chondrocyte\_differentiation\_andOffspring.csv_

| ENTREZID | SYMBOL | sentence_count |
|---|---|---|
|6688|SPI1|12|
|...|...|...|

------------------

### `coverageAllGOHumanTerms.R`

**Description**

Runs the same coverage calculation as `coverageAnalysisGOSingleTerm.R` (term and descendants), but for every GO Biological Process term that has at least one human gene annotated to it. This shows which biological processes are well covered by the model's regulators and which are not.

There are too many GO terms to process in a single run, so the script works on a batch of rows (`init_batch` to `fin_batch`) of the human BP term table. Each batch writes its own CSV, and the batch CSVs can be combined afterwards. The total number of human BP terms is printed at the start of each run, and `fin_batch` is capped at that number.

**Usage**
```bash
Rscript coverageAllGOHumanTerms.R <init_batch> <fin_batch> <predictions_csv> <output_dir>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `init_batch` | `int` (positional) | Yes | First row of the human BP term table to process (>= 1) |
| `fin_batch` | `int` (positional) | Yes | Last row to process (>= `init_batch`) |
| `predictions_csv` | `str` (positional) | Yes | CSV with the model predictions (output of `harmoniseHumanGeneIDs.py`). Needs the columns `id_human` (Entrez ID) and `predicted_label` |
| `output_dir` | `str` (positional) | Yes | Existing folder where the coverage CSV is written |

**Input example**

```bash
Rscript coverageAllGOHumanTerms.R 16 17 filteredUniqueGeneClassificationLabel_humanGenes.csv results/
```

_filteredUniqueGeneClassificationLabel\_humanGenes.csv_

_filteredUniqueGeneClassificationLabel\_humanGenes.csv_

| pmid | number | sentence | indexStart | indexEnd | start_masked | end_masked | gene | id | uniprotid | sa | text | predicted_label | prob_0 | prob_1 | id_myGene| id_human |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|15975973|2|OBJECTIVE: To investigate effects of cartilage derived morphogenetic protein-1 and -2 (CDMP-1, CDMP-2), [...]|88|93|46|69|CDMP-1|8200|P43026|9606|OBJECTIVE: To investigate effects of [GENE] ([TARGET][GENE][/TARGET], [GENE]), [...]|0|0.99928516|0.0007148563|-|8200|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

**Output example**

_results/coverage\_allGO\_terms\_human\_1\_1000.csv_

| GOID | TotalGenesGOTerm | GOGenesRetrievedByModel | GOGenesNotRetrievedByModel | CoverageGOTerm | GenesModelNotInGO | Term |
|---|---|---|---|---|---|---|
|GO:0000054|13|0|13|0|1128|ribosomal subunit export from nucleus|
|GO:0000055|7|0|8|0|1128|ribosomal large subunit export from nucleus|

------------------

### `gnorm2ToGeneMentions.py`

**Description**

Converts the sentence-level CSV produced by `fusionAllEntitiesAndUniprotID.py` (one row per sentence, with lists of genes and their metadata) into a gene-mention table with one row per gene.

**Usage**
```bash
python gnorm2ToGeneMentions.py -input <sentence-level CSV> -output <path to save gene mentions>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes | Sentence-level CSV. Needs the columns `pmid`, `number`, `text`, `gene`, `start`, `end`, `id`, `uniprotid`, `sa` |
| `-output` | `str` | Yes | Path to save the gene-mention CSV |

**Input example**

```bash
python gnorm2ToGeneMentions.py -input short-sentences-filtered.csv -output short-sentences-mergingFormat.csv
```

_short-sentences-filtered.csv_
|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|41465285|7|Significant temporal alterations in Bmp2, Bmp4, and other key genes were observed, disrupting chondrocyte differentiation.|['Bmp2', 'Bmp4']|['38', '44']|['42', '48']|['650', '652']|['P12643', 'P12644']|['9606', '9606']|
|...|...|...|...|...|...|...|...|...|


**Output example**

_short-sentences-mergingFormat.csv_
|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|41465285|7|Significant temporal alterations in Bmp2, Bmp4, and other key genes were observed, disrupting chondrocyte differentiation.|Bmp2|37|40|650|P12643|9606|
|...|...|...|...|...|...|...|...|...|


------------------

### `mergePredictionsWithGeneMetadata.py`

**Description**

Joins the model predictions (or annotated labels) with the gene-mention metadata from `gnorm2ToGeneMentions.py` (original gene text, Entrez ID, UniProt ID, species, etc.).

Both merges are inner joins, so only mentions that have both a prediction and metadata are kept. Columns with the same name in several files get a suffix (`_inter`, `_metadata`, `_inter_metadata`, `_labels`).

**Usage**
```bash
python mergePredictionsWithGeneMetadata.py -metadata <gene-mention CSV> -interFile <masked sentences with original indexes> -labels <predictions CSV> -output <path to save merged CSV> [-interFolder <folder>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-metadata` | `str` | Yes | CSV with the gene metadata (output of `gnorm2ToGeneMentions.py`), with 1-based indexes. Needs the columns `pmid`, `number`, `start`, `end` |
| `-interFile` | `str` | Yes | CSV with the masked sentences and the original gene indexes (intermidiate file comming from output of `appToNLPFormatting.py`). Needs the columns `pmid`, `number`, `indexStart`, `indexEnd`, `text` |
| `-labels` | `str` | Yes | CSV with the predicted (and probabilities) or annotated labels (output of `finetunnedModelClassification.py`). Needs the columns `pmid`, `number`, `text`, and must not have `start` or `end` columns |
| `-output` | `str` | Yes | Path to save the merged CSV |
| `-interFolder` | `str` | No | Folder where the intermediate merges are saved (`interFile_withCalculated_masked_indexes.csv`, `metadata_interFile_merged.csv`). It is created if it doesn't exist |

**Input example**

```bash
python mergePredictionsWithGeneMetadata.py -metadata short-sentences-mergingFormat.csv -interFile .\interFolderConvertingApptoNLP\masked_sentences_middle_iter0.csv -labels short-sentences-predictions.csv -interFolder interFolderMergingFiles -output short-sentences-labels-metadata-merged.csv
```

_short-sentences-mergingFormat.csv_
|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|41465285|7|Significant temporal alterations in Bmp2, Bmp4, and other key genes were observed, disrupting chondrocyte differentiation.|Bmp2|37|40|650|P12643|9606|
|...|...|...|...|...|...|...|...|...|

_masked\_sentences\_middle\_iter0.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|gene_indexes|text|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|41452756|1|Optogenetic activation of TGFb signaling drives ligand-free chondrogenesis in hESC-derived MSCs.|27|30|27|30|NA|NA|NA|NA|NA|NA|NA|False|[(27, 30)]|Optogenetic activation of [TARGET][GENE][/TARGET] signaling drives ligand-free chondrogenesis in hESC-derived MSCs.|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

_short-sentences-predictions.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|
|---|---|---|---|---|---|---|---|---|
|41452756|1|Optogenetic activation of [TARGET][GENE][/TARGET] signaling drives ligand-free chondrogenesis in hESC-derived MSCs.|1|-0.073754504|0.14078769|1|0.4465692|0.55343074|
|...|...|...|...|...|...|...|...|...|

**Output example**

_short-sentences-labels-metadata-merged.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|gene_indexes|text_inter|start_masked|end_masked|text_metadata|gene|start_inter_metadata|end_inter_metadata|id|uniprotid|sa|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|start_labels|end_labels|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|41452756|1|Optogenetic activation of TGFb signaling drives ligand-free chondrogenesis in hESC-derived MSCs.|27|30|27|30|NA|NA|NA|NA|NA|NA|NA|False|[(27, 30)]|Optogenetic activation of [TARGET][GENE][/TARGET] signaling drives ligand-free chondrogenesis in hESC-derived MSCs.|27|50|Optogenetic activation of TGFb signaling drives ligand-free chondrogenesis in hESC-derived MSCs.|TGFb|27|30|7040|P01137|9606|Optogenetic activation of [TARGET][GENE][/TARGET] signaling drives ligand-free chondrogenesis in hESC-derived MSCs.|1|-0.073754504|0.14078769|1|0.4465692|0.55343074|27|50|
|...|

------------------

### `labelClassificationGeneMentions.R`

**Description**

Counts, for each human gene (`id_human`), how many of its mentions the model classified with each predicted label. The result is a table with one row per gene and one `label_<value>` column per label (e.g. `label_0`, `label_1`), with `0` when a gene never received that label.

**Usage**
```bash
Rscript labelClassificationGeneMentions.R <input_csv> <output_csv>
```

Run `Rscript labelClassificationGeneMentions.R -h` to show the help.

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `input_csv` | `str` (positional) | Yes | CSV with every gene mention classified by the model, before removing duplicates (e.g. the `genes_withSomeHumanID_unified.csv` intermediate file of `harmoniseHumanGeneIDs.py`). Needs the columns `id_human` (Entrez ID) and `predicted_label` |
| `output_csv` | `str` (positional) | Yes | Path to save the per-gene label count table. Its folder must already exist |
| `-h`, `--help` | flag | No | Show the help message and exit |

**Input example**

```bash
Rscript labelClassificationGeneMentions.R genes_withSomeHumanID_unified.csv unique_ids_count_labels.csv
```

_genes\_withSomeHumanID\_unified.csv_

| pmid | number | sentence | indexStart | indexEnd | start_masked | end_masked | gene | id | uniprotid | sa | text | predicted_label | prob_0 | prob_1 | id_myGene| id_human |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|15975973|2|OBJECTIVE: To investigate effects of cartilage derived morphogenetic protein-1 and -2 (CDMP-1, CDMP-2), [...]|88|93|46|69|CDMP-1|8200|P43026|9606|OBJECTIVE: To investigate effects of [GENE] ([TARGET][GENE][/TARGET], [GENE]), [...]|0|0.99928516|0.0007148563|-|8200|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

**Output example**

_unique\_ids\_count\_labels.csv_ (the first, unnamed column is the row number)

| | id_human | label_0 | label_1 |
|---|---|---|---|
|1|12|8|5|
|2|15|1|0|
|3|19|1|0|
|...|...|...|...|

---
## Plot generation

The scripts in this section do not produce intermediate files for the rest of the pipeline. They take outputs of the scripts above and generate the figures (and summary statistics) used to report the results.

### `ORA_analysis.Rmd`

**Description**

R Markdown notebook, adapted from Mohammed Khalfan's clusterProfiler tutorial, that runs an over-representation analysis (ORA) of GO Biological Processes with [clusterProfiler](https://bioconductor.org/packages/release/bioc/vignettes/clusterProfiler/inst/doc/clusterProfiler.html). The genes are split into regulators (label `1`) and non-regulators (label `0`), and each group is tested separately for three gene sets:

* **Manually labelled genes** (training, test and held-out sets), using the annotated labels (`labels`)
* **Final predictions** of the model, using the predicted labels (`predicted_label`)
* **Filtered final predictions**, the same predictions after removing the manually labelled genes

The ORA uses `enrichGO` with human annotations (`org.Hs.eg.db`), Entrez IDs, `ont = "BP"`, `pvalueCutoff = 0.05`, `qvalueCutoff = 0.10` and Benjamini-Hochberg correction. No `universe` is given, so the enrichment is tested against all annotated human genes. The notebook also shows:

* Dotplots of the top 10 enriched terms for each set, and a publication version of the filtered-regulators dotplot that is saved as SVG
* A simplified version of the manually labelled regulators result (`simplify`, cutoff 0.7), where redundant GO terms are collapsed into the most representative one
* Result tables, upset plots, a barplot and the GO induced graph (`goplot`)

This is a notebook, not a command-line script, so it takes no arguments. Edit the paths below before running it.

**Configuration (edit before running)**

| Location | Description |
|---|---|
| `setup` chunk, `root.dir` | Folder that contains the input CSVs. All the input file names are read relative to it |
| "Prepare Input" chunk | Names of the three input CSVs (manually labelled, final predictions, filtered final predictions) |
| `ggsave(filename = ...)` | Path where the publication dotplot (`dotplot_ora_geneRatio.svg`) is saved |

**Usage**

Open it in RStudio and knit it (or run all chunks)

**Input example**

The three input CSVs are outputs of `harmoniseHumanGeneIDs.py`. They need the column `id_human` (Entrez ID), plus `labels` for the manually labelled file or `predicted_label` for the prediction files.

_finalSearch-dataset-metadata-labels-formatted\_withmygeneIDs\_unified\_filtered.csv_

| pmid | number | sentence | indexStart | indexEnd | start_masked | end_masked | gene | id | uniprotid | sa | text | predicted_label | prob_0 | prob_1 | id_myGene| id_human |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|15975973|2|OBJECTIVE: To investigate effects of cartilage derived morphogenetic protein-1 and -2 (CDMP-1, CDMP-2), [...]|88|93|46|69|CDMP-1|8200|P43026|9606|OBJECTIVE: To investigate effects of [GENE] ([TARGET][GENE][/TARGET], [GENE]), [...]|0|0.99928516|0.0007148563|-|8200|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

`finalSearch-dataset-metadata-labels-formatted_withmygeneIDs_unified.csv` has the same structure (before filtering out the manually labelled genes), and `training-test-held-out-metadata-labels-formatted_withmygeneIDs_unified.csv` has the annotated label in a `labels` column instead of `predicted_label`.

------------------

### `histogramFrequencyGenesRegulatorClassification.R`

**Description**

Plots the distribution of how many sentences classified each gene as a regulator (`sentence_count`), to show how often the model predicts the same gene as a regulator across the literature. It first prints a summary table with the number of genes, mean, standard deviation, median, IQR, 25th and 75th percentiles, minimum and maximum of `sentence_count`.

The plots are shown in the RStudio plots panel and are not saved to file. Export them from there, or wrap the one you need in `ggsave()`.

This is not a command-line script, so it takes no arguments. Edit the input path before running it.

**Configuration (edit before running)**

| Location | Description |
|---|---|
| `read.csv(...)` (line 9) | Path to the input CSV |

**Input example**

The input CSV has one row per gene with the number of sentences in which the model predicted it as a regulator. It is the same table `coverageAnalysisGOSingleTerm.R` writes as `frequency_classification_regulators_allNormalisedgenes_<term>.csv`. It needs the column `sentence_count`.

_frequency\_clasification\_regulators\_allNormalisedgenes.csv_

| id_human | sentence_count |
|---|---|
|12|5|
|25|1|
|87|2|
|90|13|
|...|...|

**Output example**

Summary statistics printed to the console:

```text
  n_genes     mean      sd median iqr q25 q75 min max
1    1128 6.559397 33.1367      2   3   1   4   1 829
```

And the four histograms described above in the plots panel.

------------------

### `modelALPerformanceAndDatasetCompositionPlot.R`

**Description**

Plots how the classifier improves over the active learning (AL) iterations, how the training dataset changes, and how AL compares with a random selection baseline. From the test predictions of each iteration it computes F1, AUC-ROC, precision and recall (positive class `1`).

The script builds five figures:

* **AL performance**: the four metrics on the test set for each iteration (Core, Iter 1 to Iter 6), with the Iter 6 model on the held-out dataset shown as crosses
* **Dataset composition**: for each iteration, a bar with the number of sentences and a stacked bar with the number of driver (label `1`) and non-driver (label `0`) genes, labelled with the percentage of drivers
* **Combined figure**: the two plots above stacked (3:1 height) with a shared legend
* **Random baseline comparison**: one panel per metric (a to d) with the AL performance and the mean of the random selection over 6 seeds, with its 95% confidence interval (t-distribution)
* **Driver proportion**: boxplots of the percentage of driver and non-driver genes in the training dataset of each random seed per iteration, with the AL dataset shown as crosses

The plots are shown in the RStudio plots panel and are not saved to file. Export them from there, or wrap the one you need in `ggsave()`. The colours were checked with the [Coblis colour blindness simulator](https://www.color-blindness.com/coblis-color-blindness-simulator).

This is not a command-line script, so it takes no arguments. Edit the file names below before running it.

**Configuration (edit before running)**

| Location | Description |
|---|---|
| `setwd(...)` ("AL results" section) | Folder that contains the input CSVs. All the input file names are read relative to it |
| `process_results_file(...)` calls ("AL results" section) | Test predictions of each iteration, and the name shown for it in the plots (`Core`, `Iter 1`, ..., `Iter 6`) |
| `iter6_held_out` ("AL results" section) | Predictions of the Iter 6 model on the held-out dataset instead of the validation one |
| `counts` ("barplot data counts" section) | Number of sentences and genes in the AL training dataset of each iteration |
| `seed_3` to `seed_30` ("adding random baseline" section) | Performance of the random selection baseline, one CSV per seed |
| `count_genes_random` ("boxplots for random baseline" section) | Number of driver and non-driver genes in the random selection training datasets |

**Input example**

_13\_testPredictions\_iter1.csv_ (one file per iteration: `30_testPredictions_iter2.csv`, `28_testPredictions_iter3.csv`, `5_testPredictions_iter4.csv`, `12_testPredictions_iter5.csv`, `9_testPredictions_iter6_ht.csv`, `7_testPredictions_iter7_own_ht.csv`). `held-out-dataset-resulst-iter6.csv` has the same structure. They need the columns `labels`, `predicted_label` and `prob_1`

| pmid | number | text | labels | logits_0 | logits_1 | predicted_label | prob_0 | prob_1 |
|---|---|---|---|---|---|---|---|---|
|271986|7|With the onset of chondrogenesis, [TARGET][GENE][/TARGET] was detected in the cartilage matrix on day 6 and persisted until the early stages of bone formation.|0|1.8670596|-1.3036739|0|0.959718|0.040282052|
|...|...|...|...|...|...|...|...|...|

_sentence\_gene\_number\_al\_loop.csv_. `gene` is the total number of genes (`driver` + `non-driver`)

| iteration | sentence | gene | driver | non-driver |
|---|---|---|---|---|
|Core|148|297|22|275|
|Iter 1|247|647|48|599|
|Iter 2|347|950|87|863|
|...|...|...|...|...|

_summary\_performances\_random\_seed\_3\_replicas.csv_ (one file per seed: 3, 6, 8, 11, 26 and 30). The replica number is taken from the file name in the `replica` column, where replica `0` is the Core dataset and replica `n` is Iter `n`

| replica | auc_roc | f1 | precision | recall |
|---|---|---|---|---|
|baseline_random_gene_unit/3_testPredictions_replica_0.csv|0.7029|0.0|0.0|0.0|
|baseline_random_gene_unit/3_testPredictions_replica_1.csv|0.7374|0.2786|0.5270|0.1893|
|...|...|...|...|...|

_baseline\_random\_gene\_composition\_trainingDataset.csv_

| replica | seed | driver | non_driver |
|---|---|---|---|
|0|3|80|530|
|0|6|83|521|
|0|8|63|579|
|...|...|...|...|

**Output example**

The five figures described above in the plots panel.
