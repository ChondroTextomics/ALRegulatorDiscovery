## Data Availability

The datasets, model outputs, and benchmarking results accompanying this paper and 
codebase are archived on Zenodo:

[**Zenodo link**](https://zenodo.org/records/22746090?preview=1&token=eyJhbGciOiJIUzUxMiJ9.eyJpZCI6ImRlMTNmZGNkLTc3NjYtNDhmYi1hZGE0LWRhMGVlMGI3YzQ3YyIsImRhdGEiOnt9LCJyYW5kb20iOiJiOGRiYTE5YTc3NmE2ZmE1NGFiODVmOGY0ZGQzNzA4MiJ9.UKwy_pn47uGgdP3wcYmKm9JvgRLTMkhkxmeX9NdtBlSoRpd6DwlnkK4xTuRKU9lyXoj0AtwvuX20NvAC8fxYsw) _this is a provisional link until the dataset is published_

**This includes:**
- Active learning annotation rounds (training and results, including the matched 
  random-sampling baseline) — `alLoopIterations/`
- Annotation files for the different curators - `annotationFiles/`
- PMIDs used to construct the different data — `pubMedDataExtraction/`
- Held out results of all modelse — `LLMs/`, `logisticRegressionClassificationHeldOut.csv`, `alLoopIterations`
- Production model gene classification outputs and GO coverage analysis — 
  `modelPubMedGeneExtractionResults/`
