# Applying the Pipeline to a New Biological Process

This guide explains how to reuse the study's pipeline to find candidate gene regulators of a **different biological process** (e.g. osteogenesis, adipogenesis, angiogenesis) instead of chondrogenesis.

It is not a full walkthrough. The pipeline is run the same way as in [`replicate-results.md`](replicate-results.md), so follow that guide step by step and use this one to know **what to change**. Only three parts need to be adapted:

1. **Pre-processing:** the PubMed queries and the concept list used to filter the sentences
2. **Labelling:** the labelling guidelines and, if needed, the labelling app
3. **Post-processing:** the GO term(s) the predictions are evaluated against

The benchmarking against the logistic regression and the LLMs (Part 5 of the replication guide, and step 6.1) is **not needed** to apply the pipeline to a new process as they are steps done to prove the utility of the model.

## Overview: what to reuse and what to change

| Replication guide part | For a new process |
|---|---|
| **1. Data extraction** | Change the queries (1.1) and the concept list (1.7). Everything else is the same |
| **2. Initial labelled data** | Same scripts. Write new labelling guidelines and adapt the app if needed |
| **3. Active learning iterations** | Same scripts. Only the settings per iteration are yours to decide |
| **4. Production model and application predictions** | Same |
| **5. Held-out evaluation** | Optional. Skip the benchmark models (5.3, 5.4) |
| **6. Post-processing** | Same scripts. Change the GO term(s) (6.6) and but use a held-out evaluation for your final model to test generalisation to new text (6.1) |

---

## 1. Pre-processing: Queries and Concept List

### 1.1 Queries

Replace the chondrogenesis terms of the base query with the terms of your process, keeping the language, review and date filters:

```text
((<process term 1> OR <process term 2>) AND "English"[Language]) NOT "Review"[Publication Type] AND ("<start>"[dp] : "<end>"[dp])
```

For example, for osteogenesis:

```text
((osteogenesis OR osteoblast differentiation) AND "English"[Language]) NOT "Review"[Publication Type] AND ("1000/01/01"[dp] : "2025/01/31"[dp])
```

Some things to take into account:

- **Test the query in PubMed first.** Check how many articles it returns and read a few abstracts to confirm they are about the process. A query that is too broad fills the pool with sentences that are not about the process, and one that is too narrow misses regulators.
- **Date windows.** You need a **training–validation** dataset and an **application** dataset. A **held-out** dataset (with a gap after the training window, as in the study) is only needed if you want an independent evaluation of the final model.
- **The PMID lists on Zenodo do not apply.** They belong to the chondrogenesis queries. Save your own PMID lists (the `-out` file of `fetchQueryResults.py`) so that your datasets can be reproduced later.
- **Specificity**. You can decide how specific you want to be in your search, it does not need to be as broad as the one given

### 1.2 – 1.6 Parsing, sentence splitting and GNorm2

No changes. Use the same scripts, the same GNorm2 container and the same two GNorm2 setup files. You can tune the setup file but make sure that you use the same files for all of the processing of the text

### 1.7 Concept list

Write a new `concepts.txt` for your process (one term per line). It is used by `filterSentencesGeneConcept.py` to keep only the sentences with at least one gene **and** at least one process term. This file has a large effect on what the model sees, so build it carefully, these are just a few tips:

- Include the process name and its variants (e.g. `osteogenesis`, `osteogenic`, `osteoblast differentiation`, `bone formation`), the main cell types and stages of the process.
- Remember that matching is case-insensitive and on **whole words**, so plurals and other word forms (`osteoblast`, `osteoblasts`) have to be listed separately.

Use the same `concepts.txt` for all of your datasets.

---

## 2. Labelling: Guidelines and App

The labelling workflow (Part 2, step 2.3 of the replication guide) does not change: format for the app, label independently with at least two curators, collect the disagreements, reach a consensus and fuse the files.

### 2.1 Labelling guidelines

The study's rules ([`labelling/AnnotationrulesPerDataset.md`](../labelling/AnnotationrulesPerDataset.md) and the **Rules** tab of the app) are written for chondrogenesis and specifically for our task. Most of the general rules can be kept (the relationship has to be explicit in the text, speculative evidence such as *may* or *might* is not counted, negative evidence is not counted, intermediates of a pathway are not regulators...), but the process-specific ones have to be rewritten. For example, the chondrogenesis guidelines exclude hypertrophy, proliferation-only evidence and cartilage repair. Decide which stages or related processes are inside or outside the scope of your process.

It is recommended to:

- Write a first version of the rules, label a small set of sentences with every curator, discuss the disagreements and update the rules **before** labelling the core set.
- Keep the rules **additive** between iterations, as in the study, and record which rules applied to each labelled set.
- Use an LLM with those rules and use a reasoning variant, that way you can get insides or new addition of rules before setting the rules used for the first iteration/held-out/validation datasets

### 2.2 Labelling app (`labelling_shiny_app.R` and `revision_shiny_app.R`)

**If you only need the same information** (is the gene a regulator: `Yes`/`No`/`Unclear`, plus the type of proof), only the text of the app has to change:

- The questions of the **Label** tab (*"Is the gene directly involved in chondrogenesis?"*, *"What is the proof of the relationship gene-chondrogenesis?"*)
- The **Home** and **Guide** tabs, which describe the task for chondrogenesis
- The **Rules** tab, with the rules and examples of your new guidelines
- The contact email in the **Home** tab

Do the same in `revision_shiny_app.R`, so that the revision shows the same questions and rules.

**If you need more information from the curators** (e.g. the type of regulation, the direction of the regulation, the species or the cell type), the app has to be extended manually (beyond the scope of this guideline) making sure the final results (CSV) is compatible with the rest of the pipeline:

- The model is trained on the **`label` column only**. `appToNLPFormatting.py` maps `Yes` → `1` and `No` → `0`. Any extra column is kept in the labelled files but is **not used by the model** unless you change the training scripts.
- `labellingToRevisionFormatting.py` finds disagreements (and `Unclear` labels) on the **`label` column only**. If the new field must also be agreed on, add it to the comparison, otherwise disagreements on it will not reach the revision.
- If you change the meaning of the label itself (e.g. more than two classes), `appToNLPFormatting.py` and the training and classification scripts (`num_labels = 2`, the loss weights and the BALD scoring) also have to be adapted (beyond the scope of this guideline)

---

## 3. Active Learning and Production Model

Parts 3 and 4 of the replication guide are run the same way, with your own labelled data. The table of settings per iteration (weighted loss, grid search, BALD vs. weighted BALD) is **specific to the study**: it was decided from the validation results of each iteration. For a new process, start with the same defaults as the core model and change the settings based on your own validation results, for example:

- Use the **weighted loss** if the regulators are much rarer than the non-regulators in the training data.
- Use the **weighted BALD** selection if the batches keep selecting mostly non-regulators.
- Stop the loop when the validation performance (mainly AUC-ROC) stops improving between iterations.

The sizes of the core set (150 sentences) and the validation set (500 sentences) can be kept as a starting point, and adjusted to the size of your pool and the time available for labelling.

If what is needed is to change the selection criteria some of the scripts can be re-used but this is a pipeline that has centred to choose from diveristy and uncertainty criteria so changes in this selection will require substantial changes to these steps (beyond the scope of this guide)

---

## 4. Post-processing: GO Terms of Your Process

Steps 6.2 to 6.5 (linking the predictions to their gene metadata and to a single human Entrez ID) are run exactly the same way. The step that changes is the GO coverage. This process filters by human genes, remember that when applying this pipeline to your genes as different species or more than 1 species will require changes in some scipts.

### 4.1 GO term(s) of the process (`coverageAnalysisGOSingleTerm.R`)

Pick the GO Biological Process term that best describes your process, and optionally a broader parent term, and give them to the script instead of the chondrogenesis ones (`GO:0002062` and `GO:0051216`):

```bash
Rscript coverageAnalysisGOSingleTerm.R <GO term of the process> coverage/<process name> \
  application_humanGenes_filtered.csv \
  application_harmonise_inter/genes_withSomeHumanID_unified.csv \
  --parent_go_term=<broader GO term>
```

For example, for osteogenesis, *osteoblast differentiation* (`GO:0001649`) with *ossification* (`GO:0001503`) as the parent term. Browse the terms in [QuickGO](https://www.ebi.ac.uk/QuickGO/) or [AmiGO](https://amigo.geneontology.org/) and check how many human genes are annotated to them.

### 4.2 Other post-processing steps

- **6.7 Coverage of every GO term, 6.8 mentions per gene and 6.9 ORA:** no changes, they are not specific to any process. The all-GO coverage and the ORA are useful to check that the terms most covered or enriched among the regulators are related to your process.
- **`modelALPerformanceAndDatasetCompositionPlot.R`:** the random-selection baseline on Zenodo belongs to the study, so remove it from the figure (or run your own baseline).
