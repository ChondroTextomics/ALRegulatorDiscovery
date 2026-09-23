# Script to create the AL performance increase in the iterations
# this is for the plot that will go into the IPAP report

library(MLmetrics)
library(tidyverse)   # includes ggplot2, dplyr, tidyr
library(patchwork)
library(ggh4x)

# Functions ####
process_results_file <- function(file_name, name_plot){
  data <- read.csv(file_name)
  
  # Ensure labels are factors with correct levels
  data$labels <- factor(data$labels, levels = c(0, 1))
  data$predicted_label <- factor(data$predicted_label, levels = c(0, 1))
  
  
  # Get metrics
  # f1
  f1 <- F1_Score(y_true = data$labels, y_pred = data$predicted_label, positive = "1")
  # auc-roc
  auc_roc <- AUC(y_pred = data$prob_1, y_true = data$labels)
  # precision
  prec <- Precision(y_true = data$labels, y_pred = data$predicted_label, positive = "1")
  # recall
  rec <- Recall(y_true = data$labels, y_pred = data$predicted_label, positive = "1")
  
  # combine the results, we can add more if we want in the future
  combined <- tibble(
    data_training = name_plot,
    f1 = f1,
    auc_roc = auc_roc,
    precision = prec,
    recall = rec
  )
  
  return (combined)
}


# AL results ####
setwd("AL-entity/results")
iter0 <- process_results_file("13_testPredictions_iter1.csv", "Core")
iter1 <- process_results_file("30_testPredictions_iter2.csv", "Iter 1")
iter2_w <- process_results_file("28_testPredictions_iter3.csv", "Iter 2")
iter3 <- process_results_file("5_testPredictions_iter4.csv", "Iter 3")
iter4 <- process_results_file("12_testPredictions_iter5.csv", "Iter 4")
iter5_ht <- process_results_file("9_testPredictions_iter6_ht.csv", "Iter 5")
iter6_ht <- process_results_file("7_testPredictions_iter7_own_ht.csv", "Iter 6")

iter6_held_out <- process_results_file(held-out-dataset-resulst-iter6.csv", "Iter 6 (held out)")

# need to change the value of the data_training column to be able to put it in the plot
iter6_held_out[1, "data_training"] <- "Iter 6"
iter6_heldout_long <- pivot_longer(iter6_held_out,
                                   cols = c("f1","auc_roc","precision","recall"),
                                   names_to = "Metric",
                                   values_to = "Value")


fused_results <- rbind(iter0, iter1, iter2_w, iter3, iter4, iter5_ht, iter6_ht)
fused_results[is.na(fused_results)] <- 0

# Lets reshape the dataframe so we can plot it with ggplot
fused_results_long <- fused_results %>%
                      pivot_longer(
                        cols = -data_training,
                        names_to = "Metric",
                        values_to = "Value"
                      )


# AL Plot ####
al_performance_loop <- ggplot() +
  # Use lines and points for clarity
  
  geom_line(data = fused_results_long,
            mapping = aes(x = data_training, y = Value, color = Metric, group = Metric),
            linewidth = 2.5,
            alpha = 0.8) +
  geom_point(data = fused_results_long,
             mapping = aes(x = data_training, y = Value, color = Metric, group = Metric, shape = "Validation"),
             size = 4) +
  
  # add the held-out dataset metrics
  geom_point(data = iter6_heldout_long,
             aes(x = data_training, y = Value, color = Metric, shape = "Held-out"),
             size = 6,       # Slightly larger so the cross stands out clearly
             stroke = 2,      # Makes the cross lines thicker and bolder)
             position = position_nudge(x = 0.15) # Nudges points 0.1 units to the right
  ) +

  scale_color_manual(
    values = c("auc_roc" = "#332288", "f1" = "#CC6677", "precision" = "#882255", "recall" = "#999933"),
    labels = c("auc_roc" = "AUC-ROC", "f1" = "F1", "precision" = "Precision", "recall" = "Recall")
  ) +
  
  # Shape scale for the held-out legend
  scale_shape_manual(
    name = "Dataset",                   # Removes the legend header for shape, or set to e.g. "Dataset"
    values = c("Held-out" = 4, "Validation" = 16), # 4 = Cross shape, 20 = circles
  ) +
  
  # Set Y limits from 0 to 1
  scale_y_continuous(limits = c(0, 1), expand = c(0, 0.03)) +
  
  # separate the lengends
  guides(
    color = guide_legend(
      order = 1,
      override.aes = list(shape = 16, size = 5, linetype = "blank") # solid dots, no line sample
    ),
    shape = guide_legend(
      order = 2,
      override.aes = list(color = "black", size = 5, stroke = 1.5)
    ),
    linetype = guide_legend(
      order = 3,
      override.aes = list(color = "black", linewidth = 1) # neutral black in the linetype key
    )
  ) +
  
  # Labels and Titles
  labs(
    #title = "Active Learning Loop Performances Through the Iterations",
    x = NULL,                    # Makes the X-axis title blank
    y = "Performance Score",
    color = "Metric"             # Legend title
  ) +
  
  # Scientific Theme Styling
  theme_bw() +                   # Start with a clean white background
  theme(
    # Make the background and grid lines completely blank
    panel.grid.major = element_blank(), 
    panel.grid.minor = element_blank(),
    panel.border = element_blank(),
    axis.line = element_line(color = "black", linewidth = 0.8),
    
    # Global Text Boldness and Size
    text = element_text(size = 20), # Base size for all text
    
    # Rotate X-axis tick text
    axis.text.x = element_text(size = 20, color = "black"),
    axis.text.y = element_text(size = 20, color = "black"),
    axis.title.y = element_text(size = 24, margin = margin(r = 15), face = "bold"),
    
    # Legend formatting
    legend.position = "right",
    legend.box = "vertical", # legends side-by-side
    legend.title = element_text(size = 24, face = "bold"),
    legend.text = element_text(size = 20),
    legend.key = element_blank() # Removes grey boxes behind legend lines
  )

al_performance_loop

# barplot data counts ####

counts <- read.csv("sentence_gene_number_al_loop.csv")

counts_total <- counts[c("iteration","sentence","gene")]
counts_long <- pivot_longer(
  counts_total,
  cols=-iteration,
  names_to = "Level",
  values_to = "Counts"
)

counts_level <- counts[c("iteration","sentence", "driver", "non.driver")]
counts_level_long <- counts_level %>%
  pivot_longer(cols = c(sentence, driver, non.driver),
               names_to = "category",
               values_to = "count") %>%
  mutate(
    bar_type = if_else(category == "sentence", "sentence", "gene")
  )

counts_level_long_plot <- counts_level_long %>%
  mutate(
    x_num = as.numeric(as.factor(iteration)),
    x_pos = x_num + if_else(bar_type == "gene", -0.2, 0.2)
  )

driver_labels <- counts_level_long_plot %>%
  group_by(x_pos, x_num, iteration) %>%
  mutate(total = sum(count)) %>%
  filter(category == "driver") %>%
  mutate(pct_driver = round(count / total * 100, 1),
         label = paste0(pct_driver, "%"))

plot_Data_counts_separeted_gene_counts_percentages <- ggplot(counts_level_long_plot, aes(x = x_pos, y = count, fill = category)) +
  geom_col(position = "stack", width = 0.35) +
  geom_text(
    data = driver_labels,
    aes(x = x_pos, y = total, label = label),
    inherit.aes = FALSE,
    vjust = -0.5,
    size = 6,
    fontface = "bold",
    color = "#009E73"
  ) +
  scale_x_continuous(breaks = unique(counts_level_long_plot$x_num),
                     labels = unique(counts_level_long_plot$iteration)) +
  labs(y = "Counts") +
  theme_bw() +
  theme(
    panel.grid.major = element_blank(), 
    panel.grid.minor = element_blank(),
    panel.border = element_blank(),
    axis.line = element_line(color = "black", linewidth = 0.8),
    text = element_text(size = 20),
    axis.text.x = element_text(size = 20, color = "black"),
    axis.text.y = element_text(size = 20, color = "black"),
    axis.title.y = element_text(size = 24, face = "bold"),
    axis.title.x = element_blank(),
    legend.position = "right",
    legend.box = "vertical",
    legend.title = element_text(size = 24, face = "bold"),
    legend.text = element_text(size = 20),
    legend.key = element_blank()
  ) +
  scale_fill_manual(
    values = c("driver" = "#009E73", "non.driver" = "#0072B2", "sentence" = "#E69F00"),
    labels = c("driver" = "Driver", "non.driver" = "Non-Driver", "sentence" = "Sentence"),
    name = NULL
  )+
  scale_y_continuous(expand = expansion(mult = c(0, 0.18)))

plot_Data_counts_separeted_gene_counts_percentages

# Combined  plot

(al_performance_loop / plot_Data_counts_separeted_gene_counts_percentages) +
  plot_layout(heights = c(3, 1), guides = "collect") &
  theme(plot.margin = margin(2, 5, 2, 5))

# check it is colourblind
# I checked it in
# https://www.color-blindness.com/coblis-color-blindness-simulator

# al plot only aucroc with baseline ####
# some pre processing now that we are only going to plot aucroc
fused_auc <- fused_results_long[fused_results_long$Metric == "auc_roc", ]
fused_auc$Series <- "Active Learning"

heldout_auc <- iter6_heldout_long[iter6_heldout_long$Metric == "auc_roc", ]
heldout_auc$Series <- "Active Learning"


# adding random baseline to the metrics ####
# this is for the supplementary material

seed_3 <- read.csv("summary_performances_random_seed_3_replicas.csv")
seed_6 <- read.csv("summary_performances_random_seed_6_replicas.csv")
seed_8 <- read.csv("summary_performances_random_seed_8_replicas.csv")
seed_11 <- read.csv("summary_performances_random_seed_11_replicas.csv")
seed_26 <- read.csv("summary_performances_random_seed_26_replicas.csv")
seed_30 <- read.csv("summary_performances_random_seed_30_replicas.csv")

performance_seeds <- list("3" = seed_3,
                          "6" = seed_6,
                          "8" = seed_8,
                          "11" = seed_11,
                          "26" = seed_26,
                          "30" = seed_30)

all_seeds <- data.frame()

replica_equivalent <- c("0" = "Core",
                        "1" = "Iter 1",
                        "2" = "Iter 2",
                        "3" = "Iter 3",
                        "4" = "Iter 4",
                        "5" = "Iter 5",
                        "6" = "Iter 6")

for (seed_name in names(performance_seeds)) {
  print(seed_name)
  df <- performance_seeds[[seed_name]]
  
  # we need to remove the file name where the results are coming from 
  df$replica <- sub(".*replica_([0-9]+).*", "\\1", df$replica)
  df$replica <- replica_equivalent[df$replica]
  print(df)
  
  # append the seed
  df$seed <- as.numeric(seed_name)
  
  # append to results
  all_seeds <- rbind(all_seeds, df)
}

all_seeds_long <- all_seeds %>%
  pivot_longer(
    cols = c(auc_roc, f1, precision, recall),
    names_to = "Metric",
    values_to = "Value"
  )

# we need to have the same column name as fused_results_long
all_seeds_long <- all_seeds_long %>%
  rename(data_training = replica)

ci_df <- all_seeds_long %>%
  dplyr::group_by(data_training, Metric) %>%
  dplyr::summarise(
    mean_val = mean(Value, na.rm = TRUE),
    sd_val   = sd(Value, na.rm = TRUE),
    n        = dplyr::n(),            # = 6 in our case now
    se_val   = sd_val / sqrt(n),
    t_crit   = qt(0.975, df = n - 1),
    ci_lower = mean_val - t_crit * se_val,
    ci_upper = mean_val + t_crit * se_val,
    .groups = "drop"
  )

# lets do the plot now per metric

make_metric_plot <- function(metric_name, metric_label) {
  ggplot() +
    geom_ribbon(data = filter(ci_df, Metric == metric_name), 
                aes(x = data_training, ymin = ci_lower, ymax = ci_upper, group = 1,
                    fill = "Random Selection"),
                alpha = 0.2) +
    geom_line(data = filter(ci_df, Metric == metric_name), 
              aes(x = data_training, y = mean_val, group = 1, color = "Random Selection"),
              linewidth = 1.5, linetype = "longdash") +
    geom_line(data = filter(fused_results_long, Metric == metric_name), 
              aes(x = data_training, y = Value, group = 1, color = "Active Learning"),
              linewidth = 1.5) +
    geom_point(data = filter(fused_results_long, Metric == metric_name), 
               aes(x = data_training, y = Value, color = "Active Learning"),
               size = 3.5) +
    scale_color_manual(values = c("Random Selection" = "#E69F00",
                                   "Active Learning"  = "#0072B2")) +
    scale_fill_manual(values = c("Random Selection" = "#E69F00"), guide = "none") +
    labs(x = NULL, y = "Performance Score", color = NULL, title = metric_label) +
    theme_bw() +
    theme(
      panel.grid.major = element_blank(),
      panel.grid.minor = element_blank(),
      panel.border = element_blank(),
      axis.line = element_line(color = "black", linewidth = 0.8),
      text = element_text(size = 20),
      axis.text.x = element_text(size = 20, color = "black"),
      axis.text.y = element_text(size = 20, color = "black"),
      axis.title.y = element_text(size = 24, margin = margin(r = 15), face = "bold"),
      plot.title = element_text(size = 22, face = "bold", hjust = 0.5),
      legend.position = "bottom",
      legend.title = element_text(size = 24, face = "bold"),
      legend.text = element_text(size = 20),
      legend.key = element_blank()
    )
}

metric_labels <- c(
  auc_roc   = "AUC-ROC",
  f1        = "F1",
  precision = "Precision",
  recall    = "Recall"
)

plots <- lapply(names(metric_labels),
                function(m) make_metric_plot(m, metric_labels[[m]]))

plots

final_plot_baseline_comparison <- wrap_plots(plots, ncol = 2) +
                                  plot_layout(guides = "collect") +
  plot_annotation(
    tag_levels = 'a',
    tag_prefix = '',
    tag_suffix = ')'
  ) &
  theme(
    legend.position = "bottom",
    plot.tag = element_text(size = 22, face = "bold") # Formats tags
  )

final_plot_baseline_comparison

# boxplots for random baseline and AL proportion of genes ####
count_genes_random <- read.csv("baseline_random_gene_composition_trainingDataset.csv")
count_genes_random <- count_genes_random %>%
  rename(data_training = replica)
count_genes_random$data_training <- replica_equivalent[as.character(count_genes_random$data_training)]

# we have done some restructuring and loading the data, not we need to treat the data for the plot
# get percentages
plot_data <- count_genes_random %>%
  mutate(
    total = driver + non_driver,
    driver_pct = 100 * driver / total,
    non_driver_pct = 100 * non_driver / total
  )

# filter teh columns of interes
plot_data <- plot_data %>%
  select(data_training, seed, driver_pct, non_driver_pct) %>%
  pivot_longer(
    cols = c(driver_pct, non_driver_pct),
    names_to = "class",
    values_to = "percentage"
  )

# just change the name of the values so later it looks better in the plot
plot_data_mutated <- plot_data %>%
  mutate(
    class = recode(
      class,
      driver_pct = "Driver",
      non_driver_pct = "Non-driver"
    )
  )

plot_data_mutated

# lets change the counts dataframe of active learning so we can plot it together
active_data_gene_counts_boxplot <- counts %>%
  mutate(
    driver_pct = 100 * driver / gene,
    non_driver_pct = 100 * non.driver / gene
  ) %>%
  pivot_longer(
    cols = c(driver_pct, non_driver_pct),
    names_to = "class",
    values_to = "percentage"
  ) %>%
  mutate(
    class = recode(
      class,
      driver_pct = "Driver",
      non_driver_pct = "Non-driver"
    )
  )

library(ggh4x)

percentages_random_al <- ggplot(plot_data_mutated, aes(x = data_training, y = percentage)) +
  
  # Random selection: boxplots
  geom_boxplot(aes(fill = class),width = 0.6,outlier.shape = NA,alpha = 0.5) +
  # Random selection: individual observations
  geom_jitter(aes(color = class,shape = "Random Selection"),width = 0.12,size = 2,alpha = 0.5) +
  
  # Active learning: crosses
  geom_point(data = active_data_gene_counts_boxplot,
             aes(x = iteration,y = percentage,color = class,shape = "Active Learning"),size = 5,stroke = 1.2) +
  
  facet_wrap(~ class,
             ncol = 2,
             scales = "free_y",
             ) +
  
  # Different y-axis limits for each class
  facetted_pos_scales(
    y = list(scale_y_continuous(limits = c(0, 20),breaks = seq(0, 20, 5),labels = function(x) paste0(x, "%")),
             scale_y_continuous(limits = c(80, 100),breaks = seq(80, 100, 5),labels = function(x) paste0(x, "%")))) +
  
  geom_text(
    data = data.frame(
      class = c("Driver", "Non-driver"),
      label = c("a)", "b)")
    ),
    aes(x = -Inf, y = Inf, label = label),
    hjust = 1.5,
    vjust = -0.8,
    inherit.aes = FALSE,
    size = 9
  ) +
  coord_cartesian(clip = "off") +
  
  scale_shape_manual(name = "Sampling method",values = c("Random Selection" = 16,"Active Learning" = 4)) +
  
  # Colour-blind-friendly palette: teal + purple
  scale_fill_manual(name = "Label",values = c("Driver" = "#009E73","Non-driver" = "#CC79A7")) +
  
  scale_color_manual(name = "Label",values = c("Driver" = "#009E73","Non-driver" = "#CC79A7")) +
  
  labs(x = NULL,y = NULL) +
  
  theme_bw() +
  theme(
    panel.grid.major = element_blank(),
    panel.grid.minor = element_blank(),
    panel.border = element_blank(),
    axis.line = element_line(color = "black",linewidth = 0.8),
    
    text = element_text(size = 20),
    axis.text.x = element_text(size = 20,color = "black"),
    axis.text.y = element_text(size = 20,color = "black"),
    axis.title.y = element_text(size = 24,margin = margin(r = 15),face = "bold"),
    
    # Facet titles
    strip.text = element_text(size = 28,face = "bold",color = "black"),
    strip.background = element_blank(),
    legend.position = "bottom",
    legend.title = element_text(size = 24,face = "bold"),
    legend.text = element_text(size = 20),
    legend.key = element_blank()
  )

percentages_random_al
