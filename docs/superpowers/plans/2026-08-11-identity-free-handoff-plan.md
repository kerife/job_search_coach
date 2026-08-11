# Identity-free dossier-to-practice projection plan

1. Add RED tests for bare person-name fact summaries in the shared helper,
   builder, custom/schema parity, and no-echo diagnostics.
2. Implement the smallest strict projection guard and a dedicated schema
   definition for source-fact summaries.
3. Run focused RED/GREEN checks, then the complete plugin and repository gates.
4. Review the diff and update provenance/cache metadata as required.
5. Consume one cachebuster, publish/install the plugin, compare source/cache,
   run installed smoke checks, and record the release evidence.
