# small script to get the histogram (a nice one)
# with the distribution and maybe median and other things
# about the frequency of classification of regulators

library(ggplot2)
library(dplyr)
library(scales)

freq_reg <- read.csv("./frequency_clasification_regulators_allNormalisedgenes.csv")

# Compute central tendency and dispersion metrics
stats_summary_freq <- freq_reg %>%
  summarise(
    n_genes     = n(),
    mean        = mean(sentence_count, na.rm = TRUE),
    sd          = sd(sentence_count, na.rm = TRUE),
    median      = median(sentence_count, na.rm = TRUE),
    iqr         = IQR(sentence_count, na.rm = TRUE),
    q25         = quantile(sentence_count, 0.25, na.rm = TRUE),
    q75         = quantile(sentence_count, 0.75, na.rm = TRUE),
    min         = min(sentence_count, na.rm = TRUE),
    max         = max(sentence_count, na.rm = TRUE)
  )

print(stats_summary_freq)


# plot in a linear way
ggplot(freq_reg, aes(x = sentence_count)) +
  geom_histogram(
    aes(y = after_stat(density)),
    binwidth = 1,
    fill = "#2B5C8F",
    color = "white",
    linewidth = 0.2,
    alpha = 0.85
  ) +
  geom_density(
    color = "#D95F02",
    linewidth = 0.8,
    adjust = 1.5
  ) +
  geom_vline(
    xintercept = stats_summary_freq$median,
    color = "#1B9E77",
    linetype = "dashed",
    linewidth = 0.7
  ) +
  geom_vline(
    xintercept = stats_summary_freq$mean,
    color = "#E7298A",
    linetype = "dotted",
    linewidth = 0.7
  ) +
  annotate(
    "text",
    x = stats_summary_freq$median,
    y = Inf,
    label = paste0("Median = ", stats_summary_freq$median),
    vjust = 1.5,
    hjust = -0.1,
    color = "#1B9E77",
    fontface = "bold",
    size = 3.5
  ) +
  annotate(
    "text",
    x = stats_summary_freq$mean,
    y = Inf,
    label = paste0("Mean = ", round(stats_summary_freq$mean, 2)),
    vjust = 3.2,
    hjust = -0.1,
    color = "#E7298A",
    fontface = "bold",
    size = 3.5
  ) +
  scale_x_continuous(expand = expansion(mult = c(0.01, 0.05))) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  labs(
    x = "Regulator Classification Count",
    y = "Density"
  ) +
  theme_classic(base_size = 11, base_family = "sans") +
  theme(
    axis.title = element_text(face = "bold"),
    axis.text = element_text(color = "black"),
    axis.line = element_line(linewidth = 0.4),
    axis.ticks = element_line(linewidth = 0.4)
  )



# plot in a log way

freq_reg_log <- freq_reg %>%
  mutate(log10_sentence_count = log10(sentence_count))

stats_log <- data.frame(
  log_median  = median(log10(freq_reg$sentence_count), na.rm = TRUE),
  log_mean    = mean(log10(freq_reg$sentence_count), na.rm = TRUE)
)

# Plotting the transformed variable directly


# variant 1 of plot
ggplot(freq_reg_log, aes(x = log10_sentence_count)) +
  geom_histogram(
    fill = "#2B5C8F",
    color = "white",
    linewidth = 0.2,
    bins = 30
  ) +
  geom_vline(
    xintercept = stats_log$log_median,
    color = "#1B9E77",
    linetype = "dashed",
    linewidth = 0.7
  ) +
  geom_vline(
    xintercept = stats_log$log_mean,
    color = "#E7298A",
    linetype = "dotted",
    linewidth = 0.7
  ) +
  annotate(
    "text",
    x = stats_log$log_median,
    y = Inf,
    label = paste0("Median = ", stats_log$log_median),
    vjust = 1.5,
    hjust = -0.1,
    color = "#1B9E77",
    fontface = "bold",
    size = 3.5
  ) +
  annotate(
    "text",
    x = stats_log$log_mean,
    y = Inf,
    label = paste0("Mean = ", round(stats_log$log_mean, 2)),
    vjust = 3.2,
    hjust = -0.1,
    color = "#E7298A",
    fontface = "bold",
    size = 3.5
  ) +
  
  labs(
    x = expression(log[10]("Sentence Count")),
    y = "Gene Count"
  ) +
  theme_classic(base_size = 11) +
  theme(
    axis.title = element_text(face = "bold"),
    axis.text = element_text(color = "black")
  )


# variant 2 of plot

ggplot(freq_reg_log, aes(x = log10_sentence_count)) +
  # histogram
  geom_histogram(
    bins = 30,
    fill = "#2B5C8F",
    color = "white",
    linewidth = 0.2,
    alpha = 0.9
  ) +
  # median and mean lines
  geom_vline(
    xintercept = log10(stats_summary_freq$median),
    color = "#1B9E77",
    linetype = "dashed",
    linewidth = 0.6
  ) +
  geom_vline(
    xintercept = log10(stats_summary_freq$mean),
    color = "#E7298A",
    linetype = "dotted",
    linewidth = 0.6
  ) +
  # annotations of the lines
  annotate(
    "text",
    x = stats_log$log_median,
    y = Inf,
    label = paste0("Median (raw scale) = ", round(log10(stats_summary_freq$median), 2)),
    vjust = 1.6,
    hjust = -0.05,
    color = "#1B9E77",
    fontface = "bold",
    size = 3.2
  ) +
  annotate(
    "text",
    x = stats_log$log_mean,
    y = Inf,
    label = paste0("Mean (raw scale) = ", round(log10(stats_summary_freq$mean), 2)),
    vjust = 3.2,
    hjust = -0.05,
    color = "#E7298A",
    fontface = "bold",
    size = 3.2
  ) +
  # labels and axis and things like that
  labs(
    x = expression(bold(log[10] * "(Count Gene Mentions Classified as Regulators)")),
    y = "Number of Unique Genes"
  ) +
  scale_y_continuous(
    labels = label_comma(),
    expand = expansion(mult = c(0, 0.08))
  ) +
  scale_x_continuous(
    expand = expansion(mult = c(0.02, 0.05))
  ) +
  # 6. Journal theme styling
  theme_classic(base_size = 11, base_family = "sans") +
  theme(
    axis.title        = element_text(face = "bold", size = 11),
    axis.title.x      = element_text(margin = margin(t = 8)),
    axis.title.y      = element_text(margin = margin(r = 8)),
    axis.text         = element_text(color = "black", size = 9.5),
    axis.line         = element_line(color = "black", linewidth = 0.4),
    axis.ticks        = element_line(color = "black", linewidth = 0.4),
    plot.margin       = margin(t = 10, r = 15, b = 10, l = 10)
  )

# variant 3 of the plot (same as 2, just different aesthetic parts)
ggplot(freq_reg_log, aes(x = log10_sentence_count)) +
  # 1. Histogram (Okabe-Ito Blue)
  geom_histogram(
    bins = 30,
    fill = "#56B4A9",
    color = "white",
    linewidth = 0.3,
    alpha = 0.5
  ) +
  # 2. Thicker median and mean lines (Okabe-Ito Green & Vermillion)
  geom_vline(
    xintercept = log10(stats_summary_freq$median),
    color = "#009E73",
    linetype = "solid",
    linewidth = 1
  ) +
  geom_vline(
    xintercept = log10(stats_summary_freq$mean),
    color = "#E69F00",
    linetype = "dashed",
    linewidth = 1
  ) +
  # 3. Larger text annotations
  annotate(
    "text",
    x = log10(stats_summary_freq$median),
    y = Inf,
    label = paste0("Median (raw scale) = ", round(stats_summary_freq$median, 2)),
    vjust = 1.6,
    hjust = -0.05,
    color = "#009E73",
    #fontface = "bold",
    size = 6
  ) +
  annotate(
    "text",
    x = log10(stats_summary_freq$mean),
    y = Inf,
    label = paste0("Mean (raw scale) = ", round(stats_summary_freq$mean, 2)),
    vjust = 3.4,
    hjust = -0.05,
    color = "#E69F00",
    #fontface = "bold",
    size = 6
  ) +
  # 4. Clearer axis titles and formatting
  labs(
    x = expression(bold("Log"[10] * " Count (Gene Mentions Classified as Driver)")),
    y = "Number of Unique Genes"
  ) +
  scale_y_continuous(
    labels = label_comma(),
    expand = expansion(mult = c(0, 0.08))
  ) +
  scale_x_continuous(
    breaks = seq(0, 3, by = 0.5),
    expand = expansion(mult = c(0.02, 0.05))
  ) +
  # 5. Journal theme styling with larger fonts
  theme_classic(base_size = 14, base_family = "sans") +
  theme(
    axis.title        = element_text(face = "bold", size = 20),
    axis.text         = element_text(color = "black", size = 14),
    axis.line         = element_line(color = "black", linewidth = 0.6),
    axis.ticks        = element_line(color = "black", linewidth = 1),
    plot.margin       = margin(t = 12, r = 18, b = 12, l = 12)
  )
