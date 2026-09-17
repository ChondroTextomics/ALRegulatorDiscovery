## Overview

![AL Loop](ALLoop_figure.png)

This folder contains the resources required to do part of a loop in the active learning framework using a Hugging Face model. A whole loop is the combination of the pipeline in this folder and the one in `labelling`.

Requirements for running this pipeline are provided in the `envs` folder.

This folder takes as input the results of the folder `labelling`, and the output is the input of the same folder

Pipeline stages:
 1. Create the dataset that will be the training set for the Hugging Face model
 2. Train the model and provide the predictions of the validation dataset and pool (in batches if neccessary/wanted)
 3. Clustering of the pool samples
 4. Select the samples to label from the pool predictions

---
## Files

### `appToNLPFormatting.py`

**Usage**
```bash
python appToNLPFormatting.py <input_file> <output_file> [-columnAdd <name_column_add_file> -columnOriginal <column_text> -inter -iter <curent_iteration> -folderInter <path_folder_interFiles>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `file` | `str` | Yes | name of the file to transform |
| `out` | `str` | Yes | name of the file to save the transformed sentences |
| `-columnAdd` | `str` | No | column name to add (default `masked`) |
| `-columnOriginal` | `str` | No | column that is going to be read to change (default `sentence`) |
| `-inter` | `flag` | No | if activated, returns intermediate dataframes |
| `-iter` | `int` | No | if `-inter` is activated, marker (iteration number) used to name the intermediate files |
| `-folderInter` | `str` | No | if `-inter` is activated, folder to store the intermediate files |

**Input example**

```bash
python appToNLPFormatting sentencesToLabelShort_labelled.csv sentencesToLabelShort_labelled_nlpFormat.csv
```

_sentencesToLabelShort\_labelled.csv_
|pmid|number|sentence|allGenesIndexStart|allGenesIndexEnd|indexStart|indexEnd|label|association|experiment|proof|errorReported|errorMoreGenes|numberGenesTotal|NotGeneError|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|59|82|No|NA|NA|NA|NA|NA|NA|NA|
|1952598|2|Synergistic action of transforming growth factor-beta and fibroblast growth factor.|23,59|53,82|23|53|Yes|Focus|In vivo|Biomarkers+Phenotypic|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|11|23|No|NA|NA|NA|NA|NA|NA|NA|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|25|52|NA|NA|NA|NA|NA|NA|NA|True|
|2919122|1|Effect of somatomedin-C/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|11,25,58|23,52,71|58|71|NA|NA|NA|NA|NA|NA|NA|True|

**Output example**

_sentencesToLabelShort\_labelled\_nlpFormat.csv_
|pmid|number|masked|labels|
|---|---|---|---|
|1952598|2|Synergistic action of [GENE] and [TARGET][GENE][/TARGET].|0|
|1952598|2|Synergistic action of [TARGET][GENE][/TARGET] and [GENE].|1|
|2919122|1|Effect of [TARGET][GENE][/TARGET]/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|0|

------------------

### `batchingPoolDataset.py`

**Usage**
```bash
python batchingPoolDataset.py -input <path_pool_file> -batches <amount_final_batches> -out <folder_output_batches> -prefix <root_name_file_batches>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes | file to convert into batches |
| `-batches` | `int` | Yes | number of batches to split the file into |
| `-out` | `str` | Yes | folder where the batches will be saved (created if it doesn't exist) |
| `-prefix` | `str` | Yes | prefix of the file name, followed by the batch number and extension |

**Input example**

```bash
python batchingPoolDataset.py -input  pool_short_nlpFormat.csv -out pool_short_batches -batches 3 -prefix pool_short_batch
```

_pool\_short\_nlpFormat.csv_
|pmid|number|masked|labels|
|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|
|1955460|9|"Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|
|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|

**Output example**

_pool\_short\_batchs/pool\_short\_batch\_0.csv_

|pmid|number|masked|labels|
|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|
|1955460|9|Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|
|...|...|...|...|
|35494231|4|We show that high CAR score reflects plaque instability processes related to intra-plaque hemorrhage, angiogenesis, inflammation, and foam cell differentiation, whereas [TARGET][GENE][/TARGET] associates with neutrophil-mediated immunity, foam cell differentiation, cholesterol transport, and coagulation.|NA|

------------------

### `trainingModelTestPredictionBALDPool.py`

**Usage**
```bash
python trainingModelTestPredictionBALDPool.py -train <file_training_data> \
                                              -test <file_validation_data> \
                                              -pool <file_pool_data> \
                                              -out <folder_results> \
                                              -model <path_hf_model> \
                                              -tokenizer <path_hf_tokenizer> \
                                              -iterMC <iterationForMCdropout> \
                                              -epoch <epochs> \
                                              -iteration <current_iteration> \
                                              -batch <training_batch> \
                                              -lr <learning_rate> \
                                              -warmup <warmup_step_fraction> \
                                              -weightDecay <weight_decay> \
                                              -weightLossFunction <loss_function> \
                                              [-seed <random_seed>]

```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-train` | `str` | Yes | path to the training dataset (must contain `text` and `labels` columns) |
| `-test` | `str` | Yes | path to the test/validation dataset (must contain `text` and `labels` columns) |
| `-pool` | `str` | Yes | path to the pool dataset of unlabelled samples (must contain `text` and `labels` columns) |
| `-out` | `str` | Yes | directory that will hold all of the outputs (model, test predictions, pool predictions, ...) |
| `-model` | `str` | Yes | path to the model folder |
| `-tokenizer` | `str` | Yes | path to the tokenizer folder |
| `-iterMC` | `int` | Yes | number of MC dropout iterations to do |
| `-epoch` | `int` | No | number of epochs to train for (default `2`) |
| `-iteration` | `int` | Yes | loop iteration number, used for labelling the results |
| `-batch` | `int` | Yes | number of samples per batch during training |
| `-lr` | `float` | Yes | learning rate during training |
| `-warmup` | `float` | Yes | ratio of steps used as warmup (fraction in `[0, 1]`) |
| `-weightDecay` | `float` | Yes | weight decay applied during training |
| `-weightLossFunction` | `str` | Yes | whether to use a balanced weighted loss function during training (`True`/`False`, case-insensitive) |
| `-seed` | `int` | No | random seed (default `26`) |

**Input Example**

```bash
python trainingModelTestPredictionBALDPool.py -train sentencesToLabelShort_labelled_nlpFormat.csv \
                                              -test validationDataset_short_nlpFormat.csv \
                                              -pool pool_short_nlpFormat.csv \
                                              -out ./results_loop \
                                              -seed 9 \
                                              -model /home/user/nlp_study/models/pubmedbert/model \
                                              -tokenizer /home/user/nlp_study/models/pubmedbert/tokenizer \
                                              -iteration 1 I am running a few minutes late; my previous meeting is running over.
                                              -epoch 1 \
                                              -iterMC 3 \
                                              -batch 8 \
                                              -lr 1e-4 \
                                              -warmup 0 \
                                              -weightDecay 0.001 \
                                              -weightLossFunction False
```

_sentencesToLabelShort\_labelled\_nlpFormat.csv_
|pmid|number|text|labels|
|---|---|---|---|
|1952598|2|Synergistic action of [GENE] and [TARGET][GENE][/TARGET].|0|
|1952598|2|Synergistic action of [TARGET][GENE][/TARGET] and [GENE].|1|
|2919122|1|Effect of [TARGET][GENE][/TARGET]/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|0|

_validationDataset\_short\_nlpFormat.csv_

|pmid|number|text|labels|
|---|---|---|---|
|241677|12|Cells forming the regeneration blastema were [TARGET][GENE][/TARGET] reactive during the early formative phase, but with growth and development of the blastema into bulb and conic forms, these cells did not respond for this enzyme-activity.|0|
|271986|7|With the onset of chondrogenesis, [TARGET][GENE][/TARGET] was detected in the cartilage matrix on day 6 and persisted until the early stages of bone formation.|0|
|1314187|4|Synthesis of sulfated proteoglycans, an index of chondrogenesis, was inhibited by all three PDGF isoforms ([TARGET][GENE][/TARGET], [GENE], and [GENE]).|1|
|1314187|4,Synthesis of sulfated proteoglycans, an index of chondrogenesis, was inhibited by all three PDGF isoforms ([GENE], [TARGET][GENE][/TARGET], and [GENE]).|1|
|...|...|...|...|
|21971552|3|The aim of this study was to investigate, using a rotary cell culture system (RCCS) bioreactor, the effects of microgravity on the chondrogenic differentiation of human adipose-derived MSCs (ADSCs), which were cultured in pellets with or without the chondrogenic growth factor [TARGET][GENE][/TARGET].|1|


_pool\_short\_nlpFormat.csv_
|pmid|number|text|labels|
|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|
|1955460|9|"Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|
|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|

**Output Example**

In `results_loop` we will get the BALD scores for the pool file and the test predictions as well as the trained model weights that can be re-used later for predictions of other samples.

_9\_poolBALD\_iter1.csv_

|pmid|number|text|labels|BALD|
|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.",NA,0.0006594062
68959,6,"With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.",NA,6.443262e-05
1955460,9,"Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.",NA,0.0021454692
|...|...|...|...|...|
40015854,9,"Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.",NA,0.002461493

_9\_testPredictions\_iter1.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|
|---|---|---|---|---|---|---|---|---|
|241677|12|Cells forming the regeneration blastema were [TARGET][GENE][/TARGET] reactive during the early formative phase, but with growth and development of the blastema into bulb and conic forms, these cells did not respond for this enzyme-activity.|0|-0.058483087|-0.11627989|0|0.5144452|0.4855548|
|271986|7|With the onset of chondrogenesis, [TARGET][GENE][/TARGET] was detected in the cartilage matrix on day 6 and persisted until the early stages of bone formation.|0|0.06380151|-0.0754872|0|0.534766|0.46523404|
|1314187|4|Synthesis of sulfated proteoglycans, an index of chondrogenesis, was inhibited by all three PDGF isoforms ([TARGET][GENE][/TARGET], [GENE], and [GENE]).|1|-0.0077759195|-0.1261672|0|0.5295633|0.47043672|
|...|...|...|...|...|...|...|...|...|
|21971552|3|The aim of this study was to investigate, using a rotary cell culture system (RCCS) bioreactor, the effects of microgravity on the chondrogenic differentiation of human adipose-derived MSCs (ADSCs), which were cultured in pellets with or without the chondrogenic growth factor [TARGET][GENE][/TARGET].|1|-0.026207512|-0.317861|0|0.57240087|0.4275991|

------------------

### `finetunnedModelClassification.py`

**Usage**

```bash
python finetunnedModelClassification -batch <file_classify> \
                                     -model <path_finetuned_model> \
                                     -tokenizer <path_finetuned_tokenizer> \
                                     -batchNumber <number_file> \
                                     -prefix <prefix_result_output> \
                                     -out <folder_save_output>
                                     [-prefixEmbeddings <prefix_model_embeddings> \
                                     -onlyClassification]
                                     
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-batch` | `str` | Yes | name of the file to read and classify (must contain a `text` column) |
| `-model` | `str` | Yes | path to the fine-tuned model |
| `-tokenizer` | `str` | Yes | path to the tokenizer |
| `-batchNumber` | `int` | Yes | number of the batch being predicted, used for naming the output files |
| `-prefix` | `str` | Yes | prefix of the classification output file name, followed by the batch number and extension |
| `-prefixEmbeddings` | `str` | No, but necessary if -onlyClassification is not given | prefix of the CLS embeddings output file name, followed by the batch number and extension |
| `-out` | `str` | Yes | folder where the outputs will be saved (must already exist) |
| `-onlyClassification` | flag | No | if given, no CLS embedding file will be given, just the file with the classification|


**Input Example**

```bash
python poolFinetunnedModelClassification.py -batch pool_short_nlpFormat.csv -model results_loop/trained_model/ -tokenizer results_loop/trained_model/ -batchNumber 1 -prefix pool_short_classification -prefixEmbeddings pool_short_classification_embeddings -out results_pool_classification
```

_pool\_short\_nlpFormat.csv_
|pmid|number|text|labels|
|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|
|1955460|9|"Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|
|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|

**Output Example**

_results\_pool\_classification/pool\_short\_classification\_1.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|
|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|
|1955460|9|Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|0.08880645|-0.20694146|0|0.57340276|0.42659727|
|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|

_results\_pool\_classification/pool\_short\_classification\_embeddings\_1.csv_

|0|1|...|767|
|---|---|---|---|
|0.12525174|0.073949404|...|0.33107397|
|-0.07557922|0.1796895|...|-0.24311118|

------------------

### `cosineDistancesCalculate.py`

**Usage**
```bash
python cosineDistancesCalculate.py -embeddings <file_embeddings> \
                                   -matrixFolder <folder_cosine_batches> \
                                   -matrixPrefix <prefix_cosine_batches_files> \
                                   -batches <amount_batches> \
                                   -numberBatch <number_batch_to_process>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-embeddings` | `str` | Yes | file containing the embeddings |
| `-matrixFolder` | `str` | Yes | folder for the cosine distance batches (must already exist) |
| `-matrixPrefix` | `str` | Yes | prefix of each batch file name, followed by an underscore, the batch number and extension |
| `-batches` | `int` | Yes | number of batches the embeddings are going to be split into |
| `-numberBatch` | `int` | Yes | number of the batch being processed by this run (`0` if not splitting into batches) |

**Input example**

```bash
python cosineDistancesCalculate.py -embeddings results_pool_classification/pool_short_classification_embeddings_1.csv \
                                   -matrixFolder cosine_distances_pool_short \
                                   -matrixPrefix pool_short_classification_embeddings \
                                   -batches 1 \
                                   -numberBatch 1
```

_results\_pool\_classification/pool\_short\_classification\_embeddings\_1.csv_

|0|1|...|767|
|---|---|---|---|
|0.12525174|0.073949404|...|0.33107397|
|-0.07557922|0.1796895|...|-0.24311118|

**Output example**

The pool of embeddings is split into `-batches` chunks, and this run processes chunk `-numberBatch`, writing the cosine distances between that chunk's embeddings and the full embeddings set to `-matrixFolder`, as `<matrixPrefix>_<numberBatch>.csv`.

_cosine\_distances\_pool\_short/pool\_short\_classification\_embeddings_0.csv_

|0|1|2|...|193|
|---|---|---|---|---|
|0.0|0.10113166195376344|0.10608365968944822|...|0.12256780015419944|
|0.10113166195376344|4.440892098500626e-16|0.06806455175552883|...|0.10189725676225103
|...|...|...|...|...|

------------------

### `sampleBALDClassWeighthing.R`

**Usage**
```bash
Rscript sampleBALDClassWeighthing.R -i <input_file> -o <output_file> [-c <probability_column>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-i`, `--input` | `str` | Yes | path to the file with the prediction probability for samples |
| `-o`, `--output` | `str` | Yes | path to the file where the dataframe with the weights will be stored |
| `-c`, `--probabilityColumn` | `str` | No | name of the column that contains the probability that is going to define the weights, default `prob_1` |

**Input example**

```bash
Rscript sampleBALDClassWeighthing.R -i results_pool_classification/pool_short_classification_1.csv -o results_pool_classification/pool_short_classification_1_classWeights.csv -c prob_1
```

_results\_pool\_classification/pool\_short\_classification\_1.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|
|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|
|1955460|9|Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|0.08880645|-0.20694146|0|0.57340276|0.42659727|
|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|

**Output example**

The `prob_1` column (or the column passed with `-c`) is cut into `[0,0.1]`, `(0.1,0.2]`, ..., `(0.9,1]` bins, and each sample is given a weight equal to the inverse of the number of samples that fall in its bin, so that rare probability ranges are up-weighted.

_results\_pool\_classification/pool\_short\_classification\_1\_classWeights.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|prob_int|weights|
|---|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|(0.4,0.5]|0.00862068965517241|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|(0.4,0.5]|0.00862068965517241|
|1955460|9|Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|0.08880645|-0.20694146|0|0.57340276|0.42659727|(0.4,0.5]|0.00862068965517241|
|...|...|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|(0.3,0.4]|0.0204081632653061|

------------------

### `kMedoidsClustering.py`

**Usage**
```bash
python kMedoidsClustering.py -pool <path_pool_file> \
                             -embeddings <path_embeddings_file> \
                             -out <path_output_file> \
                             -k <amount_clusters> \
                             [-seed <random_seed>] \
                             [-cosineMatrix -matrixFolder <folder_cosine_batches> -matrixPrefix <prefix_cosine_batches_files> -batches <amount_batches>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-pool` | `str` | Yes | pool file in which columns with cluster label, medoid and outlier will be added |
| `-cosineDistances` | `str` | Yes | file containing the cosine distances between the samples |
| `-out` | `str` | Yes | file name to store the final results |
| `-k` | `int` | Yes | number of cluster to divide the samples (this will impct the sampling so it needs to be according to it) |
| `-seed` | `int` | No | random seed |

**Input example**

```bash
python kMedoidsClustering.py -pool results_pool_classification/pool_short_classification_1.csv \
                             -cosineDistances cosine_distances_pool_short/pool_short_classification_embeddings_0.csv \
                             -out results_pool_classification/pool_short_classification_1_clusters.csv \
                             -k 3 \
                             -seed 9
```

_results\_pool\_classification/pool\_short\_classification\_1.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|
|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|
|1955460|9|Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|0.08880645|-0.20694146|0|0.57340276|0.42659727|
|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|

_cosine\_distances\_pool\_short/pool\_short\_classification\_embeddings_0.csv_

|0|1|2|...|193|
|---|---|---|---|---|
|0.0|0.10113166195376344|0.10608365968944822|...|0.12256780015419944|
|0.10113166195376344|4.440892098500626e-16|0.06806455175552883|...|0.10189725676225103
|...|...|...|...|...|

**Output example**

The pool of samples is clustered into `-k` groups using k-medoids on the cosine distance between embeddings. For each cluster, the sample chosen as medoid (the most central/representative point) is flagged in the `medoid` column and the sample furthest from the medoid (the outlier) is flagged in the `outlier` column.

_results\_pool\_classification/pool\_short\_classification\_1\_clusters.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|cluster|medoid|outlier|
|---|---|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|0|False|True|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|1|False|False|
|1955460|9|Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|0.08880645|-0.20694146|0|0.57340276|0.42659727|1|False|False|
|...|...|...|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|1|False|False|

------------------

### `fusingParalelResults.py`

**Usage**
```bash
python fusingParalelResults.py -bald <file_bald_predictions> \
                               -label <file_label_predictions> \
                               -cluster <file_cluster_predictions> \
                               -out <path_output_file>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-bald` | `str` | Yes | file path with the bald predictions |
| `-label` | `str` | Yes | file path with label predictions (with weights if you want to include them) |
| `-cluster` | `str` | Yes | file path with cluster predictions |
| `-out` | `str` | Yes | name of the file where the results fused will be given |

**Input example**

```bash
python fusingParalelResults.py -bald results_loop/9_poolBALD_iter1.csv \
                               -label results_pool_classification/pool_short_classification_1_classWeights.csv \
                               -cluster results_pool_classification/pool_short_classification_1_clusters.csv \ 
                               -out results_loop/pool_short_classification_fusedResults.csv
```

_results\_loop/9\_poolBALD\_iter1.csv_

|pmid|number|text|labels|BALD|
|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|0.0006594062|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|6.443262e-05|
|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.002461493|

_results\_pool\_classification/pool\_short\_classification\_1\_classWeights.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|prob_int|weights|
|---|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|(0.4,0.5]|0.00862068965517241|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|(0.4,0.5]|0.00862068965517241|
|1955460|9|Similar studies with tarsal chondrocytes demonstrated a time- and dose-dependent response to CaCl2 with [TARGET][GENE][/TARGET] levels reaching a 4-fold and 15-fold increase over controls with 5 and 10 mM Ca2+, respectively, at 48 h. Elevated extracellular Ca2+ had no effect on cell proliferation.|NA|0.08880645|-0.20694146|0|0.57340276|0.42659727|(0.4,0.5]|0.00862068965517241|
|...|...|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|(0.3,0.4]|0.0204081632653061|

_results\_pool\_classification/pool\_short\_classification\_1\_clusters.csv_

|pmid|number|text|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|cluster|medoid|outlier|
|---|---|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|0|False|True|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|1|False|False|
|...|...|...|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|1|False|False|

**Output example**

The script checks that the three input files share the same `pmid`, `number`, `text` combinations, then inner-merges them on those keys: first `-bald` with `-label`, and then the result with `-cluster`. When a non-key column is present in more than one input file (e.g. `labels`, `logits_0`, `logits_1`, `predicted_label`, `prob_0`, `prob_1`), only one copy is kept in the output: for columns shared between `-bald` and `-label`, the `-label` value is kept (the `-bald` one is dropped); for columns shared between the `-bald`/`-label` merge and `-cluster`, the `-bald`/`-label` value is kept (the `-cluster` one is dropped).

_results\_loop/pool\_short\_classification\_fusedResults.csv_

|pmid|number|text|BALD|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|prob_int|weights|cluster|medoid|outlier|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|0.0006594062|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|(0.4,0.5]|0.00862068965517241|0|False|True|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|6.443262e-05|NA|-0.101926796|-0.14922045|0|0.5118212|0.48817876|(0.4,0.5]|0.00862068965517241|1|False|False|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|0.002461493|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|(0.3,0.4]|0.0204081632653061|1|False|False|

------------------

### `separatingCosineDistanceMatrix.sh`

**Usage**
```bash
bash separatingCosineDistanceMatrix.sh <input_file> <output_folder>
```

**Arguments**

| Argument | Position | Required | Description |
|---|---|---|---|
| `input_file` | `$1` | Yes | cosine distance matrix file; the first row is the header and every following row is one sample's distances |
| `output_folder` | `$2` | Yes | folder where each sample will be saved as its own file (created if it doesn't exist) |

**Input example**

```bash
bash separatingCosineDistanceMatrix.sh cosine_distances_pool_short/pool_short_classification_embeddings_0.csv cosine_distances_folder
```

_cosine\_distances\_pool\_short/pool\_short\_classification\_embeddings_0.csv_

|0|1|2|...|193|
|---|---|---|---|---|
|0.0|0.10113166195376344|0.10608365968944822|...|0.12256780015419944|
|0.10113166195376344|4.440892098500626e-16|0.06806455175552883|...|0.10189725676225103|
|...|...|...|...|...|

**Output example**

The script writes one file per data row (i.e. per sample) into `<output_folder>`, each containing the header row plus that sample's row, named `<sample_index>.csv` where `sample_index` is the 0-based position of the row among the data rows. If a sample's output file already exists it is left as is and that sample is skipped, so the script can be re-run to pick up where a previous run stopped.

_cosine\_distances\_folder/0.csv_

|0|1|2|...|193|
|---|---|---|---|---|
|0.0|0.10113166195376344|0.10608365968944822|...|0.12256780015419944|

_cosine\_distances\_folder/1.csv_

|0|1|2|...|193|
|---|---|---|---|---|
|0.10113166195376344|4.440892098500626e-16|0.06806455175552883|...|0.10189725676225103|

------------------

### `hybridBALDClusterRandomSampling.py`

**Usage**
```bash
python hybridBALDClusterRandomSampling.py -input <file_bald_cluster_predictions> \
                                          -distance <distance_folder> \
                                          -sampling <number_of_samples> \
                                          -out <path_output_file> \
                                          -seed <random_seed>
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` | Yes | file path with the BALD and cluster info (must contain `pmid`, `number`, `BALD`, `weights`, `cluster`, `medoid` and `outlier` columns) |
| `-distance` | `str` | Yes | folder with the per-sample distance files, named `sample_<index>.csv` where `<index>` is the row index of that sentence in `-input` |
| `-sampling` | `int` | Yes | total number of sentences to select (must be at least twice the number of clusters, and no larger than the number of unique `pmid`+`number` sentences) |
| `-out` | `str` | Yes | name of the file where the selected sentences will be saved (the program stops if this file already exists) |
| `-seed` | `int` | Yes | random seed used for the random-sampling steps |

**Input example**

```bash
python hybridBALDClusterRandomSampling.py -input results_loop/pool_short_classification_fusedResults.csv \
                                          -distance cosine_distances_folder \
                                          -sampling 15 \
                                          -out pool_short_hybridSamplingResults.csv \
                                          -seed 2
```

_results\_loop/pool\_short\_classification\_fusedResults.csv_

|pmid|number|text|BALD|weights|cluster|medoid|outlier|
|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|0.0006594062|0.00862068965517241|0|False|True|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|6.443262e-05|0.00862068965517241|1|False|False|
|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|0.002461493|0.0204081632653061|1|False|False|

_cosine\_distances\_folder/sample\_0.csv_

|0|1|2|...|193|
|---|---|---|---|---|
|0.0|0.10113166195376344|0.10608365968944822|...|0.12256780015419944|

**Output example**

For each cluster the script assigns roughly `-sampling / number_of_clusters` sentences, split into three groups: diversity samples (the cluster's medoid and outlier rows, or their nearest non-diversity neighbor from the same cluster's distance files if the medoid/outlier sentence was already claimed by another cluster), uncertainty samples (the sentences with the highest `BALD_weighted = BALD * weights` score, keeping only the most uncertain row per unique `pmid`+`number`), and random samples (about 10% of the cluster's quota, drawn with `-seed`). If some clusters run out of sentences before reaching their quota, the shortfall is made up from the remaining unselected sentences across all clusters, split evenly between extra uncertainty and extra random picks. Every input row is kept in the output, with two columns added: `BALD_weighted`, and `selected`/`reason` marking whether the row was chosen and why (`diversity`, `uncertainty`, `random`, `uncertainty_remaining` or `random_remaining`; unselected rows get `False`/`NA`).

_pool\_short\_hybridSamplingResults.csv_

|pmid|number|text|BALD|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|prob_int|weights|cluster|medoid|outlier|selected|reason|BALD_weighted|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|0.0006594062|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|(0.4,0.5]|0.0086206896551724|0|False|True|True|diversity|5.684536206896543e-06|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|6.443262e-05|NA|-0.101926796|-0.14922045|0|0.5118212,0.48817876|(0.4,0.5]|0.0086206896551724|1|False|False|False|NA|5.554536206896542e-07|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|0.002461493|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|(0.3,0.4]|0.0204081632653061|1|False|False|False|NA|5.023455102040811e-05|

------------------

### `poolAndBatchUpdating.py`

**Usage**
```bash
python poolAndBatchUpdating.py <originalPool> <samplingFile> <iter> -outUnlabelled <output_new_pool> -outBatch <output_new_batch> [-errorids <output_notfound_ids>] [-inter <folder_intermediate_files>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `originalPool` | `str` | Yes | name of the file where the pool of unlabelled sentences is stored |
| `samplingFile` | `str` | Yes | file with the pool samples and the selection information |
| `iter` | `int` | Yes | number of the iteration of the AL loop this is going to be |
| `-outUnlabelled` | `str` | Yes | filename of the output file with the new pool of unlabelled sentences |
| `-outBatch` | `str` | Yes | filename of the new batch of sentences to label |
| `-errorids` | `str` | No | filename of the ids that have not been found in the unlabelled dataframe, by default `notFoundIds.csv` |
| `-inter` | `str` | No | if provided, folder that will store the intermediate files generated by the script |

**Input example**

```bash
python poolAndBatchUpdating.py pool_short.csv \
                               pool_short_hybridSamplingResults.csv\
                               2 \
                               -outUnlabelled pool_short_iter2.csv \
                               -outBatch batchLabelForIter2.csv
```

_pool\_short.csv_

|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of type II collagen synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|['type II collagen']|['135']|['151']|['395069']|['P02460']|['9031']|
|68959|6|With the onset of chondrogenesis, a gradual transition to type II collagen synthesis was observed.|['type II collagen']|['60']|['76']|['-']|['-']|['9606']|
|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including PPAR signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|['PPAR']|['138']|['142']|['-']|['-']|['7955']|


_pool\_short\_hybridSamplingResults.csv_

|pmid|number|text|BALD|labels|logits_0|logits_1|predicted_label|prob_0|prob_1|prob_int|weights|cluster|medoid|outlier|selected|reason|BALD_weighted|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|0.0006594062|NA|-0.056893274|-0.20418982|0|0.5367577|0.4632423|(0.4,0.5]|0.0086206896551724|0|False|True|True|diversity|5.684536206896543e-06|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|6.443262e-05|NA|-0.101926796|-0.14922045|0|0.5118212,0.48817876|(0.4,0.5]|0.0086206896551724|1|False|False|False|NA|5.554536206896542e-07|
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|0.002461493|NA|0.25728434|-0.23098406|0|0.61969846|0.3803016|(0.3,0.4]|0.0204081632653061|1|False|False|False|NA|5.023455102040811e-05|

**Output example**

The rows whose `pmid`+`number` were marked `selected == True` in the samplingFile are pulled out of `originalPool`, tagged with an `ALIteration` column set to `-iter`, and written to `-outBatch`; the same rows are removed from `originalPool` and the remainder is written to `-outUnlabelled`. Any selected `pmid`+`number` combination that could not be found in `originalPool` is written to `-errorids` instead (the run above finds a match for every selected id, so no file would actually be produced). When `-inter` is given, the selected ids and the intermediate merge results used to build the batch and the new pool are also saved there.

_batchLabelForIter2.csv_
|pmid|number|text|gene|start|end|id|uniprotid|sa|ALIteration|
|---|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of [TARGET][GENE][/TARGET] synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|['type II collagen']|['135']|['151']|['395069']|['P02460']|['9031']|2|
|...|...|...|...|...|...|...|...|...|...|
|39990652|4|Chondrocytes, the key cells in articular cartilage, maintain its structure by producing an extracellular matrix rich in aggrecan and type II collagen (COL2).|['aggrecan', 'COL2']|['122', '153']|['130', '157']|['176', '-']|['P16112', '-']|['9606', '9606']|2|

_pool\_short\_iter2.csv_
|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|68959|6|With the onset of chondrogenesis, a gradual transition to [TARGET][GENE][/TARGET] synthesis was observed.|['type II collagen']|['60']|['76']|['-']|['-']|['9606']|
|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including [TARGET][GENE][/TARGET] signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|['PPAR']|['138']|['142']|['-']|['-']|['7955']|

---
---

### `embedingsSBioBERT.py`

> Used only once, at the very beginning of the AL loop (the initial/first iteration), to compute the embeddings needed by `coreSetExtraction.py` to select the first batch of sentences to label.

**Usage**
```bash
python embedingsSBioBERT.py <input_file> <output_file> \
                            -tokenizer <path_tokenizer> \
                            -model <path_model> \
                            [-batch <batch_size> -maxlength <max_sequence_length>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `input` | `str` | Yes | CSV file with dataframe (must contain `pmid`, `number` and `text` columns) |
| `output` | `str` | Yes | path to save the final CSV |
| `-tokenizer` | `str` | Yes | path or name of the pretrained Hugging Face tokenizer |
| `-model` | `str` | Yes | path or name of the pretrained Hugging Face model (must return token-level embeddings compatible with mean pooling, e.g. a sentence-transformer-style encoder such as SBioBERT) |
| `-batch` | `int` | No | batch size used by the dataloader (default `100`) |
| `-maxlength` | `int` | No | max sequence length used for tokenization/truncation (default `512`) |

**Input example**

```bash
python embedingsSBioBERT.py pool_short.csv pool_short_embeddings.csv \
                            -tokenizer /home/user/models/SBioBERT/tokenizer_SBioBERT \
                            -model /home/user/models/SBioBERT/model_SBioBERT
```

_pool\_short.csv_
|pmid|number|text|
|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of type II collagen synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|
|68959|6|With the onset of chondrogenesis, a gradual transition to type II collagen synthesis was observed.|
|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including PPAR signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|

**Output example**

The `text` column is tokenized and passed through `-model` in batches (on GPU if available), and mean pooling (averaging token embeddings, weighted by the attention mask) produces one embedding vector per sentence. Two files are written: `output`, with the original `pmid`, `number`, `text` columns joined to the embedding columns (used as the `-embeddings` input for `coreSetExtraction.py`), and `<output_basename>_embeddings<ext>`, with only the embedding columns.

_pool\_short\_embeddings.csv_
|pmid|number|text|0|1|...|767|
|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of type II collagen synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|0.12525174|0.073949404|...|0.33107397|
|68959|6|With the onset of chondrogenesis, a gradual transition to type II collagen synthesis was observed.|-0.07557922|0.1796895|...|-0.24311118|
|...|...|...|...|...|...|...|

_pool\_short\_embeddings\_embeddings.csv_
|0|1|...|767|
|---|---|---|---|
|0.12525174|0.073949404|...|0.33107397|
|-0.07557922|0.1796895|...|-0.24311118|
|...|...|...|...|

------------------

### `coreSetExtraction.py`

> Used only once, at the very beginning of the AL loop (the initial/first iteration), to select the first batch of sentences to label from the embeddings produced by `embedingsSBioBERT.py`.

**Usage**
```bash
python coreSetExtraction.py -embeddings <file_embeddings> \
                            -selection <amount_sentences_to_select> \
                            -metadata <file_metadata> \
                            -output <path_output_file> \
                            [-seed <random_seed>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-embeddings` | `str` | Yes | the main output file of `embedingsSBioBERT.py` (first column is used as the index, followed by `pmid`, `number`, `text` and then the embedding dimensions) |
| `-selection` | `int` | Yes | number of sentences to select/return (cannot be greater than the number of rows in `-embeddings`) |
| `-metadata` | `str` | Yes | file with the information of the sentences in `-embeddings` (must have the same number of rows, and contain `pmid`, `number` and `text` columns) |
| `-output` | `str` | Yes | file to save the selected rows of the data |
| `-seed` | `int` | No | random seed set for reproducible selection (default `42`) |

**Input example**

```bash
python coreSetExtraction.py -embeddings pool_short_embeddings.csv \
                            -selection 1 \
                            -metadata pool_short_hybridSamplingResults.csv \
                            -output pool_short_coreset.csv \
                            -seed 9
```

_pool\_short\_embeddings.csv_
|pmid|number|text|0|1|...|767|
|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of type II collagen synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|0.12525174|0.073949404|...|0.33107397|
|68959|6|With the onset of chondrogenesis, a gradual transition to type II collagen synthesis was observed.|-0.07557922|0.1796895|...|-0.24311118|
|...|...|...|...|...|...|...|

_pool\_short.csv_

|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of type II collagen synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|['type II collagen']|['135']|['151']|['395069']|['P02460']|['9031']|
|68959|6|With the onset of chondrogenesis, a gradual transition to type II collagen synthesis was observed.|['type II collagen']|['60']|['76']|['-']|['-']|['9606']|
|...|...|...|...|...|...|...|...|...|
|40015854|9|Transcriptome sequencing of larvae showed that FEN altered the expressions of multiple metabolic and nervous system pathways, including PPAR signaling pathway, lipid metabolism pathway, carbohydrate metabolism pathway, retinol metabolism pathway, and neuroactive ligand-receptor interaction pathway, demonstrating that FEN alters the normal development of zebrafish embryos, and multiple pathways mediating the FEN-induced developmental toxicity.|['PPAR']|['138']|['142']|['-']|['-']|['7955']|

**Output example**

Starting from one randomly chosen sentence, the script greedily grows a "core set" of `-selection` sentences by repeatedly picking, from the remaining `-embeddings` rows, the one that is furthest (in cosine distance) from the sentences already chosen, so that the final selection covers the embedding space as diversely as possible. The `pmid`+`number`+`text` of the selected rows are then inner-merged back onto `-metadata` to recover the full row of information for each selected sentence.

_pool\_short\_coreset.csv_

|pmid|number|text|gene|start|end|id|uniprotid|sa|
|---|---|---|---|---|---|---|---|---|
|68959|2|This work describes an approach to monitor chondrogenesis of stage-24 chick limb mesodermal cells in vitro by analyzing the onset of type II collagen synthesis with carboxymethyl-cellulose chromatography, immunofluorescence, and radioimmunoassay.|['type II collagen']|['135']|['151']|['395069']|['P02460']|['9031']|