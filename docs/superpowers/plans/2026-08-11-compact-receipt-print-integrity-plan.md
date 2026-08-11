# Compact receipt print integrity plan

1. Add RED renderer assertions for print page-break protection in checkpoint
   and outcome CSS, including stop/non-stop copy preservation.
2. Add the two declarations only to the existing print blocks.
3. Run focused GREEN tests, plugin/static/privacy/release gates, and root tests.
4. Review the diff and update provenance/version metadata.
5. Consume one cachebuster, install the new plugin, compare source/cache, and
   run installed smoke checks.
