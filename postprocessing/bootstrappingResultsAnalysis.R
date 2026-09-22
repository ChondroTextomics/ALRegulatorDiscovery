# Script to read a folder of bootstrapped result CSVs and compute
# per-file performance metrics, plus overall mean/sd across bootstraps.


suppressPackageStartupMessages({
  library(MLmetrics)
  library(tidyverse)
  library(tidytable)
})


# Arguments ####
args <- commandArgs(trailingOnly = TRUE)

# The following party is to mimic the -h behaviour
usage <- paste(
  "Usage: Rscript process_bootstrap.R <input_folder> <output_file> [--key=value ...]",
  "",
  "Arguments:",
  "  input_folder          Path to folder containing bootstrap CSV files (required)",
  "  output_file           Path to output CSV file for per-file metrics (required)",
  "",
  "Optional (given as --key=value, in any order, any subset, the rest keep their default):",
  "  --true_label_col      Column name for true labels (default: labels)",
  "  --predicted_label_col Column name for predicted labels (default: predicted_label)",
  "  --positive_label      Value of the positive class (default: 1)",
  "  --prob_col            Column name for predicted probabilities (default: prob_1)",
  "  --summary_file        Optional path for mean/sd summary CSV",
  "",
  "Example (only setting the summary file, everything else stays default):",
  "  Rscript process_bootstrap.R ./data ./out.csv --summary_file=./summary.csv",
  "",
  "Example (setting a few options):",
  "  Rscript process_bootstrap.R ./data ./out.csv --positive_label=1 --prob_col=prob_1 --summary_file=./summary.csv",
  sep = "\n"
)

if (length(args) == 0 || args[1] %in% c("-h", "--help")) {
  cat(usage, "\n")
  quit(status = 0)
}

# now we do the checks of the arguments
if (length(args) < 2) {
  stop(paste(
    "Usage: Rscript process_bootstrap.R <input_folder> <output_file>",
    "[--true_label_col=X] [--predicted_label_col=X] [--positive_label=X] [--prob_col=X] [--summary_file=X]"
  ), call. = FALSE)
}

input_folder <- args[1]
output_file  <- args[2]

# Everything after the two required positional arguments is optional and given
# as --key=value, so you can supply any subset of them, in any order, and
# leave the rest at their defaults.
optional_args <- args[-c(1, 2)]

valid_keys <- c("true_label_col", "predicted_label_col", "positive_label", "prob_col", "summary_file")
named_args <- list()

for (arg in optional_args) {
  if (!grepl("^--[A-Za-z_]+=", arg)) {
    stop(sprintf(
      "Unrecognized argument '%s'. Optional arguments must be given as --key=value, e.g. --summary_file=./summary.csv",
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
# this way we can use the same script for different models
true_label_col      <- named_args[["true_label_col"]]      %||% "labels"
predicted_label_col <- named_args[["predicted_label_col"]] %||% "predicted_label"
positive_label       <- named_args[["positive_label"]]      %||% "1"
prob_col             <- named_args[["prob_col"]]            %||% "prob_1"
summary_file         <- named_args[["summary_file"]]        %||% NULL

if (!dir.exists(input_folder)) {
  stop(sprintf("Input folder does not exist: %s", input_folder), call. = FALSE)
}


# Function to process the files (individually) ####
process_boot_file <- function(file_name, true_col, pred_col, positive, prob_column){
  data <- read.csv(file_name)
  
  # Check required columns exist
  required_cols <- c(true_col, pred_col, prob_column)
  missing_cols <- setdiff(required_cols, colnames(data))
  if (length(missing_cols) > 0) {
    stop(sprintf(
      "File '%s' is missing required column(s): %s",
      basename(file_name), paste(missing_cols, collapse = ", ")
    ), call. = FALSE)
  }

  # set the correct values
  y_true <- data[[true_col]]
  y_pred <- data[[pred_col]]
  y_prob <- data[[prob_column]]

  # Check that the positive label actually occurs in the true/predicted columns
  observed_values <- unique(c(y_true, y_pred))
  if (!(positive %in% as.character(observed_values))) {
    stop(sprintf(
      "File '%s': positive label '%s' not found in columns '%s'/'%s'. Observed values: %s",
      basename(file_name), positive, true_col, pred_col,
      paste(sort(unique(as.character(observed_values))), collapse = ", ")
    ), call. = FALSE)
  }

  # Ensure labels are factors with the same levels so the metric functions work correctly
  all_levels <- sort(observed_values)
  y_true <- factor(y_true, levels = all_levels)
  y_pred <- factor(y_pred, levels = all_levels)
  
  
  # Get metrics
  # f1
  f1 <- F1_Score(y_true = y_true, y_pred = y_pred, positive = positive)
  # accuracy
  acc <- Accuracy(y_pred = y_pred, y_true = y_true)
  # area under the roc curve
  auc_roc <- AUC(y_pred = y_prob, y_true = y_true)
  # precision
  prec <- Precision(y_true = y_true, y_pred = y_pred, positive = positive)
  # recall
  rec <- Recall(y_true = y_true, y_pred = y_pred, positive = positive)
  
  # combine teh results, we can add more if we want in the future
  combined <- tibble(
    file_name = basename(file_name),
    f1 = f1,
    accuracy = acc,
    auc_roc = auc_roc,
    precision = prec,
    recall = rec
  )
  
  return (combined)
}


# Path of the bootstrapping folder
# We get all the files
file_list <- list.files(path = input_folder,
                        pattern = "*.csv",
                        full.names = TRUE)

if (length(file_list) == 0) {
  stop(sprintf("No CSV files found in folder: %s", input_folder), call. = FALSE)
}

message(sprintf("Found %d CSV file(s) in %s", length(file_list), input_folder))
message(sprintf(
  "Using true_label_col='%s', predicted_label_col='%s', positive_label='%s', prob_col='%s'",
  true_label_col, predicted_label_col, positive_label, prob_col
))

# process the files with our function
final_results <- map_df(
  file_list,
  process_boot_file,
  true_col = true_label_col,
  pred_col = predicted_label_col,
  positive = positive_label,
  prob_column = prob_col
)

# save the file
write.csv(final_results, output_file, row.names = FALSE)
message(sprintf("Per-file metrics written to: %s", output_file))


# if summary is given, we write that file as well
if (!is.null(summary_file)) {
  summary_results <- final_results %>%
    summarise(
      across(
        c(f1, accuracy, auc_roc, precision, recall),
        list(mean = ~mean(.x, na.rm = TRUE), sd = ~sd(.x, na.rm = TRUE)),
        .names = "{.col}_{.fn}"
      )
    )
  write.csv(summary_results, summary_file, row.names = FALSE)
  message(sprintf("Summary (mean/sd) written to: %s", summary_file))
}