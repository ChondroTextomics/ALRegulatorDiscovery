# Script meant to get the weights of samples based on their probability of
# the predicted calss being 1 (positive and minority case in our problem)

if (!requireNamespace(c("optparse"), quietly = TRUE))
  install.packages(c("optparse"))

suppressPackageStartupMessages(suppressWarnings(library(optparse)))

# Arguments ####
option_list <- list(
  make_option(c("-i", "--input"),
              metavar = "INPUTFILE",
              help = "path to the file with the prediction probability for samples",
              default = NULL),
  make_option(c("-o", "--output"),
              metavar = "OUTPUTFILE",
              help = "path to the file where the dataframe with the weights will be stored",
              default = NULL),
  make_option(c("-c", "--probabilityColumn"),
              metavar = "PROBCOLUMN",
              help = "name of the column that contains the probability that is goign to define the weights, default 'prob_1'",
              default = "prob_1")
)
parser <- OptionParser(option_list=option_list)
args <- parse_args(parser)

# checking arguments ####
# Check that at least the minimums are required
required_args <- c("input", "output")

for (arg in required_args) {
  if (is.null(args[[arg]])) {
    stop(paste0("--", arg, " is required. Use --help for usage information."))
  }
}

# Check the existence of the file
if (file.exists(args$input)){
  preds <- read.csv(args$input)
  # Check that the probability column is in the data
  if (!args$probabilityColumn %in% names(preds)){
    stop(paste0("Column '",args$probabilityColumn,"' needs to be in the file given in the argument --input"))
  }
} else {
  stop(paste0("File ", args$input, " cannot be found"))
}

# Lets check that the column provided is numeric
if (!is.numeric(preds[[args$probabilityColumn]]) || any(preds[[args$probabilityColumn]] < 0 | preds[[args$probabilityColumn]] > 1)){
  stop(paste0("Column '",args$probabilityColumn,"' is either not numeric or the values are outside the range [0, 1]. We need a column of probabilities"))
}

# Lets get the weights ####
# Create the vector of the different probabilities cuts

prob_cuts <- seq(0, 1, 0.1) # We will have a break for every 0.1

density <- cut(preds[[args$probabilityColumn]],
               breaks = prob_cuts,
               include.lowest = TRUE) # To include the 0 in the first range

# Add the density column to preds dataframe
preds$prob_int <- density

a <- as.data.frame(table(density))

# calculate the weights which is the inverse of the propensity
a$weight <- 1/a$Fre
# Change it to a 1 but it doesn't matter because we will never use that one
a$weight[is.infinite(a$weight)] <- 1

preds$weights <- 0

for (class in a$density){
  preds[preds$prob_int == class, "weights"] <- a[a$density == class, "weight"]
}


# Now we export the dataframe of predictions ####
write.csv(preds,
          args$output,
          row.names = FALSE)