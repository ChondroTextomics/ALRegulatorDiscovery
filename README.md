# ALRegulatorDiscovery

**readme in process**

Active-learning NLP pipeline for identifying candidate regulators of chondrogenesis from the biomedical literature, and the downstream tooling used to reproduce and extend the re-use the analysis of the project

This repository holds the **pipeline code** — not the trained model weights or the datasets. See [Data & Models](#data--models) below for where those live.

## What this repo does

Starting from PubMed abstracts, the pipeline:

1. Splits text into sentences and identifies gene mentions.
2. Uses an active-learning loop (with a curator labelling app) to iteratively annotate a small set of sentences.
3. Trains a PubMedBERT-based classifier to predict, per gene mention, whether it acts as a chondrogenesis regulator or not.
4. Benchmarks that classifier against open-weight LLMs (Qwen3, Llama 3.1) under a single-GPU, local-inference constraint.
5. Applies the trained classifier across the full corpus to surface novel candidate regulators, including genes absent from existing Gene Ontology annotations.

The code is organised so the core method is reusable beyond chondrogenesis:

- **Process-agnostic:** `pipeline_process_text/`, `al_loop/`, `labelling/`
- **Project-specific analysis:** `postprocessing/`, `benchmark_comparison/`

The core method is not specific to cartilage biology and can be adapted to other biological processes (see [Getting started](#getting-started)).
## Repository structure

```
ALRegulatorDiscovery/
├── al_loop/                   # reusable NLP + active learning + classifier code
├── benchmark_comparison/      # scripts used for LLM and logistic regression model usage
├── benchmark_models/          # models used as comparison with the main model used in al_loop
├── data/                      # link to data repository
├── envs/                      # per-task dependency/environment files
├── guides/                    # specific guides of the usage of the scripts for the project
├── labelling/                 # scripts used to label gene entities
├── model/                     # link to the final model weights produced by the al_loop
├── pipeline_process_text/     # scripts used to produce the input for al_loop and labelling
├── postprocessing/            # scripts used to analyse the results of models as well as creation of different plots
└── README.md
```

**Note: no containerized environment (e.g. Docker) is provided. Each task has its own environment file under `envs/`.**

## Getting started

### 1. Choose your use case

This repo supports a few different starting points — pick the guide that matches what you want to do:

| I want to... | Guide |
|---|---|
| Reproduce the results in the paper | [`guides/in-process.md`](guides/in-process.md) |
| Adapt the pipeline to a new biological process | [`guides/in-process-1`](guides/in-process-1) |
| Use the trained model to classify new abstracts | [`guides/model-inference.md`](guides/model-inference.md) |

### 2. Set up an environment

Each task has its own environment (Python or R). No container image (e.g. Docker) is provided. See [`envs/`](envs/) for setup instructions for each task.

Install the one relevant to your use case, e.g.:

```bash
python -m venv venv
source venv/bin/activate
pip install -r envs/<task>-requirements.txt
```

```r
install.packages("renv")
renv::restore(lockfile = "envs/<task>-renv.lock")
```

```bash
Rscript -e 'install.packages(readLines("envs/<task>-r-requirements.txt"), repos = "https://cloud.r-project.org")'
```

### 3. Get the data and model weights

This repo does **not** include trained weights or datasets. See [Data & Models](#data--models) below.

These and more links can be found in `/benchmark_models`, `/model` and `/data`.

## Data & Models

| Artifact | Location |
|---|---|
| Trained PubMedBERT classifier | [Hugging Face Hub Model Link](https://huggingface.co/amav/pubmedbert-chondrogenesis-classifier)|
| Training data, per-curator + aggregated labels, benchmarking results | [Zenodo Link](https://doi.org/10.5281/zenodo.22746090) |

## Citing this work

If you use this pipeline or the associated model/data, please cite:

> *Citation to be added on publication.*

## Questions

Open an issue on this repo, or contact a.valdes@liverpool.ac.uk.

## Acknowledgements
 
This work was funded by the BBSRC UKRI

## License

Code in this repository is released under the [MIT License](LICENSE).
