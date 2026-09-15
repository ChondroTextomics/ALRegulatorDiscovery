# ALRegulatorDiscovery

**readme in process**

Active-learning NLP pipeline for identifying candidate regulators of chondrogenesis from the biomedical literature, and the downstream tooling used to reproduce and extend the re-use the analysis of the project

This repository holds the **pipeline code** — not the trained model weights or the datasets. See [Data & Models](#data--models) below for where those live.

## What this repo does

Starting from PubMed abstracts, the pipeline:

1. Splits text into sentences and identifies gene mentions.
2. Uses an active-learning loop (with a curator labelling app) to iteratively annotate a small set of sentences.
3. Trains a PubMedBERT-based classifier to predict, per gene, whether it acts as a chondrogenesis regulator.
4. Applies the trained classifier across the full corpus to surface novel candidate regulators — including genes absent from existing Gene Ontology annotations.
5. Benchmarks that classifier against open-weight LLMs (Qwen3, Llama 3.1) under a single-GPU, local-inference constraint.

The code is split into two layers:

- **`pipeline/`** — reusable, process-agnostic code (sentence splitting, active learning loop, classifier training/inference, evaluation). Not specific to chondrogenesis or cartilage.
- **`chondrogenesis/`** — the application of that pipeline to this project: config, gene lists, GO enrichment analysis, and scripts to reproduce the paper's results.
- **`labelling-app/`** — the curator-facing annotation tool used during active learning rounds.

## Repository structure

```
al-regulator-discovery/
├── pipeline/            # reusable NLP + active learning + classifier code
├── chondrogenesis/      # chondrogenesis-specific config, scripts, GO analysis
├── labelling-app/       # curator annotation tool
├── docs/                # guides (see below)
├── envs/                # per-task dependency/environment files
└── README.md
```

> Note: no containerized environment (e.g. Docker) is provided. Each task has its own environment file under `envs/` — see the relevant guide for setup instructions.

## Getting started

### 1. Choose your use case

This repo supports a few different starting points — pick the guide that matches what you want to do:

| I want to... | Guide |
|---|---|
| Reproduce the results in the paper | [`docs/reproduce-paper.md`](docs/reproduce-paper.md) |
| Adapt the pipeline to a new biological process | [`docs/new-process.md`](docs/new-process.md) |
| Use the trained model to classify new abstracts | [`docs/use-trained-model.md`](docs/use-trained-model.md) |

### 2. Set up an environment

Each task has its own environment file under `envs/` (no shared container). Install the one relevant to your use case, e.g.:

```bash
python -m venv venv
source venv/bin/activate
pip install -r envs/<task>-requirements.txt
```

### 3. Get the data and model weights

This repo does **not** include trained weights or datasets. See [Data & Models](#data--models) below.

## Data & Models

| Artifact | Location |
|---|---|
| Trained PubMedBERT classifier | Hugging Face Hub — *link TBD* |
| Training data, per-curator + aggregated labels, benchmarking results | Zenodo — *DOI TBD (draft available)* |
| Raw PubMed data | Shared as PMIDs only (not abstract text), via the Zenodo record above |

## Citing this work

If you use this pipeline or the associated model/data, please cite:

> *Citation to be added on publication.*

## Questions

Open an issue on this repo, or contact [maintainer contact — TBD].
