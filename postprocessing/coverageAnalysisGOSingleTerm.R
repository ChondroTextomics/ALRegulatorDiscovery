# coverage analysis
# Generic GO-term coverage analysis: given a GO term (and, optionally, a
# parent/ancestor GO term), reports how well the model's predicted
# regulators cover the genes annotated to that term, and saves all the
# resulting tables and Venn diagrams (as SVG) into an output folder.

suppressPackageStartupMessages({
  library(GO.db)
  library(org.Hs.eg.db)
  library(dplyr)
  library(ggVennDiagram)
  library(ggplot2)
  library(VennDiagram)
})

# Fallback in case the R version in use doesn't provide the base `%||%` (R >= 4.4)
if (!exists("%||%")) {
  `%||%` <- function(x, y) if (is.null(x)) y else x
}

# Arguments ####
args <- commandArgs(trailingOnly = TRUE)

# The following party is to mimic the -h behaviour
usage <- paste(
  "Usage: Rscript coverageAnalysisGOSingleTerm.R <go_term> <output_dir> [--key=value ...]",
  "",
  "Arguments:",
  "  go_term               The GO term to analyse, e.g. GO:0002062 (required)",
  "  output_dir            Folder where all outputs are written, created if it doesn't exist (required)",
  "  final_csv             Path to the filtered/normalised predicted labels CSV",
  "  full_csv              Path to the full gene mention classification CSV, unfiltered",
  "",
  "Optional (given as --key=value, in any order, any subset, the rest keep their default):",
  "  --parent_go_term      An ancestor GO term used for the additional \"drivers found in the",
  "                        broader term\" section (default: none)",
  "",
  "Example:",
  "  Rscript coverageAnalysisGOSingleTerm.R GO:0002062 ./results/chondrocyte_differentiation \\",
  "    ./filteredUniqueGeneClassificationLabel_humanGenes.csv \\",
  "    ./fullGeneMentionClassification_humanGenes.csv",
  "    --parent_go_term=GO:0051216 \\",
  sep = "\n"
)

if (length(args) == 0 || args[1] %in% c("-h", "--help")) {
  cat(usage, "\n")
  quit(status = 0)
}

# now we do the checks of the arguments
if (length(args) < 4) {
  stop(paste(
    "Usage: Rscript coverageAnalysisGOSingleTerm.R <go_term> <output_dir> <final_csv> <full_csv>",
    "[--parent_go_term=X]"
  ), call. = FALSE)
}

go_term    <- args[1]
output_dir <- args[2]
final_csv  <- args[3]
full_csv   <- args[4]

# Everything after the two required positional arguments is optional and given
# as --key=value, so you can supply any subset of them, in any order, and
# leave the rest at their defaults.
optional_args <- args[-c(1, 2, 3, 4)]

valid_keys <- c("parent_go_term")
named_args <- list()

for (arg in optional_args) {
  if (!grepl("^--[A-Za-z_]+=", arg)) {
    stop(sprintf(
      "Unrecognized argument '%s'. Optional arguments must be given as --key=value, e.g. --parent_go_term=GO:0051216",
      arg
    ), call. = FALSE)
  }
  key   <- sub("^--([A-Za-z_]+)=.*$", "\\1", arg)
  value <- sub("^--[A-Za-z_]+=", "", arg)
  if (!(key %in% valid_keys)) {
    stop(sprintf(
      "Unknown argument '--%s'. Valid optional arguments are: %s",
      key, paste(valid_keys, collapse = ", ")
    ), call. = FALSE)
  }
  named_args[[key]] <- value
}

# we put the default values in case they are not given
# this way we can use the same script for different GO terms/inputs
parent_go_term <- named_args[["parent_go_term"]] %||% NULL

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# Lets get the name of the term so we can create the files with specific name
term_info <- AnnotationDbi::select(GO.db,
                                   keys = go_term,
                                   columns = c("TERM", "ONTOLOGY"),
                                   keytype = "GOID")
term_name <- term_info$TERM[1]
term_ontology <- term_info$ONTOLOGY[1]
term_label <- gsub(" ", "_", term_name)

# Get genes in GO ####
# Get all genes annotated to the GO term and its descendants
term_genes <- AnnotationDbi::select(org.Hs.eg.db,
                                    keys = go_term,
                                    columns = c("ENTREZID", "SYMBOL"),
                                    keytype = "GOALL")  # GOALL includes all descendants automatically

term_genes_only_mainGO <- AnnotationDbi::select(org.Hs.eg.db,
                                    keys = go_term,
                                    columns = c("ENTREZID", "SYMBOL"),
                                    keytype = "GO")  # GO will only do that GO term

# There are different evidences so some are duplicated so we need to filtrate
term_entrez <- unique(term_genes$ENTREZID)
term_entrez_mainGO <- unique(term_genes_only_mainGO$ENTREZID)

# Load our predicted labels ####
# We are going to load all of the genes that have been predicted and normalized
# they are not filtered by the ones that we have already labelled
# final is the file with the predicted label and all of the metadata
# already filtered, so it is the set that we want to see the coverage
final <- read.csv(final_csv, header = TRUE)
# full_final_predictions is the whole dataset of predictions of gene mentions
# including the ones that have been filtered (for any reason) as well as any mention and
# classification of the genes
full_final_predictions <- read.csv(full_csv, header = TRUE)
model_regulators <- as.character(final$id_human[final$predicted_label == 1])

# Overlap with GO term ####
# GO and offspring
retrieved <- intersect(model_regulators, term_entrez)
not_retrieved <- setdiff(term_entrez, model_regulators)
not_in_go <- setdiff(model_regulators, term_entrez)


output_lines <- c(
  sprintf("Information %s (%s) and descendants", go_term, term_name),
  sprintf("Total GO genes: %d", length(term_entrez)),
  sprintf("Retrieved by model: %d", length(retrieved)),
  sprintf("Not retrieved: %d", length(not_retrieved)),
  sprintf("Coverage: %f", length(retrieved)/length(term_entrez)*100),
  sprintf("Genes that are not in GO: %d", length(not_in_go))
)

writeLines(output_lines, file.path(output_dir, paste0("information_coverage_", term_label,"_andOffspring", ".txt")))

# GO only
retrieved_mainGO <- intersect(model_regulators, term_entrez_mainGO)
not_retrieved_mainGO <- setdiff(term_entrez_mainGO, model_regulators)
not_in_go_mainGO <- setdiff(model_regulators, term_entrez_mainGO)

output_lines <- c(
  sprintf("Information %s (%s)", go_term, term_name),
  sprintf("Total GO genes (main GO): %d", length(term_entrez_mainGO)),
  sprintf("Retrieved by model (main GO): %d", length(retrieved_mainGO)),
  sprintf("Not retrieved (main GO): %d", length(not_retrieved_mainGO)),
  sprintf("Coverage (main GO): %f", length(retrieved_mainGO)/length(term_entrez_mainGO)*100),
  sprintf("Genes that are not in GO (main GO): %d", length(not_in_go_mainGO))
)

writeLines(output_lines, file.path(output_dir, paste0("information_coverage_", term_label, ".txt")))

# GO term names ####
# get the offspring of the term
offspring_env <- switch(term_ontology,
                         BP = GOBPOFFSPRING,
                         CC = GOCCOFFSPRING,
                         MF = GOMFOFFSPRING,
                         stop(sprintf("Unknown ontology '%s' for %s", term_ontology, go_term)))
offspring <- as.character(offspring_env[[go_term]])
all_terms <- c(go_term, offspring)

go_term_names <- AnnotationDbi::select(GO.db,
                                       keys = all_terms,
                                       columns = "TERM",
                                       keytype = "GOID")

write.csv(go_term_names, file.path(output_dir, paste0("go_terms_offspring_", term_label, ".csv")),
          row.names = FALSE)

# get the children of the term
children_env <- switch(term_ontology,
                        BP = GOBPCHILDREN,
                        CC = GOCCCHILDREN,
                        MF = GOMFCHILDREN,
                        stop(sprintf("Unknown ontology '%s' for %s", term_ontology, go_term)))
children <- as.character(children_env[[go_term]])
all_children <- c(go_term, children)

go_term_names_direct <- AnnotationDbi::select(GO.db,
                                              keys = all_children,
                                              columns = "TERM",
                                              keytype = "GOID")

write.csv(go_term_names_direct, file.path(output_dir, paste0("go_terms_children_", term_label, ".csv")),
          row.names = FALSE)

# Venn diagrams ####
# get the term names for those GO IDs
# GO term and offspring
# 1. Calculate the actual sizes for the Venn diagram
# (VennDiagram requires counts instead of raw lists)
set1 <- unique(model_regulators)
set2 <- unique(term_entrez)
area1 <- length(set1)
area2 <- length(set2)
cross_area <- length(intersect(set1, set2))

# 2. Draw the custom Venn Diagram and save it directly as SVG
svg(file.path(output_dir, paste0("venn_", term_label, "_GOoffspring.svg")), width = 7, height = 7)
grid.newpage() # Clears the canvas
venn_plot <- draw.pairwise.venn(
  area1 = area1,
  area2 = area2,
  cross.area = cross_area,

  # Set Names (Titles for the circles)
  category = c("", ""),

  fill = c("#7F77DD", "#1D9E75"),  # purple = model candidates, teal = GO
  alpha = c(0.5, 0.5),             # High transparency so they blend

  # Border colours matched to each fill (darker shade of the same ramp)
  col = c("#534AB7", "#0F6E56"),   # purple outline, teal outline
  lwd = 2,                         # Border thickness

  # to solve the point of the text not being inside of the venn
  ext.text = FALSE,                # Prevents labels from being pushed outside

  # Numbers inside the diagram (Counts)
  label.col = "black",
  cex = 2.5,                         # Font size of counts (Larger & Bolder)
  fontface = "bold",
  fontfamily = "sans",
)
dev.off()

# GO term main only venn
# 1. Calculate the actual sizes for the Venn diagram
# (VennDiagram requires counts instead of raw lists)
set1_main <- unique(model_regulators)
set2_main <- unique(term_entrez_mainGO)
area1_main <- length(set1_main)
area2_main <- length(set2_main)
cross_area_main <- length(intersect(set1_main, set2_main))

# 2. Draw the custom Venn Diagram and save it directly as SVG ####
svg(file.path(output_dir, paste0("venn_", term_label, "_GOmainOnly.svg")), width = 7, height = 7)
grid.newpage() # Clears the canvas
venn_plot_main <- draw.pairwise.venn(
  area1 = area1_main,
  area2 = area2_main,
  cross.area = cross_area_main,

  # Set Names (Titles for the circles)
  category = c("", ""),

  fill = c("#D55E00","#0072B2"),
  alpha = c(0.6, 0.6),             # High transparency so they blend

  # If you want to force a specific color palette across the areas:
  col = "black",                   # White borders for a clean look
  lwd = 2,                         # Border thickness

  # Numbers inside the diagram (Counts)
  label.col = "black",
  cex = 3,                         # Font size of counts (Larger & Bolder)
  fontface = "bold",
  fontfamily = "sans",
)
dev.off()

# Novel candidates ####
# we are going to do this only for the go+offspring
# Here we basically we are going to look at the ones that are not in GO
# but still they are classified regulators
# Lets get some examples of the genes that are not in go
novel_candidates <- AnnotationDbi::select(org.Hs.eg.db,
                                          keys = not_in_go,
                                          columns = c("ENTREZID", "SYMBOL"),
                                          keytype = "ENTREZID")
# get frequency from full dataset
# how many times is this gene classified as regulators or not
gene_freq <- full_final_predictions %>%
             filter(predicted_label == 1) %>%
             group_by(id_human) %>%
             summarise(sentence_count = n()) %>%
             mutate(id_human = as.character(id_human))

# save the whole frequency so we can plot it
write.csv(gene_freq,
          file.path(output_dir, paste0("frequency_classification_regulators_allNormalisedgenes_", term_label, ".csv")),
          row.names = FALSE)

# merge with novel candidates
novel_candidates <- novel_candidates %>%
                    left_join(gene_freq, by = c("ENTREZID" = "id_human")) %>%
                    arrange(desc(sentence_count))

# save this ones
write.csv(novel_candidates,
          file.path(output_dir, paste0("frequency_classification_regulators_genes_not_in_", term_label, "_andOffspring.csv")),
          row.names = FALSE)

# GO genes not captured ####
# Clean gene summary - one row per gene
not_retrieved_info <- AnnotationDbi::select(org.Hs.eg.db,
                                            keys = not_retrieved,
                                            columns = c("ENTREZID", "SYMBOL", "GENENAME"),
                                            keytype = "ENTREZID")

# Full annotation with GO - one row per gene-GO combination
not_retrieved_full <- AnnotationDbi::select(org.Hs.eg.db,
                                            keys = not_retrieved,
                                            columns = c("ENTREZID", "SYMBOL", "GENENAME", "GO", "ONTOLOGY"),
                                            keytype = "ENTREZID")

# Get GO term names
go_terms <- AnnotationDbi::select(GO.db,
                                  keys = not_retrieved_full$GO,
                                  columns = c("GOID", "TERM"),
                                  keytype = "GOID")

# Merge them so when I get the analysis is easier
not_retrieved_full <- merge(not_retrieved_full, go_terms,
                            by.x = "GO", by.y = "GOID", all.x = TRUE)

not_retrieved_full$EVIDENCE <- NULL
# remove the duplicated because we have some duplicated from the evidence part
not_retrieved_full <- unique(not_retrieved_full)

# save the data
write.csv(not_retrieved_info,
          file.path(output_dir, paste0("genes_not_captured_model_", term_label, "_andOffspring.csv")),
          row.names = FALSE)

write.csv(not_retrieved_full,
          file.path(output_dir, paste0("genes_not_captured_model_full_info_", term_label, "_andOffspring.csv")),
          row.names = FALSE)

# Get the Entrez IDs that are in final but not classified as regulators
ids_in_dataset_non_reg <- final$id_human[final$id_human %in% not_retrieved &
                                           final$predicted_label != 1]

# Filter not_retrieved_info to keep only those genes
not_retrieved_non_regulators <- not_retrieved_info[not_retrieved_info$ENTREZID %in% ids_in_dataset_non_reg, ]

# get the ones that are not in our dataset for manual search
not_retrieved_absent <- not_retrieved_info[!not_retrieved_info$ENTREZID %in% final$id_human, ]

# save them
write.csv(not_retrieved_non_regulators,
          file.path(output_dir, paste0("not_caught_genes_but_in_dataset_as_NONregulators_", term_label, ".csv")),
          row.names = FALSE)

write.csv(not_retrieved_absent,
          file.path(output_dir, paste0("not_caught_genes_not_in_dataset_", term_label, ".csv")),
          row.names = FALSE)

# Now lets get the terms of the genes that were not caught (both for the ones that were not gotten and the ones not caught)
# For the ones classified as non-regulators
non_reg_go <- not_retrieved_full[not_retrieved_full$ENTREZID %in% not_retrieved_non_regulators$ENTREZID &
                                    not_retrieved_full$GO %in% all_terms &
                                    not_retrieved_full$ONTOLOGY == term_ontology, ]

# For the ones absent from the dataset
absent_go <- not_retrieved_full[not_retrieved_full$ENTREZID %in% not_retrieved_absent$ENTREZID &
                                   not_retrieved_full$GO %in% all_terms &
                                   not_retrieved_full$ONTOLOGY == term_ontology, ]

# save the files ####
write.csv(non_reg_go,
          file.path(output_dir, paste0("not_caught_genes_but_in_dataset_as_NONregulators_GOTerms_", term_label, ".csv")),
          row.names = FALSE)
write.csv(absent_go,
          file.path(output_dir, paste0("not_caught_genes_not_in_dataset_GOTerms_", term_label, ".csv")),
          row.names = FALSE)

# finally lets get a count of how many times each term is repeated
go_term_counts_non_regulators <- aggregate(ENTREZID ~ GO + TERM,
                            data = non_reg_go,
                            FUN = function(x) length(unique(x)))
colnames(go_term_counts_non_regulators) <- c("GO", "TERM", "GENE_COUNT")

go_term_counts_absent_regulators <- aggregate(ENTREZID ~ GO + TERM,
                                           data = absent_go,
                                           FUN = function(x) length(unique(x)))
colnames(go_term_counts_absent_regulators) <- c("GO", "TERM", "GENE_COUNT")

# final step, save these last ones
write.csv(go_term_counts_non_regulators,
          file.path(output_dir, paste0("not_caught_genes_but_in_dataset_as_NONregulators_GOTerms_count_", term_label, ".csv")),
          row.names = FALSE)
write.csv(go_term_counts_absent_regulators,
          file.path(output_dir, paste0("not_caught_genes_not_in_dataset_GOTerms_count_", term_label, ".csv")),
          row.names = FALSE)


# drivers that are in a broader/parent GO term ####
# optional: only runs when --parent_go_term is supplied
# e.g. for chondrocyte differentiation, a natural parent would be
# GO:0051216 cartilage development (it would go cartilage development,
# cell differentiation and then chondrocyte differentiation)
if (!is.null(parent_go_term)) {
  parent_term_info <- AnnotationDbi::select(GO.db,
                                            keys = parent_go_term,
                                            columns = "TERM",
                                            keytype = "GOID")
  parent_term_name <- parent_term_info$TERM[1]
  parent_term_label <- gsub(" ", "_", parent_term_name)

  genes_parent_term <- AnnotationDbi::select(org.Hs.eg.db,
                                             keys = parent_go_term,
                                             columns = c("ENTREZID", "SYMBOL"),
                                             keytype = "GOALL")  # GOALL includes all descendants

  unique_parent_genes <- unique(genes_parent_term$ENTREZID)

  genes_parent_term_no_main <- genes_parent_term[
    !genes_parent_term$ENTREZID %in% term_entrez,
  ]

  parent_entrez <- unique(genes_parent_term_no_main$ENTREZID)

  retrieved_parent <- intersect(not_in_go, parent_entrez)

  output_lines <- c(
    sprintf("Information %s (%s) and genes not retrieved with %s and offspring", parent_go_term, parent_term_name, go_term),
    sprintf("Total parent term GO genes: %d", length(unique_parent_genes)),
    sprintf("Total parent term GO genes without %s: %d", go_term, length(parent_entrez)),
    sprintf("Retrieved by model as drivers but not in GO %s: %d", go_term, length(not_in_go)),
    sprintf("Retrieved by model as drivers but not in GO %s but in %s: %d",go_term, parent_go_term, length(retrieved_parent))
  )

writeLines(output_lines, file.path(output_dir, paste0("information_coverage_", parent_term_label, ".txt")))

  info_retrieved_parent <- genes_parent_term[genes_parent_term$ENTREZID %in% retrieved_parent, ]

  write.csv(info_retrieved_parent,
            file.path(output_dir, paste0("drivers_in_", parent_term_name, "_not_in_", term_label, ".csv")),
            row.names = FALSE)
}
