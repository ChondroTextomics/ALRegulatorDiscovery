suppressWarnings(suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
}))

usage <- function() {
  cat(
"Usage: Rscript labelClassificationGeneMentions.R <input_csv> <output_csv>

Counts, for each human gene ID, how many of its mentions the model assigned
to each predicted label.

Arguments:
  input_csv    CSV with the full list of gene mentions classified by the model.
               Must contain the columns 'id_human' and 'predicted_label'.
  output_csv   Path where the per-ID label count table will be written.

Options:
  -h, --help   Show this help message and exit.
")
}

args <- commandArgs(trailingOnly = TRUE)

if (any(args %in% c("-h", "--help"))) {
  usage()
  quit(status = 0)
}

if (length(args) != 2) {
  cat("Error: expected 2 arguments, got ", length(args), ".\n\n", sep = "")
  usage()
  quit(status = 1)
}

input_file  <- args[1]
output_file <- args[2]

if (!file.exists(input_file)) {
  stop("Input file does not exist: ", input_file, call. = FALSE)
}
if (!file_test("-f", input_file)) {
  stop("Input path is a directory, not a file: ", input_file, call. = FALSE)
}
if (file.size(input_file) == 0) {
  stop("Input file is empty: ", input_file, call. = FALSE)
}

if (dir.exists(output_file)) {
  stop("Output path is a directory, not a file: ", output_file, call. = FALSE)
}
output_dir <- dirname(output_file)
if (!dir.exists(output_dir)) {
  stop("Output directory does not exist: ", output_dir, call. = FALSE)
}

full_final_predictions <- tryCatch(
  read.csv(input_file, header = TRUE),
  error = function(e) {
    stop("Could not read input file '", input_file, "': ",
         conditionMessage(e), call. = FALSE)
  }
)

required_cols <- c("id_human", "predicted_label")
missing_cols <- setdiff(required_cols, colnames(full_final_predictions))
if (length(missing_cols) > 0) {
  stop("Input file is missing required column(s): ",
       paste(missing_cols, collapse = ", "), call. = FALSE)
}

if (nrow(full_final_predictions) == 0) {
  stop("Input file has a header but no gene mentions: ", input_file,
       call. = FALSE)
}

# Count occurrences of each predicted_label for each id_human
result <- full_final_predictions %>%
  group_by(id_human, predicted_label) %>%
  summarise(count = n(), .groups = "drop") %>%
  pivot_wider(
    names_from = predicted_label,
    values_from = count,
    values_fill = 0,
    names_prefix = "label_"
  )


write.csv(result, output_file)
