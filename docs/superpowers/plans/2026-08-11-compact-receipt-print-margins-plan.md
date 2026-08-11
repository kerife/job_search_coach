# Compact Receipt Print Margins Implementation Plan

1. Add RED assertions for the `@page` rule to both compact receipt renderer tests.
2. Add the rule to both CSS assets and synchronize the Superdesign theme dump.
3. Run focused receipt tests, static/theme checks, and diff validation.
4. Publish the increment only after the release gates pass.
