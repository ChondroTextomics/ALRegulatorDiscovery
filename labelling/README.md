## Overview

This folder contains the resources for the manual curation and consensus revision of genes associated with chondrogenesis

Requirements for running this pipeline are provided in the `envs` folder.

**Pipeline stages:**

1. Transform files from the al_loop to the labelling app format
2. Label the file(s)
3. Fuse the labelled files for revision (consensus revision)
4. Label the disagreement entities
5. Produce the consensus labelled dataset

The files required to generate the inputs for both app.R can be found in this repository folder `al_loop`

The final output of this repository is a labelled dataset of the selected sentences done in `al_loop`

---
## Files

### `modelToLabellingFormatting.py`



**Usage**
```bash
python modelToLabellingFormatting.py -input <> -output <> -group -seed
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes |  |
| `-output` | `str` | Yes |  |
| `-group` | `str` | Yes |  |
| `-seed` | `str` | Yes |  |

**Input example**

```bash
python modelToLabellingFormatting.py -input sentencesToLabelShort.csv -output sentencesToLabelShort_appFormat.csv -group -seed 1
```

_sentencesToLabelShort.csv_

|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|['transforming growth factor-beta', 'fibroblast growth factor']|['24', '60']|['55', '84']|['7040', '-']|['P01137', '-']|['9606', '9606']|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|['somatomedin-C', 'insulin-like growth factor I', 'growth hormone']|['10', '24', '57']|['23', '52', '71']|['3479', '3479', '2688']|['P05019', 'P05019', 'P01241']|['9606', '9606', '9606']|


**Output example**

_sentencesToLabelShort\_appFormat.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|NA|NA|NA|NA|NA|NA|NA|NA|			
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|NA|NA|NA|NA|NA|NA|NA|NA|						
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|NA|NA|NA|NA|NA|NA|NA|NA|					
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|NA|			
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|NA|							

------------------

### labelling_shiny_app.R

**Usage**

Run the script with R and upload the labelling file

**Input Example**

_sentencesToLabelShort\_appFormat.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|NA|NA|NA|NA|NA|NA|NA|NA|			
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|NA|NA|NA|NA|NA|NA|NA|NA|						
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|NA|NA|NA|NA|NA|NA|NA|NA|					
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|NA|			
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|NA|	

**Output example**

_sentencesToLabelShort\_appFormat.csv_ (labelled)

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|

------------------

### `labellingToRevisionFormatting.py`

**Usage**

```bash
 python
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes |  |
| `-output` | `str` | Yes |  |
| `-group` | `str` | Yes |  |
| `-seed` | `str` | Yes |  |

**Input example**

```bash
python labellingToRevisionFormatting.py -files sentencesToLabelShort_appFormat_1.csv sentencesToLabelShort_appFormat_2.csv -curators Person1 Person2 -out sentencesToLabelShort_appFormat_revision.csv -group
```

_sentencesToLabelShort\_appFormat|_1.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|

_sentencesToLabelShort\_appFormat|_2.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|No|NA|NA|NA|NA|NA|NA|NA|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|Unclear|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|TRUE|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|Yes|NA|NA|Phenotypic|NA|NA|NA|NA|

**Output example**

_sentencesToLabelShort\_appFormat\_revision.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|Curator|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|Person1|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|No|								Person2
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|NA|Final
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58	23,52,71	11	23	No								Person1
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	25	52	No								Person1
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	58	71								TRUE	Person1
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	11	23	Unclear								Person2
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	25	52								TRUE	Person2
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	58	71	Yes			Phenotypic					Person2
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	11	23									Final
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	25	52									Final
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.	11,25,58	23,52,71	58	71									Final

------------------

### `revision_shiny_app.R`

**Usage**

Run the script with R and upload the revision labelling file

**Input example**

_sentencesToLabelShort\_appFormat\_revision.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|Curator|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|Person1|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|No|NA|NA|NA|NA|NA|NA|NA|Person2|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|NA|NA|NA|NA|NA|NA|NA|NA|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|No|NA|NA|NA|NA|NA|NA|NA|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|Unclear|NA|NA|NA|NA|NA|NA|NA|Person2|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|TRUE|Person2|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|Yes|NA|NA|Phenotypic|NA|NA|NA|NA|Person2|	
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|NA|NA|NA|NA|NA|NA|NA|NA|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|NA|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|NA|Final|

**Output example**

_sentencesToLabelShort\_appFormat\_revision.csv_ (labelled)

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|Curator|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|Person1|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|No|NA|NA|NA|NA|NA|NA|NA|Person2|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|No|NA|NA|NA|NA|NA|NA|NA|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|Unclear|NA|NA|NA|NA|NA|NA|NA|Person2|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|TRUE|Person2|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|Yes|NA|NA|Phenotypic|NA|NA|NA|NA|Person2|	
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|TRUE|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|Final|

------------------

### `fusingAgreementData.py`



**Usage**

```bash
python fusingAgreementData.py -fileCurator <path_file_labelled> -fileAgree <path_file_revision> -fileOut <path_output_file> -curatorAgree <name_agreement_curator> [-inter -namesFilesInt <name_file_1> <name_file_2>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-fileCurator` | `str` | Yes |  |
| `-fileAgree` | `str` | Yes |  |
| `-fileOut` | `str` | Yes |  |
| `-curatorAgree` | `str` | Yes |  |
| `-inter` | `str` | No |  |
| `-namesFilesInt` | `str` | No |  |

**Input Example**
```bash
python fusingAgreementData.py -fileCurator sentencesToLabelShort_appFormat_1.csv -fileAgree sentencesToLabelShort_appFormat_revision.csv -fileOut sentencesToLabelShort_labelled.csv -curatorAgree Final
```

_sentencesToLabelShort\_appFormat|_1.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|

_sentencesToLabelShort\_appFormat\_revision.csv_

|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|Curator|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|Person1|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|No|NA|NA|NA|NA|NA|NA|NA|Person2|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|No|NA|NA|NA|NA|NA|NA|NA|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|Person1|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|Unclear|NA|NA|NA|NA|NA|NA|NA|Person2|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|TRUE|Person2|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|Yes|NA|NA|Phenotypic|NA|NA|NA|NA|Person2|	
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|TRUE|Final|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|TRUE|Final|

**Output Example**

_sentencesToLabelShort\_labelled.csv_
|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|No|NA|NA|NA|NA|NA|NA|NA|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|True|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|True|

