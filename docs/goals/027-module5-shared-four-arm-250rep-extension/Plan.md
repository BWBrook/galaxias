# Goal 027 Plan

1. Freeze the source set, shared-seed identity, replicate-level interaction,
   weighting, tolerances, and 250-replicate stopping rule.
2. Implement the smallest separate four-arm execution and audit modules with
   focused synthetic tests.
3. Run local gates once, commit and push the execution source, and create a
   checksummed Git bundle from that exact SHA.
4. On `deep-server-ts`, run and inspect an all-source five-replicate smoke in
   `tmux`.
5. If and only if the smoke passes, run 250 replicates with 32 workers under a
   new run ID, then audit the remote raw result.
6. Pull back compact evidence only, conduct one scientific review, record the
   stability decision, and publish the bounded completion record.
