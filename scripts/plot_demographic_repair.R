args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: Rscript scripts/plot_demographic_repair.R INPUT_DIR OUTPUT_DIR")
input_dir <- args[[1]]
output_dir <- args[[2]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
neutral <- read.csv(file.path(input_dir, "neutral_reference_comparison.csv"))
founders <- read.csv(file.path(input_dir, "reference_founder_trajectories.csv"))

draw <- function() {
  oldpar <- par(no.readonly = TRUE)
  on.exit(par(oldpar))
  par(mfrow = c(1, 2), mar = c(4.2, 4.6, 3.2, 1.0), oma = c(3.5, 0, 1.5, 0),
      family = "sans", las = 1, mgp = c(2.8, 0.7, 0), tcl = -0.25)
  colors <- c(archived_common = "#646B73", archived_guard = "#BD5D25", repaired_founder = "#126D89")
  plot(NA, xlim = c(70, 110), ylim = c(0, 85), xlab = "Neutral annual step",
       ylab = "A-state abundance (fish)", main = "Neutral reference dynamics")
  abline(h = seq(0, 80, 20), col = "#E5E8EB", lwd = 0.8)
  for (key in names(colors)) {
    subset <- neutral[neutral$kernel == key & neutral$step >= 70 & neutral$step <= 110, ]
    lines(subset$step, subset$eligible_total, col = colors[[key]], lwd = 2)
  }
  legend(70, 72, legend = c("Archived common kernel", "Archived breeding guard", "Recruitment repair"),
         col = colors, lwd = 2, bty = "n", cex = 0.8)
  plot(NA, xlim = c(1991, 2012), ylim = c(0, 2000), xlab = "Year",
       ylab = "Modelled total fish", main = "Illustrative founder scenarios", xaxt = "n")
  axis(1, at = c(1991, 1997, 2002, 2008, 2012))
  abline(h = seq(0, 2000, 500), col = "#E5E8EB", lwd = 0.8)
  for (site in c("lake_oberon", "strathgordon")) {
    subset <- founders[founders$scenario_id == site, ]
    col <- if (site == "lake_oberon") "#126D89" else "#93713A"
    lines(subset$year, subset$N_total, col = col, lwd = 2)
    points(subset$year, subset$N_total, col = col, pch = 16, cex = 0.5)
  }
  legend("topleft", c("Oberon", "Strathgordon"), col = c("#126D89", "#93713A"),
         lwd = 2, bty = "n", cex = 0.85)
  mtext("Demographic repair qualification", outer = TRUE, side = 3, line = 0.2, font = 2, cex = 1.1)
  mtext("Illustrative parameter settings; no fitted population estimates or historical likelihoods.",
        outer = TRUE, side = 1, line = 1.0, cex = 0.8)
  mtext("Recruitment limits differ by site. The 2008 Strathgordon spawning switch is imposed.",
        outer = TRUE, side = 1, line = 2.1, cex = 0.8)
}
pdf(file.path(output_dir, "demographic_repair.pdf"), width = 10, height = 4.8, useDingbats = FALSE)
draw()
dev.off()
png(file.path(output_dir, "demographic_repair.png"), width = 1800, height = 864, res = 180)
draw()
dev.off()
