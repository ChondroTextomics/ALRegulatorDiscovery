## Overview

This folder contains the scripts necessary to go from a PubMed-format query to a file of genes extracted from the matching text. The pipeline is fully re-usable: it depends only on a query and a file of process-specific filtering (concept) terms, so it can be repurposed for topics and gene-extraction tasks beyond the one described below by swapping in a different query and concept list.

As configured here, it retrieves and processes PubMed articles related to chondrogenesis to obtain sentences that contain gene(s) and a chondrogenesis-related concept term, producing a training dataset for classifying those genes into regulators or non-regulators of chondrogenesis.

**Pipeline stages:**

1. Retrieve PubMed article identifiers from predefined queries
2. Download article metadata and abstracts
3. Parse article content
4. Split articles into sentences
5. Convert sentences into PubTator format
6. Run GNorm2 to identify gene mentions, using two setup configurations (all identified genes, and genes restricted to those with a UniProt ID), then fuse both result sets into a single annotated dataset
7. Filter sentences containing:
   * At least one gene mentioned
   * At least one term from the defined concept list
8. Store the final filtered dataset for downstream NLP analysis

![Pipeline overview](pipeline-data-extraction.png)

The final output of this repository is a sentence-level dataset of samples containing recognised genes and topic-specific (concept-defined) terminology.

`comparisonResultsGNorm2.py` sits outside this main sequence — it's an optional validation utility for comparing intermediate GNorm2 outputs across separate runs (e.g. to sanity-check that two configurations produce consistent results where expected).

---
## Files

### `fetchQueryResults.py`

**Description**

Given a search query, retrieves the matching PMIDs from PubMed and downloads the corresponding article data (e.g. title, abstract) for each one.

If given a file containing PMIDs (one per line) it will extract the data and save it

**Usage**
```bash
python fetchQueryResults.py -out <path to save PMIDs> -mindate "<lower bound date>" -maxdate "<upper bound date>" -db <database name> -email <email address> -query "<query in PubMed format>" [-retrieve <path to save article data>]
```

To skip the search and retrieve data directly for a list of PMIDs you already have:

```bash
python fetchQueryResults.py -out <path to save PMIDs> -db <database name> -email <email address> -pmidfile <path to file with PMIDs> -retrieve <path to save article data>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-out` | `str` | Yes | File path to save the list of PMIDs obtained by the search (one PMID per line) |
| `-mindate` | `str` | Yes, unless -pmidfile is given | Lower bound date for the query, in format YYYY/MM/DD, YYYY/MM, or YYYY |
| `-maxdate` | `str` | Yes, unless -pmidfile is given | Upper bound date for the query, in format YYYY/MM/DD, YYYY/MM, or YYYY |
| `-db` | `str` | Yes | Database to search (see Entrez Direct guides for accepted values) |
| `-email` | `str` | Yes | Email address attached to the query, as required by NCBI Entrez |
| `-query` | `str` | Yes, unless -pmidfile is given | Search query, in PubMed query format |
| `-retrieve` | `str` | No, unless -pmidfile is given | Path to save the retrieved article data as XML. If omitted, only the PMID list is saved |
| `-pmidfile` | `str` | No | Path to an existing file with one PMID per line. |


**Input example**

Searching by query
```bash
python fetchQueryResults.py \
  -out pmids_query_short.txt \
  -mindate "2025/01/07" \
  -maxdate "2025/01/07" \
  -db pubmed \
  -email example@gmail.com \
  -query '((chondrogenesis OR chondrocyte differentiation) AND "English"[Language]) NOT "Review"[Publication Type]' \
  -retrieve info_papers_short.xml
```

Retrieving form an existing PMID file
```bash
python fetchQueryResults.py \
  -out pmids_from_file.txt \
  -db pubmed \
  -email example@gmail.com \
  -pmidfile my_pmids.txt \
  -retrieve info_papers_short.xml
```

**Output example**

_pmids\_query\_short.txt_
```txt
39764517
39764126
39762337
```
_info\_papers\_short.xml_

```xml
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Example article title</ArticleTitle>
        <Abstract>
          <AbstractText>Example abstract text...</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Smith</LastName>
            <ForeName>Jane</ForeName>
          </Author>
          <!-- ...additional <Author> entries -->
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <!-- ...additional <PubmedArticle> entries, one per PMID -->
```

------------------

### `pubmedXMLtoCSV.py`

**Description**

Extracts title, abstract, and PMID from PubMed XML exports into a CSV, filtering out non-article records.

**Usage**
```bash
python pubmedXMLtoCSV.py -input <path to file with article info> -out <path to save extracted data>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes | File path to the file in XML format with all the information of articles |
| `-out` | `str` | Yes | File path to save the extracted title and abstracts of the articles |


**Input example**

```bash
python pubmedXMLtoCSV.py -input info_papers_short.xml -out parsed_short.csv
```

_info\_papers\_short.xml_

```xml
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Example article title</ArticleTitle>
        <Abstract>
          <AbstractText>Example abstract text...</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Smith</LastName>
            <ForeName>Jane</ForeName>
          </Author>
          <!-- ...additional <Author> entries -->
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <!-- ...additional <PubmedArticle> entries, one per PMID -->
```

**Output example**

_parsed\_short.csv_
| pmid | title | abstract |
|---|---|---|
|39764517|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released [...]|
|39764126|Direct Scaffold-Coupled Electrical Stimulation of Chondrogenic Progenitor Cells through Graphene Foam Bioscaffolds to Control Mechanical Properties of Graphene Foam - Cell Composites.|Osteoarthritis, a major global cause of pain and disability, is driven by the irreversible degradation of hyaline cartilage in joints. [...]|

------------------

### `splitterArticleSentences.py`

**Description**

For each row of the input file (article) text is split and converted in their own row

**Usage**
```bash
python splitterArticleSentences.py -input <path to file with article title and abstract> -out <path to save sentences>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes | File path to the file with the articles title and abstract in one row per article |
| `-out` | `str` | Yes | File path to save the extracted sentences |

**Input example**

```bash
python splitterArticleSentences.py -input parsed_short.csv -out sentences_short.csv
```

_parsed\_short.csv_
| pmid | title | abstract |
|---|---|---|
|39764517|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released [...]|
|39764126|Direct Scaffold-Coupled Electrical Stimulation of Chondrogenic Progenitor Cells through Graphene Foam Bioscaffolds to Control Mechanical Properties of Graphene Foam - Cell Composites.|Osteoarthritis, a major global cause of pain and disability, is driven by the irreversible degradation of hyaline cartilage in joints. [...]|

**Output example**

_sentences\_short.csv_

| pmid | sentence |
|---|---|
|39764517|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.|
|39764517|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.|
|39764126|Although electrical stimulation has been shown to enhance chondrogenesis and extracellular matrix production in 2D cultures, the mechanisms underlying these effects remain poorly understood, particularly in 3D models.|

------------------

### `pubtatorFormatter.py`

**Description**

Converts sentences and abstracts into PubTator format, the input format required by GNorm2 for gene/species normalization. Supports both sentence-level and abstract-level inputs, producing structured PubTator files ready to feed directly into the GNorm2 pipeline.

**Usage**
```bash
python pubtatorFormatter.py -input <path to file with sentences> -out <path to output file> -structure {sentence|abstract} 
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes | File path to the file with the sentences (one per row) |
| `-out` | `str` | Yes | File path to save the formatted sentences |
| `-structure` | `str` | Yes | given structure of the file, for formatting purposes |

**Input example**

```bash
python pubtatorFormatter.py -input sentences_short.csv -out sentences_formatted_short.pubtator -structure sentence
```

_sentences\_short.csv_

| pmid | sentence |
|---|---|
|39764517|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.|
|39764517|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.|
|39764126|Although electrical stimulation has been shown to enhance chondrogenesis and extracellular matrix production in 2D cultures, the mechanisms underlying these effects remain poorly understood, particularly in 3D models.|

**Output example**

_sentences\_formatted\_short.pubtator_

```text
39764517_1|t|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.
39764517_1|a|-

39764517_2|t|-
39764517_2|a|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released from the bone medullary cavity and differentiated into cartilage via microfracture surgery is a frequently employed technique for treating articular cartilage injuries, yet the treatment presents a main drawback of poor cartilage regeneration in the elderly.

39764517_3|t|-
39764517_3|a|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.
```

------------------

### `gnormSingularityExecution.sh`

Shell script that runs GNorm2 gene/species normalization inside a Singularity container for a given PubTator file. Sets up the required directory structure, stages the input PubTator file and setup config, then executes GNorm2 by piping [`gnorm_execution_singularity.sh`](#gnorm_execution_singularitysh) into the container via `singularity exec ... /bin/bash < gnorm_execution_singularity.sh`.

This script is run directly in the shell and does **not** take command-line arguments — instead, edit the variables in the "Files and directories to change" block at the top of the script before submitting.

**Usage**

If not done previously turn gnorm2 docker into a singularity

```bash
singularity pull docker://nadarajan07/gnorm2-ncbi
```

That command should give you the file `gnorm2-ncbi_latest.sif` that will be used for this script

A setup file is also neccessary for this script to work and the script `gnorm_execution_singularity.sh` (included in this repository)

**Configuration (edit before running)**

| Variable | Description |
|---|---|
| `results_directory` | Path where all working directories (`tmp_SR`, `tmp_GNR`, `tmp_SA`, `tmp`, `input`, `output`) will be created |
| `input_pubtator_file` | Path to the PubTator-formatted input file (output of `pubtatorFormatter.py`) |
| `setup_path` / `setup_file` | Location of the GNorm2 setup config, copied in and renamed to `setup.GN.txt` |
| `gnorm_singularity_path` | Path to the GNorm2 `.sif` container image |
| `gnorm_script_path` | Path to [`gnormAppExecution.sh`](#gnormAppExecution.sh), the script run inside the container |

**Input example**

```bash
bash gnormSingularityExecution > run.log 2> run.er
```

_setupFile.txt_

```text
#===Annotation
#Attribution setting:
#FocusSpecies = Taxonomy ID
#	All: All species
#	9606: Human
#	4932: yeast
#	7227: Fly
#	10090: Mouse
#	10116: Rat
#	7955: Zebrafish
#	3702: Arabidopsis thaliana
#open: True
#close: False

[Focus Species]
	FocusSpecies = All
	FilterAntibody = True
[Dictionary & Model]
	DictionaryFolder = Dictionary
	GNRModel = Dictionary/GNR.Model
	SCModel = Dictionary/SimConcept.Model
	GeneIDMatch = False
	HomologeneID = False
[Modules]
	SpeciesRecognition = False
	GeneRecognition = False
	SpeciesAssignment = False
	GeneNormalization = True
[Others]
	Normalization2Protein = False
	ShowUnNormalizedMention = True
	tmpFolder = tmp
	DeleteTmp = False
```

_sentences\_formatted\_short.pubtator_

```text
39764517_1|t|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.
39764517_1|a|-

39764517_2|t|-
39764517_2|a|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released from the bone medullary cavity and differentiated into cartilage via microfracture surgery is a frequently employed technique for treating articular cartilage injuries, yet the treatment presents a main drawback of poor cartilage regeneration in the elderly.

39764517_3|t|-
39764517_3|a|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.
```

**Output example**

The script creates several working directories under `results_directory` (`tmp_SR`, `tmp_GNR`, `tmp_SA`, `tmp`, `input`, `output`) — these hold intermediate files used internally by GNorm2 during processing.

The final normalized result is written to the `output/` directory, as a file with **the same filename as the input PubTator file** (this is how GNorm2 names its output — it does not append a suffix or change the extension).

For an input file named `sentences_formatted_short.pubtator`, the result will be at:
```text
[results_directory]/output/sentences_formatted_short.pubtator
```

_sentences\_formatted\_short.pubtator_ (in `output/`)

```text
39764517_1|t|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.
39764517_1|a|-
39764517_1      0       4       SPI1    Gene    Focus:9606|6688-2346

39764517_3|t|-
39764517_3|a|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.

39764517_6|t|-
39764517_6|a|To investigate the role of BMSCs stemness in microfracture, we developed microfracture-mimic cartilage regeneration organoid models.

39764517_7|t|-
39764517_7|a|In vitro experiments identified SPI1 as a potential stemness target gene, which could enhance the stemness and chondrogenesis of OBMSCs.
39764517_7      34      38      SPI1    Gene    Focus:9606|6688-2346
```

------------------

### `gnormAppExecution.sh`

Helper script that runs *inside* the Singularity container, replacing the default GNorm2 execution script that ships with the container image. It exists because the container's built-in script does not run GNorm2 correctly out of the box; `gnormAppExecution.sh` corrects this so that gene/species normalization runs as expected.

This script is not intended to be run standalone or called directly — it is piped into the container by [`gnormSingularityExecution.sh`](#gnormsingularityexecutionsh) via:

```bash
singularity exec --bind ... $gnorm_singularity_path /bin/bash < $gnorm_script_path
```

**Usage**

This script is only ever executed as stdin input to `/bin/bash` inside the container, as part of `gnormSingularityExecution.sh`. See that script's documentation for usage.

------------------

### `comparisonResultsGNorm2.py`

Compares the intermediate (temporary) output files from two or more `gnormSingularityExecution.sh` runs. For example, results generated with different settings or entity configurations. For each of the three temporary result stages (`tmp_SR`, `tmp_GNR`, `tmp_SA`), it writes a comparison file listing only the pubtator entries where the outputs diverge between the given result folders.

**Usage**
```bash
python comparisonResultsGNorm2.py -folders <path to result folder 1> <path to result folder 2> [<path to result folder N> ...] -fileNameCompare <filename to compare across folders> -outputFolder <path to output folder>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-folders` | `str` (two or more) | Yes | Paths to two or more `gnormSingularityExecution.sh` result directories to compare |
| `-fileNameCompare` | `str` | Yes | Filename (matching across the given folders) whose temporary-stage outputs should be compared |
| `-outputFolder` | `str` | Yes | Directory where the comparison files will be written |

**Input example**

```bash
python comparisonResultsGNorm2.py -folders results_proteinID/ results_allEntities/ -fileNameCompare sentences_formatted_short.pubtator -outputFolder results_comparison
```

**Output example**

Running this produces one comparison file per temporary stage (`tmp_SR`, `tmp_GNR`, `tmp_SA`) inside `results_comparison`. If no differences are found for a given stage, the corresponding file is created empty; otherwise, it lists the sentences that differ between the compared folders.

_analysis\_tmp\_GNR.txt_ (1 difference found)

```text
-----------------------------------------
Analysis of tmp_GNR folders from GNorm2
-----------------------------------------

Number of same blocks: 35
Number of different blocks: 1

-----------------------------------------

DIFFERENT BLOCKS

1
39762337_12|t|-
39762337_12|a|Gene co-expression network analysis identified hub genes associated with mitochondrial function, including SDHA, SIRT1, and PGC1A, which showed reduced expression in microtia chondrocytes.
39762337_12	109	113	SDHA	Gene
39762337_12	126	131	PGC1A	Gene
39762337_12	115	120	SIRT1	Gene

39762337_12|t|-
39762337_12|a|Gene co-expression network analysis identified hub genes associated with mitochondrial function, including SDHA, SIRT1, and PGC1A, which showed reduced expression in microtia chondrocytes.
39762337_12	109	113	SDHA	Gene
39762337_12	115	120	SIRT1	Gene
39762337_12	126	131	PGC1A	Gene
```

_analysis\_tmp\_SR.txt_ (no differences found)

```text
-----------------------------------------
Analysis of tmp_SR folders from GNorm2
-----------------------------------------

Number of same blocks: 36
Number of different blocks: 0

-----------------------------------------
```

------------------

### `fusionAllEntitiesAndUniprotID.py`

Fuses the two GNorm2 result sets produced by `gnormSingularityExecution.sh` when the pipeline is run with different setup configurations: one capturing all identified genes (normalized and unnormalized), and one restricted to genes with a UniProt ID. For each sentence, combines the metadata identified by GNorm2 across both runs, producing both a CSV containing the sentence text and the identified metadata, and a PubTator file with the fused annotations.

**Usage**
```bash
python fusionAllEntitiesAndUniprotID.py -allEntitiesInput <PubTator file with unnormalized results> -uniprotIDInput <PubTator file with UniProt ID results> -format {sentence|abstract} -outFolder <path to output folder>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-allEntitiesInput` | `str` | Yes | Path to the PubTator file containing the all-entities (normalized and unnormalized) GNorm2 results |
| `-uniprotIDInput` | `str` | Yes | Path to the PubTator file containing the UniProt ID–restricted GNorm2 results |
| `-format` | `str` | Yes | Format of the text in the PubTator files (`sentence` or `abstract`) |
| `-outFolder` | `str` | Yes | Directory where the fused CSV and PubTator files will be stored |

**Input example**

```bash
python fusionAllEntitiesAndUniprotID.py -allEntitiesInput results_allEntities/output/sentences_formatted_short.pubtator -uniprotIDInput results_proteinID/output/sentences_formatted_short.pubtator -format sentence -outFolder sentence_genes_fused
```

_sentences\_formatted\_short.pubtator_ (results_proteinID folder)

```text
39764517_1|t|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.
39764517_1|a|-
39764517_1	0	4	SPI1	Gene	6688(UniProt:P17947)

39764517_2|t|-
39764517_2|a|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released from the bone medullary cavity and differentiated into cartilage via microfracture surgery is a frequently employed technique for treating articular cartilage injuries, yet the treatment presents a main drawback of poor cartilage regeneration in the elderly.

39764517_3|t|-
39764517_3|a|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.

```

_sentences\_formatted\_short.pubtator_ (results_allEntities folder)

```text
39764517_1|t|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.
39764517_1|a|-
39764517_1	0	4	SPI1	Gene	Focus:9606|6688-2346

39764517_2|t|-
39764517_2|a|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released from the bone medullary cavity and differentiated into cartilage via microfracture surgery is a frequently employed technique for treating articular cartilage injuries, yet the treatment presents a main drawback of poor cartilage regeneration in the elderly.

39764517_3|t|-
39764517_3|a|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.

```

**Output example**

_genes-sentences-test.csv_

pmid | number |	text |	gene |	start |	end |	id |	uniprotid |	sa |
|---|---|---|---|---|---|---|---|---|
|39764517|1|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.|['SPI1']|['0']|['4']|['6688']|['P17947']|['9606']|
|39764517|2|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released from the bone medullary cavity and differentiated into cartilage via microfracture surgery is a frequently employed technique for treating articular cartilage injuries, yet the treatment presents a main drawback of poor cartilage regeneration in the elderly.|[]|[]|[]|[]|[]|[]|
|39764517|3|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.|[]|[]|[]|[]|[]|[]|

_output-both-analyses-test.pubtator_

```text
39764517_1|t|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.
id	start	end	text	type	sa-id	SA	ID	normalized_id	UniProt_ID
39764517_1	0	4	SPI1	Gene	Focus:9606|6688-2346	9606	6688	6688(UniProt:P17947)	P17947

39764517_2|a|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released from the bone medullary cavity and differentiated into cartilage via microfracture surgery is a frequently employed technique for treating articular cartilage injuries, yet the treatment presents a main drawback of poor cartilage regeneration in the elderly.
id	start	end	text	type	sa-id	SA	ID	normalized_id	UniProt_ID

39764517_3|a|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.
id	start	end	text	type	sa-id	SA	ID	normalized_id	UniProt_ID

```

------------------

### `filterSentencesGeneConcept.py`

Filters the CSV output produced by `fusionAllEntitiesAndUniprotID.py`, keeping only rows whose sentence contains at least one gene identified by GNorm2 **and** at least one term from a given list of concepts (one concept per line in a separate input file).

**Usage**

```bash
python filterSentencesGeneConcept.py -input <CSV file with sentences> -concepts <file with filtering concepts> -output <file store results>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes |  |
| `-concepts` | `str` | Yes |  |
| `-output` | `str` | Yes |  |

**Input example**

```bash
python filterSentencesGeneConcept.py -input sentence_genes_fused/genes-sentences-test.csv -concepts example_concepts.txt -output filtered_sentences.csv
```

_genes-sentences-test.csv_

pmid | number |	text |	gene |	start |	end |	id |	uniprotid |	sa |
|---|---|---|---|---|---|---|---|---|
|39764517|1|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.|['SPI1']|['0']|['4']|['6688']|['P17947']|['9606']|
|39764517|2|Bone marrow stimulation treatment by bone marrow stromal cells (BMSCs) released from the bone medullary cavity and differentiated into cartilage via microfracture surgery is a frequently employed technique for treating articular cartilage injuries, yet the treatment presents a main drawback of poor cartilage regeneration in the elderly.|[]|[]|[]|[]|[]|[]|
|39764517|3|Prior research indicated that aging could decrease the stemness capacity of BMSCs, thus we made a hypothesis that increasing old BMSCs (OBMSCs) stemness might improve the results of microfracture in the elderly.|[]|[]|[]|[]|[]|[]|

_example\_concepts.txt_

```text
chondrogenesis
development
regeneration
cartilage
```

**Output example**

_filtered\_sentences.csv_

pmid | number |	text |	gene |	start |	end |	id |	uniprotid |	sa |
|---|---|---|---|---|---|---|---|---|
|39764517|1|SPI1 facilitates microfracture-mediated cartilage regeneration in the elderly by enhancing bone marrow stromal cells ctemness.|['SPI1']|['0']|['4']|['6688']|['P17947']|['9606']|
