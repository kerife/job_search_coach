# Skip-link focus target implementation plan

1. Add failing renderer assertions for the three main landmarks.
2. Add `tabindex="-1"` to the three renderer templates only.
3. Run focused render tests, plugin/static/privacy checks, and the full root
   suite; inspect the diff for unchanged copy/order.
4. Obtain an independent review, refresh provenance, consume the cachebuster
   once, publish, install, and verify source/cache identity and installed
   validation.
