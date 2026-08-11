# Compact receipt forced-colors boundary plan

1. Add RED renderer assertions for boundary width and `CanvasText` in both
   compact forced-colors blocks.
2. Add only the explicit left-border width declarations.
3. Run focused GREEN tests and full plugin/static/privacy/release gates.
4. Consume one cachebuster, install the release, compare source/cache, and run
   installed smoke checks.
