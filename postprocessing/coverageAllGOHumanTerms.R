#   For every GO Biological Process (BP) term that has at least one human gene
#   annotated to it, compute how many of that term's genes were retrieved by
#   our model (genes with predicted_label == 1). This shows which biological
#   processes are well covered by the model's predictions and which are not.

#   There are too many GO terms to run in one go (a single run failed), so the
#   script is run in batches of row indices of the human BP term table.
#   Run from the terminal, as it takes a long time:
#
#   The batch CSVs can then be combined afterwards.

# Help message ####
help_message <- "
Usage: Rscript coverageAllGOHumanTerms.R <init_batch> <fin_batch> <predictions_csv> <output_dir>

Computes, for each human GO Biological Process term in rows
init_batch..fin_batch of the human BP term table, how many of its genes
were retrieved by the model (predicted_label == 1).

Arguments:
  init_batch       First row index of the human BP term table (integer >= 1)
  fin_batch        Last row index (integer >= init_batch; capped at the number of terms)
  predictions_csv  CSV with the model predictions; must contain the columns
                   'id_human' (Entrez ID) and 'predicted_label'
  output_dir       Existing folder where the coverage CSV will be written

Options:
  -h, --help       Show this help message and exit

Output:
  <output_dir>/coverage_allGO_terms_human_<init_batch>_<fin_batch>.csv

Example:
  Rscript coverageAllGOHumanTerms.R 1 1000 predictions.csv results/
"

# get the arguments
# (parsed before loading the packages so -h/--help answers straight away)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0 || any(args %in% c("-h", "--help"))) {
  cat(help_message)
  quit(save = "no", status = 0)
}
if (length(args) < 4) {
  cat(help_message)
  stop("Expected 4 arguments, got ", length(args))
}
init_batch <- as.integer(args[1]) # first index of the coverage
fin_batch <- as.integer(args[2]) # final index of the coverage
predictions_csv <- args[3] # csv with the predicted labels of the model
output_dir <- args[4] # folder where the coverage csv will be saved

# check the arguments before doing anything slow
if (is.na(init_batch) || is.na(fin_batch) || init_batch < 1 || fin_batch < init_batch) {
  stop("init_batch and fin_batch must be integers with 1 <= init_batch <= fin_batch")
}
if (!file.exists(predictions_csv)) {
  stop("Predictions file does not exist: ", predictions_csv)
}
if (!dir.exists(output_dir)) {
  stop("Output folder does not exist: ", output_dir)
}

# Packages ####
library(GO.db) # v 3.22.0
library(org.Hs.eg.db)
library(dbplyr)

# Load our predicted labels ####
# We are going to load all of the genes that have been predicted and normalized
# they are not filtered by the ones that we have already labelled
final <- read.csv(predictions_csv, header = TRUE)

# the file needs the human Entrez ID and the predicted label of each gene
required_cols <- c("id_human", "predicted_label")
missing_cols <- setdiff(required_cols, colnames(final))
if (length(missing_cols) > 0) {
  stop("Predictions file is missing the column(s): ", paste(missing_cols, collapse = ", "))
}

model_regulators <- as.character(final$id_human[final$predicted_label == 1])

# Function to get the coverage ####
coverage_analysis <- function(go_term, regulators){
  print(go_term)

  # This is what we are doing in coverage_analysis scripts
  # Get all genes annotated to that term
  # if one term fails we skip it (returning NULL) so we don't lose the whole batch
  go_term_genes <- tryCatch(
    AnnotationDbi::select(org.Hs.eg.db,
                          keys = go_term,
                          columns = c("ENTREZID", "SYMBOL"),
                          keytype = "GOALL"),  # GOALL includes all descendants automatically
    error = function(e){
      message("Skipping ", go_term, ": ", conditionMessage(e))
      NULL
    })
  if (is.null(go_term_genes)) return(NULL)

  # There are different evidences so some are duplicated so we need to filtrate
  go_term_entrez <- unique(go_term_genes$ENTREZID)
  
  retrieved <- intersect(regulators, go_term_entrez)
  not_retrieved <- setdiff(go_term_entrez, regulators)
  not_in_go <- setdiff(regulators, go_term_entrez)
  
  results_coverage <- data.frame(GOID = go_term,
                                 TotalGenesGOTerm = length(go_term_entrez),
                                 GOGenesRetrievedByModel = length(retrieved),
                                 GOGenesNotRetrievedByModel = length(not_retrieved),
                                 CoverageGOTerm = length(retrieved)/length(go_term_entrez)*100,
                                 GenesModelNotInGO = length(not_in_go)
  )
  
  return(results_coverage)
}

# Get all GO terms ####
all_go_terms <- as.list(GOTERM)
# This mapping, because of the 3.22 version is from the dat 2025-07-22 (this date is from their manual)
# Even if it doesnt look like it in the manual, the terms that GOTERM returns
# are all active ones, they are not obsolete

# if you check this list you will see that the terms
# that are in this list are not in the all_go_terms
all_obsolete_list <- as.list(GOOBSOLETE)
# acccording to the manual the obsolete terms are in
# GO:0008369 (for MF), GO:0008370 (for CC) and GO:0008371 (for BO)

BP_go_terms <- Filter(
  function(x){x@Ontology =="BP"},
  all_go_terms)

# so now we have only the BP processes but we need a list of the ID so
# we can do the coverage of each one of them
bp_ids <- sapply(BP_go_terms, GOID , simplify = TRUE)
bp_terms <- sapply(BP_go_terms, Term)

dataframe_bp_terms <- data.frame(
  GOID = bp_ids,
  Term = bp_terms,
  row.names = NULL,
  stringsAsFactors = FALSE
)

# Get only the valid go terms for human because if we preserve everything
# the Annotation command will give an error
valid_keys_human <- keys(org.Hs.eg.db, keytype = "GOALL") # this will include all CC, BP and MF

dataframe_bp_terms_human <- dataframe_bp_terms[dataframe_bp_terms$GOID %in% valid_keys_human,]
# we wont get the whole valid_keys_human because, as said before, it not only includes BP but other

# make sure the batch does not go beyond the number of terms, if not we get NA GO IDs
message("Total human BP terms: ", nrow(dataframe_bp_terms_human))
if (init_batch > nrow(dataframe_bp_terms_human)) {
  stop("init_batch is larger than the number of human BP terms")
}
fin_batch <- min(fin_batch, nrow(dataframe_bp_terms_human))

# Apply the coevrage to all of the GO BP terms ####
# we need to establish that is with dplyr because if not, it doesnt find the function
coverage_df <- dplyr::bind_rows(lapply(dataframe_bp_terms_human$GOID[init_batch:fin_batch], 
                                coverage_analysis,
                                regulators = model_regulators))

coverage_df_info <- merge(coverage_df, dataframe_bp_terms_human[init_batch:fin_batch, ],
                          by = "GOID")

write.csv(coverage_df_info,
          file.path(output_dir,
                    paste0("coverage_allGO_terms_human_", init_batch, "_", fin_batch, ".csv")),
          row.names = FALSE)
