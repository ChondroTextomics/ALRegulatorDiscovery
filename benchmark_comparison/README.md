## Overview

This folder contains the resources required to do the comparison of the main model (the one trained with the `al_loop` folder) with the models stated in the folder `benchmark_comparison`

Requirements for running the scripts in this folder are provided in the `envs` folder. Different models have different environment requirements due to incompatibility of the packages with the used HuggingFace models.

---
## Files

### `logisticRegressionWithEmbeddings.py`

**Usage**
```bash
python logisticRegressionWithEmbeddings.py -training <training_file> -test <evaluation_file> -out <output_file> -model <path_hf_model> -tokenizer <path_hf_tokenizer> -batch <amount_training_batch> [-seed <random_seed>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-training` | `str` | Yes | path to the file that will be used for training the logistic regression model |
| `-test` | `str` | Yes | path to the file that will be used to evaluate the logistic regression model |
| `-out` | `str` | Yes | path to the file where the results will be saved |
| `-model` | `str` | Yes | path to the huggingface model |
| `-tokenizer` | `str` | Yes | path to the huggingface tokenizer |
| `-batch` | `int` | Yes | amount of sampels to use per batch for training and predicting |
| `-seed` | `int` | No | number taht will serve as seed for reproducibility (default 24) |

**Input example**

```bash
python logisticRegressionWithEmbeddings.py -training trainigData_NLPFormat.csv  \
						                   -test validationDataset_short_nlpFormat.csv \
						                   -out lr_baseline_held-out.csv \
						                   -seed 4 \
						                   -model pubMedBERTmodel/model \
						                   -tokenizer pubMedBERTmodel/tokenizer \
						                   -batch 10
```
_trainingData\_NLPFormat.csv_
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
|...|...|...|...|
|21971552|3|The aim of this study was to investigate, using a rotary cell culture system (RCCS) bioreactor, the effects of microgravity on the chondrogenic differentiation of human adipose-derived MSCs (ADSCs), which were cultured in pellets with or without the chondrogenic growth factor [TARGET][GENE][/TARGET].|1|

**Output example**

_lr\_baseline\_held-out.csv_

|pmid|number|text|labels|label_pool	label_cls|prob_0_pool|prob_0_cls|prob_1_pool|prob_1_cls|
|---|---|---|---|---|---|---|---|---|
|241677|12|Cells forming the regeneration blastema were [TARGET][GENE][/TARGET] reactive during the early formative phase, but with growth and development of the blastema into bulb and conic forms, these cells did not respond for this enzyme-activity.|0|0|0|0.969891442|0.995304417|0.030108558|0.004695583|
|271986|7|With the onset of chondrogenesis, [TARGET][GENE][/TARGET] was detected in the cartilage matrix on day 6 and persisted until the early stages of bone formation.|0|0|0|0.965214775|0.989361203|0.034785225|0.010638797|
|1314187|4|Synthesis of sulfated proteoglycans, an index of chondrogenesis, was inhibited by all three PDGF isoforms ([TARGET][GENE][/TARGET], [GENE], and [GENE]).|1|0|0|0.957652913|0.967245378|0.042347087|0.032754622|
|...|...|...|...|...|...|...|...|...|
|21971552|3|The aim of this study was to investigate, using a rotary cell culture system (RCCS) bioreactor, the effects of microgravity on the chondrogenic differentiation of human adipose-derived MSCs (ADSCs), which were cultured in pellets with or without the chondrogenic growth factor [TARGET][GENE][/TARGET].|1|0|0|0.92741126|0.849298807|0.07258874|0.150701193|

------------------

### `creationDatasetsLLMs.py`

Transforms one or several csv files (NLP format) into a HuggingFace `DatasetDict` in chat format (system / user / assistant), ready for fine-tuning or evaluating LLMs. Each row becomes one conversation: the system prompt, the user prompt (with the sentence inserted) and the expected answer (`Yes` if the label is 1, `No` otherwise).

**Usage**
```bash
python creationDatasetsLLMs.py -input <csv_file_1> [<csv_file_2> ...] -systemPrompt <system_prompt_file> -userPrompt <user_prompt_file> -output <output_folder> -nameHfDataset <name_1> [<name_2> ...]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-input` | `str` (one or more) | Yes | path(s) to the csv file(s) that will be transformed into the HuggingFace dataset. Must contain the columns `pmid`, `number`, `text` and `labels` |
| `-systemPrompt` | `str` | Yes | path to the text file with the system prompt |
| `-userPrompt` | `str` | Yes | path to the text file with the user prompt template. It must contain the placeholder `{sentence_to_classify}`, which is replaced by the `text` of each row |
| `-output` | `str` | Yes | path to the folder where the dataset will be saved. If it already exists the script asks for confirmation before overwriting it |
| `-nameHfDataset` | `str` (one or more) | Yes | name of each split in the `DatasetDict` (e.g. `train`, `validation`). The number of names must match the number of `-input` files, and they are paired in order |

**Input example**

```bash
python creationDatasetsLLMs.py -input trainigData_NLPFormat.csv validationDataset_short_nlpFormat.csv \
                               -systemPrompt system_prompt.xml \
                               -userPrompt user_prompt.md \
                               -nameHfDataset train validation \
                               -output datasets/llm_dataset
```
_trainingData\_NLPFormat.csv_
|pmid|number|text|labels|
|---|---|---|---|
|1952598|2|Synergistic action of [GENE] and [TARGET][GENE][/TARGET].|0|
|1952598|2|Synergistic action of [TARGET][GENE][/TARGET] and [GENE].|1|
|2919122|1|Effect of [TARGET][GENE][/TARGET]/insulin-like growth factor I and growth hormone on cultured growth plate and articular chondrocytes.|0|

_validationDataset\_short\_nlpFormat.csv_

|pmid|number|text|labels|
|---|---|---|---|
|241677|12|Cells forming the regeneration blastema were [TARGET][GENE][/TARGET] reactive during the early formative phase, but with growth and development of the blastema into bulb and conic forms, these cells did not respond for this enzyme-activity.|0|
|1314187|4|Synthesis of sulfated proteoglycans, an index of chondrogenesis, was inhibited by all three PDGF isoforms ([TARGET][GENE][/TARGET], [GENE], and [GENE]).|1|
|...|...|...|...|

_system\_prompt.xml_
```text
<role>
  You are a molecular biology assistant that works in chondrogenesis.
</role>
<task>
  Classify whether a gene is a regulator of chondrogenesis.
</task>
<context>
  <definition_chondrogenesis>
    Chondrogenesis is the biological process through which cartilage tissue, known as chondrocytes, is formed and developed.
  </definition_chondrogenesis>
  <definition_regulator>
    A chondrogenesis regulator is a gene whose activity directly modulates the frequency, rate, or extent of chondrogenesis.
  </definition_regulator>
</context>
<output>
  Output must consist of a single word only: "Yes" or "No".
  Output "Yes" if the target gene is a regulator of chondrogenesis.
  Output "No" otherwise.
</output>
```

_user\_prompt.md_
```text
## Task
Your task is to determine whether the target gene (marked as [TARGET][GENE][/TARGET]) is a regulator of chondrogenesis based only on the provided text.
## Text to classify
{sentence_to_classify}
```

**Output example**

_datasets/llm\_dataset_ (folder created with `save_to_disk`, it can be loaded with `datasets.load_from_disk("datasets/llm_dataset")` in python)

```text
DatasetDict({
    train: Dataset({
        features: ['messages', 'metadata'],
        num_rows: 3
    })
    validation: Dataset({
        features: ['messages', 'metadata'],
        num_rows: 41
    })
})
```

Example of one record of `train`:

```text
{
	'messages': [
		{'role': 'system', 'content': '<role>\n  You are a molecular biology assistant that works in chondrogenesis.\n</role>\n<task>\n  Classify whether a gene is a regulator of chondrogenesis.\n</task>\n<context>\n  <definition_chondrogenesis>\n    Chondrogenesis is the biological process through which cartilage tissue, known as chondrocytes, is formed and developed.\n  </definition_chondrogenesis>\n  <definition_regulator>\n    A chondrogenesis regulator is a gene whose activity directly modulates the frequency, rate, or extent of chondrogenesis.\n  </definition_regulator>\n</context>\n<output>\n  Output must consist of a single word only: "Yes" or "No".\n  Output "Yes" if the target gene is a regulator of chondrogenesis.\n  Output "No" otherwise.\n</output>'}, 
		{'role': 'user', 'content': '## Task\nYour task is to determine whether the target gene (marked as [TARGET][GENE][/TARGET]) is a regulator of chondrogenesis based only on the provided text.\n## Text to classify\nSynergistic action of [GENE] and [TARGET][GENE][/TARGET].'},
		{'role': 'assistant', 'content': 'No'}], 
	'metadata': {'pmid': 1952598, 'number': 2}
}
```

---

### `LLMInferenceHF.py`

Runs a HuggingFace LLM (no specific quantisation) over one split of a dataset created with `creationDatasetsLLMs.py`. For each record the assistant answer (gold label) is separated from the conversation, the remaining system / user messages are given to the model, and the generated text is stored together with the probability of `Yes` and `No` for the answer token. Models and tokenizers must be already downloaded locally (the script does not use the network). Loading time, total time and time per sample are tracked.

**Usage**
```bash
python LLMInferenceHF.py -data <hf_dataset_folder> -split <split_name> -out <output_folder> -model <path_hf_model> -tokenizer <path_hf_tokenizer> [-maxToken <max_new_tokens> -batch <batch_size>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-data` | `str` | Yes | path to the HuggingFace dataset (`DatasetDict` saved with `save_to_disk`, e.g. the output of `creationDatasetsLLMs.py`) |
| `-split` | `str` | Yes | split of the `DatasetDict` to run the inference on (e.g. `train`, `validation`) |
| `-out` | `str` | Yes | path to the folder where all the outputs will be saved. It is created if it does not exist |
| `-model` | `str` | Yes | path to the local huggingface model folder |
| `-tokenizer` | `str` | Yes | path to the local huggingface tokenizer folder |
| `-maxToken` | `int` | No | maximum number of tokens generated by the model, must be higher than 0 (default 32768) |
| `-batch` | `int` | No | number of samples per batch for the generation (default 8) |

**Input example**

```bash
python LLMInferenceHF.py -data datasets/llm_dataset \
                         -split train \
                         -out results_validation_llm \
                         -model models/llm_model/model \
                         -tokenizer models/llm_model/tokenizer \
                         -batch 1
```

_datasets/llm\_dataset_ (output of `creationDatasetsLLMs.py`, see above)

```text
DatasetDict({
    train: Dataset({
        features: ['messages', 'metadata'],
        num_rows: 3
    })
    validation: Dataset({
        features: ['messages', 'metadata'],
        num_rows: 41
    })
})
```

Example of one record of `train`:

```text
{
	'messages': [
		{'role': 'system', 'content': '<role>\n  You are a molecular biology assistant that works in chondrogenesis.\n</role>\n<task>\n  Classify whether a gene is a regulator of chondrogenesis.\n</task>\n<context>\n  <definition_chondrogenesis>\n    Chondrogenesis is the biological process through which cartilage tissue, known as chondrocytes, is formed and developed.\n  </definition_chondrogenesis>\n  <definition_regulator>\n    A chondrogenesis regulator is a gene whose activity directly modulates the frequency, rate, or extent of chondrogenesis.\n  </definition_regulator>\n</context>\n<output>\n  Output must consist of a single word only: "Yes" or "No".\n  Output "Yes" if the target gene is a regulator of chondrogenesis.\n  Output "No" otherwise.\n</output>'}, 
		{'role': 'user', 'content': '## Task\nYour task is to determine whether the target gene (marked as [TARGET][GENE][/TARGET]) is a regulator of chondrogenesis based only on the provided text.\n## Text to classify\nSynergistic action of [GENE] and [TARGET][GENE][/TARGET].'},
		{'role': 'assistant', 'content': 'No'}], 
	'metadata': {'pmid': 1952598, 'number': 2}
}
```

**Output example**

The folder `results_validation_llm` will contain:

```text
results_validation_llm/
├── table_output_complete.csv
├── time_tracking.txt
└── datasets/llm_dataset_processed/   (DatasetDict saved with save_to_disk)
```

_results\_validation\_llm/table\_output\_complete.csv_

|pmid|number|user_mssg|label|generated_text|predicted_label|prob_yes_all_logits|prob_no_all_logits|prob_yes|prob_no|avg_elapsed_time_sample_batch|
|---|---|---|---|---|---|---|---|---|---|---|
|1952598|2|## Text to classify
Synergistic action of [GENE] and [TARGET][GENE][/TARGET].|No|Yes|Yes|0.9999996423721313|3.4095148748747306e-07|0.9999996423721313|3.4095148748747306e-07|5.34798454499105|
|...|...|...|...|...|...|...|...|...|...|...|

_time\_tracking.txt_

```text
Model load time: 17.81s
Total time: 49.10s
Avg time per batch for the samples are recorded in results_validation_llm/table_output_complete.csv
```

The saved dataset (`datasets/llm_dataset_processed`) is the input `DatasetDict` plus a new split `validation_processed` with the extra features such as `gold_assistant`.

**Notes**
- The answer token is assumed to be the second to last generated token (`outputs.logits[-2]`), so the model must answer `Yes`/`No` followed by the end-of-sequence token. The prompt is built with `enable_thinking = False`.
- The token ids of `Yes` and `No` are obtained with `tokenizer.convert_tokens_to_ids`, so the tokenizer must have those exact tokens.
- The FP8 kernel is pinned to a cached commit at the top of the script so it works in compute nodes without network.

---

### `LLMInferenceHFAWQ.py`

Runs an AWQ-quantised HuggingFace LLM over one split of a dataset created with `creationDatasetsLLMs.py`. It is the same script as `LLMInferenceHF.py` (see above for the details of the processing and the outputs) but customised for Llama models: the model is loaded from its quantised safetensors weights and, because Llama has no padding token, the end-of-sequence token is used as padding token. Models and tokenizers must be already downloaded locally. Loading time, total time and time per sample are tracked.

**Usage**
```bash
python LLMInferenceHFAWQ.py -data <hf_dataset_folder> -split <split_name> -out <output_folder> -model <path_hf_model> -tokenizer <path_hf_tokenizer> [-maxToken <max_new_tokens> -batch <batch_size>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-data` | `str` | Yes | path to the HuggingFace dataset (`DatasetDict` saved with `save_to_disk`, e.g. the output of `creationDatasetsLLMs.py`) |
| `-split` | `str` | Yes | split of the `DatasetDict` to run the inference on (e.g. `train`, `validation`) |
| `-out` | `str` | Yes | path to the folder where all the outputs will be saved. It is created if it does not exist |
| `-model` | `str` | Yes | path to the local AWQ-quantised huggingface model folder |
| `-tokenizer` | `str` | Yes | path to the local huggingface tokenizer folder |
| `-maxToken` | `int` | No | maximum number of tokens generated by the model, must be higher than 0 (default 32768) |
| `-batch` | `int` | No | number of samples per batch for the generation (default 8) |

**Input example**

```bash
python LLMInferenceHFAWQ.py -data datasets/llm_dataset \
                         	-split train \
                         	-out results_validation_llm \
                         	-model models/llm_model/model \
                         	-tokenizer models/llm_model/tokenizer \
                         	-batch 1
```

_datasets/llm\_dataset_ (output of `creationDatasetsLLMs.py`, the same input files can be used as in `LLMInferenceHF.py`)

**Output example**

The folder `results_validation_llama_awq` will contain the same files as in `LLMInferenceHF.py`:

```text
results_validation_llama_awq/
├── table_output_complete.csv
├── time_tracking.txt
└── datasets/llm_dataset_processed/   (DatasetDict saved with save_to_disk)
```

The content of `table_output_complete.csv` and `time_tracking.txt` has the same format as the one described for `LLMInferenceHF.py`. The script additionally prints the total time when it finishes.

**Notes**
- Differences with `LLMInferenceHF.py`: the model is loaded with `use_safetensors = True` (AWQ weights), the FP8 kernel pin is not needed, and the padding token is set with `tokenizer.pad_token = tokenizer.eos_token` and `model.config.pad_token_id = tokenizer.eos_token_id`.
- Loading an AWQ model requires the AWQ dependencies (e.g. `autoawq`) to be installed in the environment, see the `envs` folder.
- The answer token is assumed to be the second to last generated token (`outputs.logits[-2]`), so the model must answer `Yes`/`No` followed by the end-of-sequence token.
- The token ids of `Yes` and `No` are obtained with `tokenizer.convert_tokens_to_ids`, so the tokenizer must have those exact tokens. Llama tokenizers may not have them as single tokens (they can be e.g. `ĠYes`), so check it before running.

---

### `bootstrappingPredictions.py`

Computes bootstrap confidence intervals for the performance of a model from its predictions. It is useful when the model cannot be run many times (e.g. very time consuming LLMs): instead of repeating the training/inference, the predictions file is resampled with replacement `-iterations` times and, for each resampled dataset, the AUC-ROC, F1, precision and recall are computed. Then the mean, standard deviation, minimum, maximum and the 95% confidence interval (percentiles 2.5 and 97.5) of each metric are summarised. The resampling can be done row by row (default) or by clusters (e.g. by sentence) with `-cluster`, so all the rows of the same cluster are kept together. Optionally, every bootstrapped dataset can be saved.

**Usage**
```bash
python bootstrappingPredictions.py -data <predictions_file> -filePerformance <performance_file> -summaryFile <summary_file> -iterations <number_iterations> -column_label <true_label_column> -column_predicted_label <predicted_label_column> -column_prob_positive <prob_positive_column> -positive_class <positive_label> [-cluster <column_1> <column_2> ...] [-outFolder <output_folder> -out <file_name_root>]
```

**Arguments**

| Argument | Type | Required | Description |
|---|---|---|---|
| `-data` | `str` | Yes | path to the csv file with the predictions of the model |
| `-filePerformance` | `str` | Yes | path to the csv file where the performance of each one of the bootstrapped datasets will be saved |
| `-summaryFile` | `str` | Yes | path to the csv file where the summary (mean, std, min, max and confidence interval) of each performance metric will be saved |
| `-iterations` | `int` | Yes | number of resamplings of the bootstrap, must be greater than 0 |
| `-column_label` | `str` | Yes | name of the column that contains the true labels |
| `-column_predicted_label` | `str` | Yes | name of the column that contains the predicted labels |
| `-column_prob_positive` | `str` | Yes | name of the column that contains the probability of the positive class |
| `-positive_class` | `str` | Yes | label of the positive class (e.g. `Yes`, or `1` if the labels are numeric). It must be present in `-column_label` |
| `-cluster` | `str` (one or more) | No | column(s) used to do cluster bootstrapping. The unique combinations of these columns are resampled with replacement and all the rows belonging to each selected combination are kept. If it is not given, the rows are resampled individually |
| `-outFolder` | `str` | No | folder where each one of the bootstrapped datasets will be saved. It is created if it does not exist. If it is given, `-out` must be given as well |
| `-out` | `str` | No | file name root of the bootstrapped datasets, the iteration number and the extension are added (`<out>_<iteration>.csv`). It is only used if `-outFolder` is given |

**Input example**

```bash
python bootstrappingPredictions.py -data results_validation_llm/table_output_complete.csv \
                                   -filePerformance bootstrap/performance_llm.csv \
                                   -summaryFile bootstrap/summary_llm.csv \
                                   -iterations 1000 \
                                   -column_label label \
                                   -column_predicted_label predicted_label \
                                   -column_prob_positive prob_yes \
                                   -positive_class Yes \
                                   -cluster pmid number \
                                   -outFolder bootstrap/datasets \
                                   -out bootstrap_llm
```

_results\_validation\_llm/table\_output\_complete.csv_ (output of `LLMInferenceHF.py`, see above; only the relevant columns are shown)

|pmid|number|label|predicted_label|prob_yes|prob_no|
|---|---|---|---|---|---|
|1952598|2|No|Yes|0.9999996423721313|3.4095148748747306e-07|
|1952598|2|Yes|Yes|0.9812345678901234|0.0187654321098766|
|2919122|1|No|No|0.0213456789012345|0.9786543210987655|
|...|...|...|...|...|...|

**Output example**

The following files are created (the folder `bootstrap/datasets` only if `-outFolder` is given):

```text
bootstrap/
├── performance_llm.csv
├── summary_llm.csv
└── datasets/
    ├── bootstrap_llm_0.csv
    ├── bootstrap_llm_1.csv
    └── ...                      (one file per iteration)
```

_bootstrap/performance\_llm.csv_ (one row per iteration; the column `bootstrap_file` is only present if `-outFolder` is given)

|bootstrap_file|iteration|auc_roc|f1|precision|recall|
|---|---|---|---|---|---|
|bootstrap/datasets/bootstrap_llm_0.csv|0|0.9123|0.8471|0.8215|0.8744|
|bootstrap/datasets/bootstrap_llm_1.csv|1|0.9047|0.8392|0.8106|0.8698|
|...|...|...|...|...|...|

_bootstrap/summary\_llm.csv_

|index|auc_roc|f1|precision|recall|
|---|---|---|---|---|
|mean|0.9085|0.8431|0.8160|0.8721|
|std|0.0121|0.0154|0.0189|0.0167|
|min|0.8702|0.7958|0.7563|0.8194|
|max|0.9418|0.8879|0.8721|0.9203|
|ci_lower|0.8843|0.8127|0.7789|0.8392|
|ci_upper|0.9312|0.8730|0.8524|0.9046|

_bootstrap/datasets/bootstrap\_llm\_0.csv_ has the same columns as the input file, with the resampled rows (in cluster mode, the rows of a cluster selected several times appear several times).

_(The numbers of the output tables are only illustrative.)_

**Notes**
- The iteration number is used as the random seed of each resampling (`random_state = iter`), so the results are reproducible.
- The bootstrapped dataset has the same size as the original one (`frac = 1`) in row mode. In cluster mode the number of clusters is the same as the original, but the number of rows can vary as the clusters can have different sizes.
- The AUC-ROC is computed with the probability of the positive class, while precision, recall and F1 are computed with the predicted labels, using `-positive_class` as the positive label. If the labels column is numeric the positive class is converted to `int`.
- A bootstrapped dataset with only one class in the true labels makes the AUC-ROC impossible to compute and the script will fail. This is unlikely with a reasonable amount of data, but it can happen in cluster mode with few clusters.
- The confidence interval is the percentile bootstrap interval with `alpha = 0.05` (percentiles 2.5 and 97.5 of the metric across the iterations).
