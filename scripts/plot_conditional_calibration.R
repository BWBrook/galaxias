#!/usr/bin/env Rscript
# Validation-only target penalties and fixed-source observation sensitivity.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3L) stop('Usage: plot_conditional_calibration.R validation_analysis final_membership output_dir')
validation <- read.csv(file.path(args[1], 'verified_sources.csv'), check.names = FALSE)
validation$mc_qualified <- tolower(as.character(validation$mc_qualified)) == 'true'
members <- read.csv(args[2], check.names = FALSE)
out <- args[3]
dir.create(out, recursive = TRUE, showWarnings = FALSE)
ids <- c('search_seed', 'family_id', 'proposal_id')
profiles <- c('repair_presence_only', 'repair_detection_060', 'repair_detection_098',
              'repair_shared_window_060', 'repair_shared_window_098')
profile_labels <- c('Presence only', '0.60 independent', '0.98 independent', '0.60 shared', '0.98 shared')
families <- c('habitat_only_null', 'trout_only', 'climbing_only', 'persistent_joint_cause', 'transient_perfect_storm')
family_labels <- c('Habitat only', 'Trout only', 'Climbing only', 'Persistent joint', 'Transient joint')
global <- subset(members, cohort == 'global')
counts <- table(factor(global$family_id, levels = families), factor(global$profile, levels = profiles))
leverage <- read.csv(file.path(out, 'target_leverage_contexts.csv'), check.names = FALSE)
floors <- read.csv(file.path(out, 'structural_score_floors.csv'), check.names = FALSE)
lev <- subset(leverage, phase == 'validate' & profile == 'repair_presence_only' & cohort == 'family')
fields <- sprintf('CT%03d_weighted_penalty_mean', 1:5)
lev$early_mean <- rowSums(lev[fields])
observed <- tapply(lev$early_mean, lev$family_id, mean)[families]
minimum <- (floors$CT004_structural_floor + floors$CT005_structural_floor)[match(families, floors$family_id)]
if (any(observed < minimum - 1e-8)) stop('Observed penalties below the stated structural floors')
penalties <- rbind(minimum, pmax(0, observed - minimum))
# Keep two frozen reference cohorts fixed across observation profiles. The
# all-profile global union avoids privileging one profile's parameter selection;
# the presence-only reference shows sensitivity within that baseline cohort.
references <- list(
  global_union = unique(global[ids]),
  presence_only_global = unique(subset(global, profile == 'repair_presence_only', select = ids)))
rows <- list()
for (reference_name in names(references)) {
  reference <- references[[reference_name]]
  paired <- merge(reference, validation, by = ids)
  if (nrow(paired) != nrow(reference) * length(profiles)) stop('Incomplete fixed-source profile coverage')
  for (seed in sort(unique(paired$search_seed))) {
    for (profile in profiles) {
      x <- paired[paired$search_seed == seed & paired$profile == profile, ]
      estimates <- x$compatibility_weighted_surviving_2002
      errors <- x$compatibility_weighted_surviving_2002_mc_se
      valid <- is.finite(estimates)
      rows[[length(rows) + 1L]] <- data.frame(
        reference_cohort = reference_name, search_seed = seed, profile = profile, n_sources = nrow(x),
        n_conditioned_sources = sum(valid), n_weight_precision_qualified = sum(x$mc_qualified),
        unconditional_survival = mean(x$surviving_2002_mean),
        conditioned_survival = if (any(valid)) mean(estimates[valid]) else NA_real_,
        conditioned_survival_mc_se = if (any(valid)) sqrt(sum(errors[valid]^2)) / sum(valid) else NA_real_)
    }
  }
}
paired_summary <- do.call(rbind, rows)
write.csv(paired_summary, file.path(out, 'paired_observation_sensitivity.csv'), row.names = FALSE)
write.csv(data.frame(family_id = families, counts, check.names = FALSE), file.path(out, 'global_family_counts.csv'), row.names = FALSE)
render <- function() {
  par(mfrow = c(1, 2), mar = c(7.5, 4.3, 3.3, 0.7), oma = c(2.8, 0, 0, 0), mgp = c(2.7, 0.8, 0), las = 1, cex = 0.85)
  barplot(penalties, col = c('#929292', '#416fa1'), border = NA, names.arg = family_labels,
          las = 2, ylim = c(0, max(observed)*1.35), ylab = 'Mean early-target penalty',
          main = 'A  Structural penalties dominate simpler families')
  legend('topright', legend = c('Minimum imposed by family definition', 'Additional early-target discrepancy'),
         fill = c('#929292', '#416fa1'), border = NA, bty = 'n', cex = 0.73)
  plot(NA, xlim = c(0.6, 5.4), ylim = c(0, 1.28), xaxt = 'n', yaxt = 'n',
       xlab = '', ylab = 'Simulated survival to end-2002',
       main = 'B  Same parameter sources, different observations')
  axis(1, at = seq_along(profiles), labels = profile_labels, las = 2)
  axis(2, at = seq(0, 1, 0.2))
  abline(h = seq(0, 1, 0.25), col = '#e5e5e5', lty = 1)
  seeds <- sort(unique(paired_summary$search_seed))
  offsets <- seq(-0.10, 0.10, length.out = length(seeds))
  for (j in seq_along(seeds)) {
    z <- paired_summary[paired_summary$search_seed == seeds[j] & paired_summary$reference_cohort == 'global_union', ]
    z <- z[match(profiles, z$profile), ]
    xpos <- seq_along(profiles) + offsets[j]
    points(xpos, z$unconditional_survival, pch = 1, col = '#888888', cex = 0.85)
    low <- pmax(0, z$conditioned_survival - 1.96*z$conditioned_survival_mc_se)
    high <- pmin(1, z$conditioned_survival + 1.96*z$conditioned_survival_mc_se)
    segments(xpos, low, xpos, high, col = '#1e658f', lwd = 1.2)
    points(xpos, z$conditioned_survival, pch = 16, col = '#1e658f', cex = 0.85)
  }
  legend('topright', legend = c('Unconditional histories', 'Observation-weighted histories'),
         pch = c(1, 16), col = c('#888888', '#1e658f'), bty = 'n', cex = 0.78)
  mtext('Left: frozen family representatives under presence-only scoring. Right: the fixed union of global selections, evaluated under every observation profile.',
        outer = TRUE, side = 1, line = 0.25, cex = 0.70)
  mtext('Points represent search seeds; approximate Monte Carlo error bars omit unseen rare histories. Conservation removals are not explicit model forcing.',
        outer = TRUE, side = 1, line = 1.35, cex = 0.70)
}
pdf(file.path(out, 'conditional_calibration.pdf'), width = 11, height = 6.3, useDingbats = FALSE)
render()
dev.off()
png(file.path(out, 'conditional_calibration.png'), width = 1980, height = 1134, res = 180)
render()
dev.off()
